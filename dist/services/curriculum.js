import { query } from "../db/db.js";
function clean(value) {
    const normalized = value?.trim().replace(/\s+/g, " ");
    return normalized ? normalized : null;
}
async function upsertClass(client, className) {
    const result = await client.query(`
      INSERT INTO classes (name, sort_order)
      VALUES ($1, 0)
      ON CONFLICT (name) DO UPDATE SET updated_at = NOW()
      RETURNING id
    `, [className]);
    return result.rows[0].id;
}
async function upsertSubject(client, classId, subject) {
    const result = await client.query(`
      INSERT INTO subjects (class_id, name, sort_order)
      VALUES ($1, $2, 0)
      ON CONFLICT (class_id, name) DO UPDATE SET updated_at = NOW()
      RETURNING id
    `, [classId, subject]);
    return result.rows[0].id;
}
async function upsertChapter(client, subjectId, chapter) {
    const result = await client.query(`
      INSERT INTO chapters (subject_id, name, sort_order)
      VALUES ($1, $2, 0)
      ON CONFLICT (subject_id, name) DO UPDATE SET updated_at = NOW()
      RETURNING id
    `, [subjectId, chapter]);
    return result.rows[0].id;
}
async function upsertTopic(client, chapterId, topic) {
    const result = await client.query(`
      INSERT INTO topics (chapter_id, name, sort_order)
      VALUES ($1, $2, 0)
      ON CONFLICT (chapter_id, name) DO UPDATE SET updated_at = NOW()
      RETURNING id
    `, [chapterId, topic]);
    return result.rows[0].id;
}
export async function resolveOrCreateCurriculumIds(client, input) {
    const className = clean(input.className);
    const subject = clean(input.subject);
    const chapter = clean(input.chapter);
    const topic = clean(input.topic);
    let classId = null;
    let subjectId = null;
    let chapterId = null;
    let topicId = null;
    if (className) {
        classId = await upsertClass(client, className);
    }
    if (classId && subject) {
        subjectId = await upsertSubject(client, classId, subject);
    }
    if (subjectId && chapter) {
        chapterId = await upsertChapter(client, subjectId, chapter);
    }
    if (chapterId && topic) {
        topicId = await upsertTopic(client, chapterId, topic);
    }
    return { classId, subjectId, chapterId, topicId };
}
export async function getClasses() {
    const result = await query(`
      SELECT id, name, sort_order
      FROM classes
      ORDER BY sort_order ASC, name ASC
    `);
    return result.rows.map((row) => ({
        id: row.id,
        name: row.name,
        sortOrder: row.sort_order,
    }));
}
export async function getSubjects(classId) {
    const result = await query(`
      SELECT id, name, sort_order
      FROM subjects
      WHERE class_id = $1
      ORDER BY sort_order ASC, name ASC
    `, [classId]);
    return result.rows.map((row) => ({
        id: row.id,
        name: row.name,
        sortOrder: row.sort_order,
    }));
}
export async function getChapters(subjectId) {
    const result = await query(`
      SELECT id, name, sort_order
      FROM chapters
      WHERE subject_id = $1
      ORDER BY sort_order ASC, name ASC
    `, [subjectId]);
    return result.rows.map((row) => ({
        id: row.id,
        name: row.name,
        sortOrder: row.sort_order,
    }));
}
export async function getTopics(chapterId) {
    const result = await query(`
      SELECT id, name, sort_order
      FROM topics
      WHERE chapter_id = $1
      ORDER BY sort_order ASC, name ASC
    `, [chapterId]);
    return result.rows.map((row) => ({
        id: row.id,
        name: row.name,
        sortOrder: row.sort_order,
    }));
}
//# sourceMappingURL=curriculum.js.map