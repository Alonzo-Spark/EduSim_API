import pgvector from "pgvector/pg";
import { query } from "../db/db.js";
import { getNumberEnv } from "../utils/env.js";
import { embedText } from "./embedding.js";
const RETRIEVAL_CACHE_TTL_MS = getNumberEnv("RETRIEVAL_CACHE_TTL_MS", 60_000);
const RETRIEVAL_CACHE_MAX_ITEMS = getNumberEnv("RETRIEVAL_CACHE_MAX_ITEMS", 500);
const DEFAULT_SEMANTIC_WEIGHT = getNumberEnv("RETRIEVAL_SEMANTIC_WEIGHT", 0.75);
const DEFAULT_KEYWORD_WEIGHT = getNumberEnv("RETRIEVAL_KEYWORD_WEIGHT", 0.25);
const retrievalCache = new Map();
function normalizeNumber(value) {
    const parsedValue = typeof value === "number" ? value : Number(value);
    return Number.isFinite(parsedValue) ? parsedValue : 0;
}
function stableCacheKey(question, options) {
    return JSON.stringify({
        question: question.trim().toLowerCase(),
        topK: options.topK ?? 5,
        minimumSimilarity: options.minimumSimilarity ?? 0,
        minimumScore: options.minimumScore ?? 0,
        semanticWeight: options.semanticWeight ?? DEFAULT_SEMANTIC_WEIGHT,
        keywordWeight: options.keywordWeight ?? DEFAULT_KEYWORD_WEIGHT,
        classId: options.classId ?? null,
        subjectId: options.subjectId ?? null,
        chapterId: options.chapterId ?? null,
        topicId: options.topicId ?? null,
        className: options.className ?? null,
        subject: options.subject ?? null,
        chapter: options.chapter ?? null,
    });
}
function getCachedResult(cacheKey) {
    const hit = retrievalCache.get(cacheKey);
    if (!hit) {
        return null;
    }
    if (hit.expiresAtMs < Date.now()) {
        retrievalCache.delete(cacheKey);
        return null;
    }
    return hit.value;
}
function setCachedResult(cacheKey, value) {
    retrievalCache.set(cacheKey, {
        value,
        expiresAtMs: Date.now() + RETRIEVAL_CACHE_TTL_MS,
    });
    if (retrievalCache.size > RETRIEVAL_CACHE_MAX_ITEMS) {
        const oldest = [...retrievalCache.entries()].sort((a, b) => a[1].expiresAtMs - b[1].expiresAtMs);
        const toDelete = retrievalCache.size - RETRIEVAL_CACHE_MAX_ITEMS;
        for (const [key] of oldest.slice(0, toDelete)) {
            retrievalCache.delete(key);
        }
    }
}
export async function retrieveRelevantChunks(question, options = {}) {
    const topK = Math.max(1, Math.min(options.topK ?? 6, 25));
    const minimumSimilarity = options.minimumSimilarity ?? 0;
    const minimumScore = options.minimumScore ?? 0;
    const semanticWeight = Math.max(0, options.semanticWeight ?? DEFAULT_SEMANTIC_WEIGHT);
    const keywordWeight = Math.max(0, options.keywordWeight ?? DEFAULT_KEYWORD_WEIGHT);
    const weightSum = semanticWeight + keywordWeight || 1;
    const normalizedSemanticWeight = semanticWeight / weightSum;
    const normalizedKeywordWeight = keywordWeight / weightSum;
    const cacheKey = stableCacheKey(question, options);
    if (!options.disableCache) {
        const cached = getCachedResult(cacheKey);
        if (cached) {
            return cached;
        }
    }
    const questionEmbedding = await embedText(question);
    const result = await query(`
      WITH ranked_chunks AS (
        SELECT
          id,
          class_id,
          subject_id,
          chapter_id,
          topic_id,
          class_name,
          subject,
          chapter,
          topic,
          content,
          source_file,
          page,
          GREATEST(1 - (embedding <=> $1), 0) AS semantic_score,
          ts_rank_cd(
            to_tsvector(
              'english',
              coalesce(class_name, '') || ' ' ||
              coalesce(subject, '') || ' ' ||
              coalesce(chapter, '') || ' ' ||
              coalesce(topic, '') || ' ' ||
              coalesce(content, '')
            ),
            plainto_tsquery('english', $2)
          ) AS keyword_score
        FROM textbook_chunks
        WHERE ($3::bigint IS NULL OR class_id = $3)
          AND ($4::bigint IS NULL OR subject_id = $4)
          AND ($5::bigint IS NULL OR chapter_id = $5)
          AND ($6::bigint IS NULL OR topic_id = $6)
          AND ($7::text IS NULL OR class_name = $7)
          AND ($8::text IS NULL OR subject = $8)
          AND ($9::text IS NULL OR chapter = $9)
      )
      SELECT
        *,
        (semantic_score * $10) + (keyword_score * $11) AS score
      FROM ranked_chunks
      ORDER BY score DESC, semantic_score DESC, keyword_score DESC
      LIMIT $12
    `, [
        pgvector.toSql(questionEmbedding),
        question,
        options.classId ?? null,
        options.subjectId ?? null,
        options.chapterId ?? null,
        options.topicId ?? null,
        options.className ?? null,
        options.subject ?? null,
        options.chapter ?? null,
        normalizedSemanticWeight,
        normalizedKeywordWeight,
        topK,
    ]);
    const rows = result.rows
        .map((row) => ({
        id: normalizeNumber(row.id),
        classId: row.class_id,
        subjectId: row.subject_id,
        chapterId: row.chapter_id,
        topicId: row.topic_id,
        className: row.class_name,
        subject: row.subject,
        chapter: row.chapter,
        topic: row.topic,
        content: row.content,
        sourceFile: row.source_file,
        page: normalizeNumber(row.page),
        semanticScore: normalizeNumber(row.semantic_score),
        keywordScore: normalizeNumber(row.keyword_score),
        score: normalizeNumber(row.score),
    }))
        .filter((chunk) => chunk.semanticScore >= minimumSimilarity && chunk.score >= minimumScore);
    if (!options.disableCache) {
        setCachedResult(cacheKey, rows);
    }
    return rows;
}
//# sourceMappingURL=retriever.js.map