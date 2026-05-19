import os
import json
from app.rag.topic_mapper import find_best_canonical_match

CURRICULUM_JSON_PATH = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "generated_curriculum.json"
))

class CurriculumIndex:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CurriculumIndex, cls).__new__(cls)
            cls._instance.load_index()
        return cls._instance

    def load_index(self):
        self.graph = []
        self.topic_map = {}  # Exact lookup map: LowercaseTopicName -> Node
        self.all_topics = []

        if not os.path.exists(CURRICULUM_JSON_PATH):
            # Write a clean blank list so files don't crash
            os.makedirs(os.path.dirname(CURRICULUM_JSON_PATH), exist_ok=True)
            with open(CURRICULUM_JSON_PATH, "w") as f:
                json.dump([], f)
            return

        try:
            with open(CURRICULUM_JSON_PATH, "r", encoding="utf-8") as f:
                self.graph = json.load(f)
                
            # Flatten graph into searchable topic mapping
            for book in self.graph:
                class_name = book.get("class", "Class 9")
                subject = book.get("subject", "Science")
                book_title = book.get("book", "Textbook")
                pdf_file = book.get("pdf", "")
                
                for chapter in book.get("chapters", []):
                    chap_num = chapter.get("chapter_number", 1)
                    chap_name = chapter.get("chapter_name", "")
                    
                    for topic in chapter.get("topics", []):
                        node = {
                            "class": class_name,
                            "subject": subject,
                            "book": book_title,
                            "pdf": pdf_file,
                            "chapter_number": chap_num,
                            "chapter": chap_name,
                            "topic": topic
                        }
                        self.topic_map[topic.lower()] = node
                        if topic not in self.all_topics:
                            self.all_topics.append(topic)
        except Exception as e:
            print(f"[ERROR] Failed to load curriculum graph index: {e}")

    def lookup_topic(self, query_topic: str) -> dict | None:
        """Looks up a topic name in the index using exact and fuzzy mappings."""
        if not self.topic_map:
            self.load_index()
            
        # 1. Exact Match
        query_lower = query_topic.strip().lower()
        if query_lower in self.topic_map:
            return self.topic_map[query_lower]

        # 2. Fuzzy Match
        best_match = find_best_canonical_match(query_topic, self.all_topics)
        if best_match:
            return self.topic_map[best_match.lower()]
            
        return None

    def get_related_topics(self, chapter_name: str, current_topic: str = "", limit: int = 4) -> list[str]:
        """Returns other topics inside the same chapter context."""
        related = []
        for book in self.graph:
            for chapter in book.get("chapters", []):
                if chapter.get("chapter_name", "").lower() == chapter_name.lower():
                    for t in chapter.get("topics", []):
                        if t != current_topic:
                            related.append(t)
                            if len(related) >= limit:
                                return related
        return related
