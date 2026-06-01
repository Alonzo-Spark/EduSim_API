/**
 * EduSim Database Service
 * Covers every table the spec marks as "Active":
 *   users, user_sessions, user_settings, chat_history, simulation_history
 *   subjects / chapters / topics  (read-only at runtime; seeded separately)
 *
 * formula_history → intentionally untouched (spec: Unused / no inserts)
 *
 * Adapt the `query` helper at the top to match your ORM / driver.
 */

import { Pool, PoolClient } from "pg";

const pool = new Pool({ connectionString: process.env.DATABASE_URL });

/** Thin wrapper – swap for Prisma / Drizzle / Knex if preferred */
async function query<T = any>(sql: string, params: any[] = []): Promise<T[]> {
  const { rows } = await pool.query(sql, params);
  return rows as T[];
}

// ─────────────────────────────────────────────────────────────────────────────
// USERS
// ─────────────────────────────────────────────────────────────────────────────

export interface CreateUserInput {
  name: string;
  email: string;
  password_hash: string;
  mobile_number?: string;
  role?: string; // "student" | "teacher" | "admin"
}

/** Register a new user */
export async function createUser(input: CreateUserInput) {
  const [user] = await query(
    `INSERT INTO users (name, email, password_hash, mobile_number, role,
                        created_at, updated_at)
     VALUES ($1, $2, $3, $4, $5, NOW(), NOW())
     RETURNING id, name, email, mobile_number, role, created_at`,
    [
      input.name,
      input.email,
      input.password_hash,
      input.mobile_number ?? null,
      input.role ?? "student",
    ],
  );
  return user;
}

/** Called on every successful login */
export async function recordLogin(userId: string) {
  await query(
    `UPDATE users
     SET last_login_at = NOW(), last_active_at = NOW(), updated_at = NOW()
     WHERE id = $1`,
    [userId],
  );
}

