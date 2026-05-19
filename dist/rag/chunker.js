import { createHash } from "node:crypto";
import path from "node:path";
const MIN_CHUNK_LENGTH = 500;
const TARGET_CHUNK_LENGTH = 700;
const MAX_CHUNK_LENGTH = 800;
const OVERLAP_LENGTH = 100;
function normalizeWhitespace(text) {
    return text
        .replace(/\r\n/g, "\n")
        .replaceAll("\u0000", "")
        .replace(/[ \t]+\n/g, "\n")
        .replace(/\n{3,}/g, "\n\n")
        .trim();
}
function cleanHeading(text) {
    return text
        .replace(/\s+/g, " ")
        .replace(/^[-–—•*\d.\s]+/, "")
        .trim();
}
function cleanFileName(fileName) {
    return fileName
        .replace(/[_-]+/g, " ")
        .replace(/\s+/g, " ")
        .replace(/\.pdf$/i, "")
        .trim();
}
function extractClassFromText(value) {
    if (!value) {
        return null;
    }
    const classMatch = value.match(/\b(?:class|grade|std|standard)\s*[-_ ]?(\d{1,2})\b/i);
    if (classMatch?.[1]) {
        return `Class ${classMatch[1]}`;
    }
    const bareMatch = value.match(/\b(\d{1,2})(?:th)?\b/);
    if (bareMatch?.[1] && Number(bareMatch[1]) >= 1 && Number(bareMatch[1]) <= 12) {
        return `Class ${bareMatch[1]}`;
    }
    return null;
}
function isChapterHeading(text) {
    return /^(chapter|unit|lesson|module)\b/i.test(text) || /^chapter\s+\d+/i.test(text);
}
function inferHeadingContext(text) {
    const cleaned = cleanHeading(text);
    if (!cleaned) {
        return null;
    }
    if (isChapterHeading(cleaned)) {
        return { chapter: cleaned };
    }
    const looksLikeTopic = cleaned.length <= 120 &&
        !/[.!?]$/.test(cleaned) &&
        (cleaned === cleaned.toUpperCase() ||
            /^\d+(\.\d+)*\s+[A-Z]/.test(cleaned) ||
            /^[A-Z][A-Za-z0-9 ,:'"()/-]+$/.test(cleaned));
    if (looksLikeTopic) {
        return { topic: cleaned };
    }
    return null;
}
function splitIntoParagraphs(pageText) {
    return normalizeWhitespace(pageText)
        .split(/\n\s*\n+/)
        .map((paragraph) => paragraph.trim())
        .filter(Boolean);
}
function splitLongParagraph(paragraph) {
    if (paragraph.length <= MAX_CHUNK_LENGTH) {
        return [paragraph];
    }
    const sentences = paragraph.match(/[^.!?]+[.!?]+|[^.!?]+$/g) ?? [paragraph];
    const pieces = [];
    let current = "";
    for (const sentence of sentences) {
        const trimmedSentence = sentence.trim();
        if (!trimmedSentence) {
            continue;
        }
        const trial = current ? `${current} ${trimmedSentence}` : trimmedSentence;
        if (trial.length > TARGET_CHUNK_LENGTH && current) {
            pieces.push(current.trim());
            current = trimmedSentence;
            continue;
        }
        current = trial;
    }
    if (current.trim()) {
        pieces.push(current.trim());
    }
    return pieces;
}
function fingerprintChunk(metadata, sourceFile, page, content) {
    return createHash("sha256")
        .update(JSON.stringify({
        ...metadata,
        sourceFile,
        page,
        content: content.replace(/\s+/g, " ").trim(),
    }))
        .digest("hex");
}
export function deriveMetadataFromPath(relativePath) {
    const normalizedPath = relativePath.split(path.sep).join("/");
    const segments = normalizedPath.split("/").filter(Boolean);
    const fileName = segments.at(-1) ?? "";
    const cleanName = cleanFileName(fileName);
    const fileTokens = cleanName.split(/\s+/).filter(Boolean);
    const classFromSegments = segments.map((segment) => extractClassFromText(segment)).find(Boolean) ?? null;
    const classFromFilename = extractClassFromText(cleanName);
    const inferredSubject = (segments[1] ? cleanHeading(segments[1]) : null) ??
        fileTokens.find((token) => /^[A-Za-z]{4,}$/.test(token)) ??
        null;
    const chapterMatch = cleanName.match(/\b(?:chapter|ch|unit|lesson)\s*[-_ ]?(\d+)?[:.\- ]*([A-Za-z0-9 ,:'"()/-]{2,})?/i);
    const inferredChapterLabel = chapterMatch?.[0] && chapterMatch[0].trim().length > 2 ? cleanHeading(chapterMatch[0]) : null;
    const inferredTopicFromFilename = cleanName
        .replace(/\b(?:class|grade|std|standard)\s*[-_ ]?\d{1,2}\b/gi, "")
        .replace(/\b(?:chapter|ch|unit|lesson)\s*[-_ ]?\d+\b/gi, "")
        .replace(/\s+/g, " ")
        .trim();
    return {
        className: classFromSegments ?? classFromFilename ?? (segments[0] ? cleanHeading(segments[0]) : null),
        subject: inferredSubject,
        chapter: segments[2] ? cleanHeading(segments[2]) : (inferredChapterLabel ?? cleanName),
        topic: inferredTopicFromFilename || cleanName || null,
    };
}
export function chunkTextbookDocument(input) {
    const pages = input.rawText.split(/\f+/);
    const chunks = [];
    const context = { ...input.metadata };
    let buffer = "";
    let bufferStartPage = 1;
    const flushBuffer = (page) => {
        const content = buffer.trim();
        if (!content) {
            buffer = "";
            bufferStartPage = page;
            return;
        }
        const chunkMetadata = {
            className: context.className,
            subject: context.subject,
            chapter: context.chapter,
            topic: context.topic,
        };
        chunks.push({
            ...chunkMetadata,
            content,
            sourceFile: input.sourceFile,
            page: bufferStartPage,
            fingerprint: fingerprintChunk(chunkMetadata, input.sourceFile, bufferStartPage, content),
        });
        const overlap = content.slice(Math.max(0, content.length - OVERLAP_LENGTH)).trim();
        buffer = overlap;
        bufferStartPage = page;
    };
    pages.forEach((pageText, pageIndex) => {
        const pageNumber = pageIndex + 1;
        const paragraphs = splitIntoParagraphs(pageText);
        for (const paragraph of paragraphs) {
            const headingContext = inferHeadingContext(paragraph);
            if (headingContext?.chapter) {
                context.chapter = headingContext.chapter;
                continue;
            }
            if (headingContext?.topic) {
                context.topic = headingContext.topic;
                continue;
            }
            for (const paragraphPiece of splitLongParagraph(paragraph)) {
                const piece = paragraphPiece.trim();
                if (!piece) {
                    continue;
                }
                if (!buffer) {
                    bufferStartPage = pageNumber;
                }
                const trial = buffer ? `${buffer}\n\n${piece}` : piece;
                if (trial.length > MAX_CHUNK_LENGTH && buffer.length >= MIN_CHUNK_LENGTH) {
                    flushBuffer(pageNumber);
                    buffer = piece;
                    bufferStartPage = pageNumber;
                    continue;
                }
                buffer = trial;
                if (buffer.length >= TARGET_CHUNK_LENGTH) {
                    flushBuffer(pageNumber);
                }
            }
        }
    });
    if (buffer.trim()) {
        flushBuffer(pages.length || 1);
    }
    return chunks;
}
//# sourceMappingURL=chunker.js.map