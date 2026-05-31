/**
 * Curriculum Seed Script
 * Populates: subjects, chapters, topics tables
 * Run once (or with --force to re-seed)
 *
 * Usage:
 *   npx ts-node seed-curriculum.ts
 *   npx ts-node seed-curriculum.ts --force   # clears and re-seeds
 */

import { Pool } from "pg"; // or swap for mysql2, better-sqlite3, etc.
import { CLASSES, Chapter, Subject } from "./curriculum";

// ── DB connection ─────────────────────────────────────────────────────────────
// Replace with your actual connection string / env variable
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  // ssl: { rejectUnauthorized: false },   // uncomment for hosted DBs
});

// ── Helpers ───────────────────────────────────────────────────────────────────

/** Upsert a subject row; returns its DB id */
async function upsertSubject(
  client: any,
  code: string,
  name: string,
  description: string,
  icon: string,
): Promise<number> {
  const { rows } = await client.query(
    `INSERT INTO subjects (code, name, description, icon)
     VALUES ($1, $2, $3, $4)
     ON CONFLICT (code)
     DO UPDATE SET name = EXCLUDED.name,
                   description = EXCLUDED.description,
                   icon = EXCLUDED.icon
     RETURNING id`,
    [code, name, description, icon],
  );
  return rows[0].id;
}

/** Upsert a chapter row; returns its DB id */
async function upsertChapter(
  client: any,
  subjectId: number,
  name: string,
  className: string,
  description: string,
): Promise<number> {
  const { rows } = await client.query(
    `INSERT INTO chapters (subject_id, name, class_name, description)
     VALUES ($1, $2, $3, $4)
     ON CONFLICT (subject_id, name, class_name)
     DO UPDATE SET description = EXCLUDED.description
     RETURNING id`,
    [subjectId, name, className, description],
  );
  return rows[0].id;
}

/** Upsert a topic row */
async function upsertTopic(
  client: any,
  chapterId: number,
  name: string,
  description: string,
): Promise<void> {
  await client.query(
    `INSERT INTO topics (chapter_id, name, description)
     VALUES ($1, $2, $3)
     ON CONFLICT (chapter_id, name)
     DO UPDATE SET description = EXCLUDED.description`,
    [chapterId, name, description],
  );
}

// ── Main seed logic ────────────────────────────────────────────────────────────

async function seedCurriculum(): Promise<void> {
  const client = await pool.connect();

  try {
    await client.query("BEGIN");

    let subjectCount = 0;
    let chapterCount = 0;
    let topicCount = 0;

    for (const classInfo of CLASSES) {
      const className = String(classInfo.id); // e.g. "6", "7", "10"

      for (const subject of classInfo.subjects) {
        // ── Subject ──────────────────────────────────────────────────────────
        // Use a composite code so the same subject across classes stays unique
        // e.g.  "math" + class 6  →  "math"  (subjects are shared across classes)
        // If your schema treats subjects per-class, change the code to `${subject.id}_${className}`
        const subjectCode = subject.id; // "math", "science", "physics", "biology", "evs"

        const subjectId = await upsertSubject(
          client,
          subjectCode,
          subject.name,
          subject.description,
          subject.icon,
        );
        subjectCount++;

        // ── Chapters ─────────────────────────────────────────────────────────
        if (typeof subject.chapters === "number") {
          // Abbreviated entry (classes 1-5 and some subjects) — generate placeholder chapters
          for (let i = 1; i <= subject.chapters; i++) {
            const chapterName = `Chapter ${i}`;
            const chapterId = await upsertChapter(
              client,
              subjectId,
              chapterName,
              className,
              `${subject.name} – Chapter ${i}`,
            );
            chapterCount++;

            // No detailed topics available for abbreviated entries
          }
        } else {
          // Full chapter + topic data
          for (const chapter of subject.chapters as Chapter[]) {
            const chapterId = await upsertChapter(
              client,
              subjectId,
              chapter.name,
              className,
              `${subject.name} – ${chapter.name}`,
            );
            chapterCount++;

            // ── Topics ──────────────────────────────────────────────────────
            for (const topic of chapter.topics) {
              await upsertTopic(
                client,
                chapterId,
                topic.name,
                topic.name, // description defaults to name; extend if you add descriptions
              );
              topicCount++;
            }
          }
        }
      }
    }

    await client.query("COMMIT");

    console.log("✅  Curriculum seeded successfully");
    console.log(`    Subjects : ${subjectCount}`);
    console.log(`    Chapters : ${chapterCount}`);
    console.log(`    Topics   : ${topicCount}`);
  } catch (err) {
    await client.query("ROLLBACK");
    console.error("❌  Seed failed – transaction rolled back:", err);
    throw err;
  } finally {
    client.release();
    await pool.end();
  }
}

seedCurriculum().catch(() => process.exit(1));
