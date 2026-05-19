import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import pgvector from "pgvector/pg";
import { initializeDatabase, withClient } from "../db/db.js";
import { chunkTextbookDocument, deriveMetadataFromPath } from "./chunker.js";
import { embedTexts } from "./embedding.js";
import { logger } from "../utils/logger.js";
import { resolveOrCreateCurriculumIds } from "../services/curriculum.js";
const DEFAULT_TEXTBOOK_ROOT = path.resolve(process.cwd(), "data", "textbooks");
const INGEST_BATCH_SIZE = 8;
async function readPdf(filePath) {
    const pdfParseModule = await import("pdf-parse");
    const pdfBuffer = await fs.readFile(filePath);
    const pdfParse = pdfParseModule;
    const parsedPdf = await pdfParse(pdfBuffer);
    return typeof parsedPdf.text === "string" ? parsedPdf.text : "";
}
async function findPdfFiles(rootDir) {
    const entries = await fs.readdir(rootDir, { withFileTypes: true });
    const pdfFiles = [];
    for (const entry of entries) {
        const resolvedPath = path.join(rootDir, entry.name);
        if (entry.isDirectory()) {
            pdfFiles.push(...(await findPdfFiles(resolvedPath)));
            continue;
        }
        if (entry.isFile() && entry.name.toLowerCase().endsWith(".pdf")) {
            pdfFiles.push(resolvedPath);
        }
    }
    return pdfFiles;
}
function batchItems(items, batchSize) {
    const batches = [];
    for (let index = 0; index < items.length; index += batchSize) {
        batches.push(items.slice(index, index + batchSize));
    }
    return batches;
}
async function insertChunk(client, chunk, embedding) {
    const curriculumIds = await resolveOrCreateCurriculumIds(client, {
        className: chunk.className,
        subject: chunk.subject,
        chapter: chunk.chapter,
        topic: chunk.topic,
    });
    const insertResult = await client.query(`
      INSERT INTO textbook_chunks (
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
        embedding
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
      ON CONFLICT DO NOTHING
    `, [
        curriculumIds.classId,
        curriculumIds.subjectId,
        curriculumIds.chapterId,
        curriculumIds.topicId,
        chunk.className,
        chunk.subject,
        chunk.chapter,
        chunk.topic,
        chunk.content,
        chunk.sourceFile,
        chunk.page,
        pgvector.toSql(embedding),
    ]);
    return (insertResult.rowCount ?? 0) > 0;
}
async function ingestPdfFile(rootDir, filePath) {
    const relativePath = path.relative(rootDir, filePath).split(path.sep).join("/");
    logger.info("Processing textbook PDF", { filePath: relativePath });
    const rawText = await readPdf(filePath);
    if (!rawText.trim()) {
        logger.warn(`No extractable text found in ${relativePath}`);
        return;
    }
    const metadata = deriveMetadataFromPath(relativePath);
    const chunks = chunkTextbookDocument({
        rawText,
        sourceFile: relativePath,
        metadata,
    });
    const uniqueChunks = chunks.filter((chunk, index, collection) => {
        return (collection.findIndex((candidate) => candidate.fingerprint === chunk.fingerprint) === index);
    });
    logger.info(`Chunked ${relativePath}`, {
        extractedCharacters: rawText.length,
        generatedChunks: chunks.length,
        deduplicatedChunks: uniqueChunks.length,
    });
    let insertedCount = 0;
    let skippedCount = 0;
    for (const chunkBatch of batchItems(uniqueChunks, INGEST_BATCH_SIZE)) {
        const embeddings = await embedTexts(chunkBatch.map((chunk) => chunk.content));
        await withClient(async (client) => {
            await client.query("BEGIN");
            try {
                for (const [index, chunk] of chunkBatch.entries()) {
                    const embedding = embeddings[index];
                    if (!chunk || !embedding) {
                        continue;
                    }
                    const inserted = await insertChunk(client, chunk, embedding);
                    if (inserted) {
                        insertedCount += 1;
                    }
                    else {
                        skippedCount += 1;
                    }
                }
                await client.query("COMMIT");
            }
            catch (error) {
                await client.query("ROLLBACK");
                throw error;
            }
        });
    }
    logger.info(`Completed ingest for ${relativePath}`, {
        insertedCount,
        skippedCount,
    });
}
export async function runIngestion(rootDir = DEFAULT_TEXTBOOK_ROOT) {
    await initializeDatabase();
    const pdfFiles = await findPdfFiles(rootDir);
    if (pdfFiles.length === 0) {
        logger.warn(`No textbook PDFs found under ${rootDir}`);
        return;
    }
    logger.info(`Found ${pdfFiles.length} textbook PDF(s)`, { rootDir });
    for (const filePath of pdfFiles) {
        await ingestPdfFile(rootDir, filePath);
    }
    logger.info("Ingestion complete");
}
const isMainModule = process.argv[1]
    ? path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)
    : false;
if (isMainModule) {
    void runIngestion().catch((error) => {
        logger.error("Ingestion failed", error);
        process.exitCode = 1;
    });
}
//# sourceMappingURL=ingest.js.map