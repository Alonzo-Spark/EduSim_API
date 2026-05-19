import re
import hashlib
from dataclasses import dataclass

@dataclass
class TextChunk:
    text: str
    metadata: dict
    chunk_id: str

class SemanticEducationalChunker:
    def __init__(self, chunk_size: int = 800, overlap: int = 100):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def clean_and_normalize(self, text: str) -> str:
        """
        Normalize and clean textbook text:
        - Normalize smart quotes/dashes
        - Remove duplicate empty lines
        - Clean page numbers/headers
        """
        if not text:
            return ""
        # Normalize quotes and dashes
        text = text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
        text = text.replace("–", "-").replace("—", "-")
        
        # Clean excessive newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Remove lines that look like page headers or footers
        # e.g., "12 SCIENCE" or "Page 25 of 150" or single digit numbers
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            stripped = line.strip()
            # If line is just a page number or very short header, skip it
            if re.match(r'^\d+$', stripped):
                continue
            if re.match(r'^(class\s+\d+|science|physics|chemistry|biology|chapter\s+\d+)\s*$', stripped, re.IGNORECASE):
                continue
            cleaned_lines.append(line)
            
        return '\n'.join(cleaned_lines).strip()

    def identify_special_lines(self, line: str) -> str:
        """Classify a line as a regular line or part of a list, formula, example, etc."""
        stripped = line.strip()
        if not stripped:
            return "empty"
        
        # Heading: short capitalized line or section numbers
        if re.match(r'^\d+(\.\d+){1,3}\s+[A-Z]', stripped):
            return "heading"
        if len(stripped) < 60 and (stripped.isupper() or stripped.startswith("Chapter ") or stripped.startswith("CHAPTER ")):
            return "heading"
            
        # Example: starts with example / question indicator
        if re.match(r'^(Example|Q\d+|Question|Sol\.|Solution|Ans\.|Answer)[:\s\.]', stripped, re.IGNORECASE):
            return "example"
            
        # List or step: starts with bullet or number
        if re.match(r'^(\d+[\.\)]|\*|\-|•|[a-z][\.\)])\s+', stripped):
            return "step"
            
        # Formula: contains equal signs and math expressions
        if re.search(r'([a-zA-Z0-9\s_]{1,10}\s*=\s*[a-zA-Z0-9\s_*/\+\-\(\)\^]{2,})', stripped):
            # Verify if it also contains some common scientific operators or terms
            if any(sym in stripped for sym in ["+", "-", "*", "/", "=", "^", "²", "³", "Δ", "λ", "θ", "π"]):
                return "formula"
            
        return "text"

    def parse_semantic_blocks(self, text: str) -> list[dict]:
        """Group text lines into logical semantic blocks (heading, example, formula, list, paragraph)"""
        text = self.clean_and_normalize(text)
        lines = text.split('\n')
        
        blocks = []
        current_block = []
        current_type = "empty"
        
        for line in lines:
            line_type = self.identify_special_lines(line)
            
            if line_type == "empty":
                if current_block:
                    blocks.append({"type": current_type, "text": "\n".join(current_block)})
                    current_block = []
                    current_type = "empty"
                continue
            
            # If type matches, group them (especially for lists and formulas which can span multiple lines)
            if line_type == current_type and current_type in ["step", "formula"]:
                current_block.append(line)
            else:
                if current_block:
                    blocks.append({"type": current_type, "text": "\n".join(current_block)})
                current_block = [line]
                current_type = line_type
                
        if current_block:
            blocks.append({"type": current_type, "text": "\n".join(current_block)})
            
        return [b for b in blocks if b["text"].strip()]

    def chunk_document(self, text: str, metadata: dict) -> list[TextChunk]:
        """
        Produce smart, educational semantic chunks respecting boundaries
        """
        blocks = self.parse_semantic_blocks(text)
        
        chunks = []
        current_chunk_text = ""
        chunk_index = 0
        
        for block in blocks:
            b_text = block["text"]
            b_type = block["type"]
            
            # Add semantic prefix/clue if it is an Example or Formula
            if b_type == "example" and not b_text.lower().startswith("example"):
                b_text = f"[Example] {b_text}"
            elif b_type == "formula" and not any(kw in b_text.lower() for kw in ["formula", "equation"]):
                b_text = f"[Equation/Formula] {b_text}"
                
            # If current chunk has space, add block
            if len(current_chunk_text) + len(b_text) + 2 <= self.chunk_size:
                current_chunk_text += ("\n\n" if current_chunk_text else "") + b_text
            else:
                # If current chunk has content, emit it
                if current_chunk_text:
                    # Extract keywords for metadata
                    keywords = self.extract_keywords_from_chunk(current_chunk_text)
                    chunk_meta = {
                        **metadata,
                        "chunk_index": chunk_index,
                        "scanned": False,
                        "semantic_keywords": keywords
                    }
                    
                    # Generate deterministic ID
                    text_hash = hashlib.md5(current_chunk_text.encode('utf-8')).hexdigest()[:12]
                    chunk_id = f"{metadata.get('class', 'class')}_{metadata.get('subject', 'subj')}_{metadata.get('chapter', 'ch')}_p{metadata.get('page', 0)}_idx{chunk_index}_{text_hash}".lower().replace(" ", "_")
                    
                    chunks.append(TextChunk(
                        text=current_chunk_text,
                        metadata=chunk_meta,
                        chunk_id=chunk_id
                    ))
                    chunk_index += 1
                    
                    # Apply overlap: grab approx last `overlap` chars, trying to align on sentences
                    overlap_text = current_chunk_text[-self.overlap:]
                    # Try to align overlap to nearest space or sentence
                    space_idx = overlap_text.find(" ")
                    if space_idx != -1:
                        overlap_text = overlap_text[space_idx:].strip()
                        
                    current_chunk_text = overlap_text + "\n\n" + b_text
                else:
                    # Single block exceeds chunk size, split by sentences
                    sentences = re.split(r'(?<=[.!?])\s+', b_text)
                    for sent in sentences:
                        if len(current_chunk_text) + len(sent) + 1 <= self.chunk_size:
                            current_chunk_text += (" " if current_chunk_text else "") + sent
                        else:
                            if current_chunk_text:
                                keywords = self.extract_keywords_from_chunk(current_chunk_text)
                                chunk_meta = {
                                    **metadata,
                                    "chunk_index": chunk_index,
                                    "scanned": False,
                                    "semantic_keywords": keywords
                                }
                                text_hash = hashlib.md5(current_chunk_text.encode('utf-8')).hexdigest()[:12]
                                chunk_id = f"{metadata.get('class', 'class')}_{metadata.get('subject', 'subj')}_{metadata.get('chapter', 'ch')}_p{metadata.get('page', 0)}_idx{chunk_index}_{text_hash}".lower().replace(" ", "_")
                                
                                chunks.append(TextChunk(
                                    text=current_chunk_text,
                                    metadata=chunk_meta,
                                    chunk_id=chunk_id
                                ))
                                chunk_index += 1
                                current_chunk_text = current_chunk_text[-self.overlap:] + " " + sent
                            else:
                                current_chunk_text = sent
                                
        if current_chunk_text.strip():
            keywords = self.extract_keywords_from_chunk(current_chunk_text)
            chunk_meta = {
                **metadata,
                "chunk_index": chunk_index,
                "scanned": False,
                "semantic_keywords": keywords
            }
            text_hash = hashlib.md5(current_chunk_text.encode('utf-8')).hexdigest()[:12]
            chunk_id = f"{metadata.get('class', 'class')}_{metadata.get('subject', 'subj')}_{metadata.get('chapter', 'ch')}_p{metadata.get('page', 0)}_idx{chunk_index}_{text_hash}".lower().replace(" ", "_")
            
            chunks.append(TextChunk(
                text=current_chunk_text,
                metadata=chunk_meta,
                chunk_id=chunk_id
            ))
            
        return chunks

    def extract_keywords_from_chunk(self, text: str) -> str:
        """Extract top 10 relevant keywords/nouns from educational text."""
        # Simple stop words list
        stopwords = {
            "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "aren't",
            "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by",
            "can", "can't", "cannot", "could", "couldn't", "did", "didn't", "do", "does", "doesn't", "doing",
            "don't", "down", "during", "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't",
            "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here", "here's", "hers", "herself",
            "him", "himself", "his", "how", "how's", "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is",
            "isn't", "it", "it's", "its", "itself", "let's", "me", "more", "most", "mustn't", "my", "myself", "no",
            "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our", "ours", "ourselves",
            "out", "over", "own", "same", "shan't", "she", "she'd", "she'll", "she's", "should", "shouldn't", "so",
            "some", "such", "than", "that", "that's", "the", "their", "theirs", "them", "themselves", "then", "there",
            "there's", "these", "they", "they'd", "they'll", "they're", "they've", "this", "those", "through", "to",
            "too", "under", "until", "up", "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were",
            "weren't", "what", "what's", "when", "when's", "where", "where's", "which", "while", "who", "who's", "whom",
            "why", "why's", "with", "won't", "would", "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your",
            "yours", "yourself", "yourselves"
        }
        
        # Find capitalised nouns or scientific terms (letters only, length > 3)
        cleaned = re.sub(r'[^a-zA-Z\s]', ' ', text)
        words = cleaned.split()
        
        keywords = []
        seen = set()
        
        for word in words:
            w_lower = word.lower()
            if len(w_lower) > 3 and w_lower not in stopwords and w_lower not in seen:
                seen.add(w_lower)
                # Boost capitalized words (proper nouns or key terms)
                if word[0].isupper():
                    keywords.insert(0, word)
                else:
                    keywords.append(word)
                    
        return ", ".join(keywords[:10])

# Maintain backward compatibility with the old simple chunking function
def chunk_by_paragraphs(
    text: str,
    metadata: dict,
    chunk_size: int = 800,
    overlap: int = 100
) -> list:
    """Helper to maintain backward compatibility with old app.rag.chunker imports."""
    chunker = SemanticEducationalChunker(chunk_size, overlap)
    return chunker.chunk_document(text, metadata)
