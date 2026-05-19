import { pipeline } from "@xenova/transformers";
import { EMBEDDING_DIMENSION } from "../db/schema.js";
import { getNumberEnv } from "../utils/env.js";
import { logger } from "../utils/logger.js";
const EMBEDDING_MODEL = "Xenova/all-MiniLM-L6-v2";
const CACHE_TTL_MS = getNumberEnv("EMBEDDING_CACHE_TTL_MS", 15 * 60 * 1000);
const CACHE_MAX_ITEMS = getNumberEnv("EMBEDDING_CACHE_MAX_ITEMS", 5_000);
const EMBEDDING_BATCH_SIZE = Math.max(1, getNumberEnv("EMBEDDING_BATCH_SIZE", 12));
let extractorPromise = null;
const embeddingCache = new Map();
async function getExtractor() {
    if (!extractorPromise) {
        logger.info(`Loading embedding model ${EMBEDDING_MODEL}`);
        extractorPromise = pipeline("feature-extraction", EMBEDDING_MODEL, {
            quantized: true,
        });
    }
    return extractorPromise;
}
function toVector(output) {
    const rawData = typeof output === "object" && output !== null && "data" in output && output.data
        ? output.data
        : output;
    const vector = Array.from(rawData, (value) => Number(value));
    if (vector.length !== EMBEDDING_DIMENSION) {
        throw new Error(`Expected embedding dimension ${EMBEDDING_DIMENSION}, received ${vector.length}`);
    }
    return vector;
}
function normalizeText(text) {
    return text.trim().replace(/\s+/g, " ");
}
function evictIfNeeded() {
    if (embeddingCache.size <= CACHE_MAX_ITEMS) {
        return;
    }
    const entries = [...embeddingCache.entries()].sort((a, b) => a[1].expiresAtMs - b[1].expiresAtMs);
    for (const [key] of entries.slice(0, embeddingCache.size - CACHE_MAX_ITEMS)) {
        embeddingCache.delete(key);
    }
}
function getCachedEmbedding(cacheKey) {
    const hit = embeddingCache.get(cacheKey);
    if (!hit) {
        return null;
    }
    if (hit.expiresAtMs < Date.now()) {
        embeddingCache.delete(cacheKey);
        return null;
    }
    return hit.vector;
}
function setCachedEmbedding(cacheKey, vector) {
    embeddingCache.set(cacheKey, {
        vector,
        expiresAtMs: Date.now() + CACHE_TTL_MS,
    });
    evictIfNeeded();
}
export async function embedText(text) {
    const normalized = normalizeText(text);
    const cacheKey = normalized.toLowerCase();
    const cached = getCachedEmbedding(cacheKey);
    if (cached) {
        return cached;
    }
    const extractor = await getExtractor();
    const output = await extractor(normalized, { pooling: "mean", normalize: true });
    const vector = toVector(output);
    setCachedEmbedding(cacheKey, vector);
    return vector;
}
export async function embedTexts(texts) {
    const embeddings = new Array(texts.length);
    for (let index = 0; index < texts.length; index += EMBEDDING_BATCH_SIZE) {
        const chunk = texts.slice(index, index + EMBEDDING_BATCH_SIZE);
        const chunkResults = await Promise.all(chunk.map((text) => embedText(text)));
        chunkResults.forEach((embedding, batchIndex) => {
            embeddings[index + batchIndex] = embedding;
        });
    }
    return embeddings;
}
//# sourceMappingURL=embedding.js.map