/** Called on any user action (page visit, quiz attempt, etc.) */
export async function touchActivity(userId: string) {
  await query(
    `UPDATE users SET last_active_at = NOW(), updated_at = NOW() WHERE id = $1`,
    [userId],
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// USER SESSIONS
// ─────────────────────────────────────────────────────────────────────────────

export interface CreateSessionInput {
  user_id: string;
  session_key: string;
  expires_at: Date;
}

/** Create a session row after login */
export async function createSession(input: CreateSessionInput) {
  const [session] = await query(
    `INSERT INTO user_sessions
       (user_id, session_key, last_login_at, is_active, expires_at, created_at, updated_at)
     VALUES ($1, $2, NOW(), true, $3, NOW(), NOW())
     RETURNING id, session_key, expires_at`,
    [input.user_id, input.session_key, input.expires_at],
  );
  return session;
}

/** Invalidate a session on logout */
export async function endSession(sessionKey: string) {
  await query(
    `UPDATE user_sessions
     SET is_active = false, last_logout_at = NOW(), updated_at = NOW()
     WHERE session_key = $1`,
    [sessionKey],
  );
}

/** Validate and return an active session */
export async function getActiveSession(sessionKey: string) {
  const [session] = await query(
    `SELECT us.*, u.id AS user_id, u.role
     FROM user_sessions us
     JOIN users u ON u.id = us.user_id
     WHERE us.session_key = $1
       AND us.is_active = true
       AND us.expires_at > NOW()`,
    [sessionKey],
  );
  return session ?? null;
}

// ─────────────────────────────────────────────────────────────────────────────
// USER SETTINGS
// ─────────────────────────────────────────────────────────────────────────────

type SettingKey =
  | "theme"
  | "selected_subject"
  | "selected_class"
  | "notifications"
  | "language";

/** Upsert a single setting for a user */
export async function saveSetting(
  userId: string,
  key: SettingKey,
  value: string,
) {
  await query(
    `INSERT INTO user_settings (user_id, setting_key, setting_value, updated_at)
     VALUES ($1, $2, $3::jsonb, NOW())
     ON CONFLICT (user_id, setting_key)
     DO UPDATE SET setting_value = EXCLUDED.setting_value,
                   updated_at = NOW()`,
    [userId, key, JSON.stringify({ value })],
  );
}

/** Bulk-save multiple settings at once (e.g. from a settings page) */
export async function saveSettings(
  userId: string,
  settings: Partial<Record<SettingKey, string>>,
) {
  for (const [key, value] of Object.entries(settings)) {
    await saveSetting(userId, key as SettingKey, value as string);
  }
}

/** Retrieve all settings for a user as a flat key→value map */
export async function getSettings(
  userId: string,
): Promise<Partial<Record<SettingKey, string>>> {
  const rows = await query(
    `SELECT setting_key, setting_value FROM user_settings WHERE user_id = $1`,
    [userId],
  );
  return Object.fromEntries(
    rows.map((r) => [r.setting_key, (r.setting_value as any)?.value ?? null]),
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// CHAT HISTORY  (AI Tutor)
// ─────────────────────────────────────────────────────────────────────────────

export interface SaveTutorInteractionInput {
  user_id: string;
  session_id: string; // logical tutor session (UUID from frontend)
  topic: string;
  content: string; // user's original prompt
  summary: string; // AI-generated summary of the response
  class_name: string; // e.g. "10"
  subject: string; // e.g. "Physics"
}

/**
 * Save ONE tutor interaction.
 * Per spec: one row = one interaction.
 * We save prompt + summary only – NOT the full AI response.
 */
export async function saveTutorInteraction(input: SaveTutorInteractionInput) {
  const [row] = await query(
    `INSERT INTO chat_history
       (user_id, session_id, session_type, role, topic, content, summary,
        metadata_json, created_at)
     VALUES ($1, $2, 'tutor', 'user', $3, $4, $5, $6::jsonb, NOW())
     RETURNING id, created_at`,
    [
      input.user_id,
      input.session_id,
      input.topic,
      input.content,
      input.summary,
      JSON.stringify({ class_name: input.class_name, subject: input.subject }),
    ],
  );
  return row;
}

/** Recent tutor history for a user (latest first) */
export async function getTutorHistory(userId: string, limit = 50) {
  return query(
    `SELECT id, session_id, topic, content, summary, metadata_json, created_at
     FROM chat_history
     WHERE user_id = $1 AND session_type = 'tutor'
     ORDER BY created_at DESC
     LIMIT $2`,
    [userId, limit],
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// SIMULATION HISTORY
// ─────────────────────────────────────────────────────────────────────────────

export interface SaveSimulationInput {
  user_id: string;
  simulation_id: string; // stable identifier for the simulation type
  title: string;
  description: string;
  score?: number;
  completion_percentage: number;
  time_spent: number; // seconds
}

/**
 * Insert a simulation result.
 * Stores metadata only – no object positions, frame data, or physics state.
 */
export async function saveSimulation(input: SaveSimulationInput) {
  const [row] = await query(
    `INSERT INTO simulation_history
       (user_id, simulation_id, title, description, score,
        runtime_json, created_at, updated_at)
     VALUES ($1, $2, $3, $4, $5, $6::jsonb, NOW(), NOW())
     RETURNING id, created_at`,
    [
      input.user_id,
      input.simulation_id,
      input.title,
      input.description,
      input.score ?? null,
      JSON.stringify({
        completion_percentage: input.completion_percentage,
        time_spent: input.time_spent,
      }),
    ],
  );
  return row;
}

/** Update score/completion for an existing simulation row */
export async function updateSimulation(
  simulationRowId: string,
  updates: Partial<Pick<SaveSimulationInput, "score" | "completion_percentage" | "time_spent">>,
) {
  await query(
    `UPDATE simulation_history
     SET score = COALESCE($2, score),
         runtime_json = runtime_json || $3::jsonb,
         updated_at = NOW()
     WHERE id = $1`,
    [
      simulationRowId,
      updates.score ?? null,
      JSON.stringify({
        ...(updates.completion_percentage !== undefined && {
          completion_percentage: updates.completion_percentage,
        }),
        ...(updates.time_spent !== undefined && {
          time_spent: updates.time_spent,
        }),
      }),
    ],
  );
}

export async function getSimulationHistory(userId: string, limit = 50) {
  return query(
    `SELECT id, simulation_id, title, description, score, runtime_json,
            created_at, updated_at
     FROM simulation_history
     WHERE user_id = $1
     ORDER BY created_at DESC
     LIMIT $2`,
    [userId, limit],
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// CURRICULUM  (read-only at runtime – seeded by seed-curriculum.ts)
// ─────────────────────────────────────────────────────────────────────────────

/** All subjects */
export async function getAllSubjects() {
  return query(`SELECT id, code, name, description, icon FROM subjects ORDER BY name`);
}

/** Chapters for a subject + class */
export async function getChapters(subjectCode: string, className: string) {
  return query(
    `SELECT c.id, c.name, c.description
     FROM chapters c
     JOIN subjects s ON s.id = c.subject_id
     WHERE s.code = $1 AND c.class_name = $2
     ORDER BY c.id`,
    [subjectCode, className],
  );
}

/** Topics for a chapter */
export async function getTopics(chapterId: string) {
  return query(
    `SELECT id, name, description FROM topics WHERE chapter_id = $1 ORDER BY id`,
    [chapterId],
  );
}

/** Full curriculum tree for one class (subjects → chapters → topics) */
export async function getCurriculumForClass(className: string) {
  const subjects = await query(
    `SELECT DISTINCT s.id, s.code, s.name, s.description, s.icon
     FROM subjects s
     JOIN chapters c ON c.subject_id = s.id
     WHERE c.class_name = $1
     ORDER BY s.name`,
    [className],
  );

  for (const subject of subjects) {
    subject.chapters = await query(
      `SELECT c.id, c.name, c.description FROM chapters c
       WHERE c.subject_id = $1 AND c.class_name = $2
       ORDER BY c.id`,
      [subject.id, className],
    );
    for (const chapter of subject.chapters) {
      chapter.topics = await getTopics(chapter.id);
    }
  }

  return subjects;
}

// ─────────────────────────────────────────────────────────────────────────────
// FORMULA HISTORY  –  intentionally left empty per spec
// ─────────────────────────────────────────────────────────────────────────────
// No functions exported. Formula Lab runs in-memory only.
