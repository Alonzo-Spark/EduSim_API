/**
 * EduSim API Routes  –  integration example
 * Mount these in your Express app, e.g.:
 *   app.use("/api", router);
 *
 * Every handler calls the db-service functions and
 * also touches activity / session tracking per spec.
 */

import { Router, Request, Response, NextFunction } from "express";
import * as db from "./db-service";
import bcrypt from "bcryptjs";
import { v4 as uuid } from "uuid";

export const router = Router();

// ── Middleware: resolve session + touch activity ───────────────────────────────

async function requireAuth(req: Request, res: Response, next: NextFunction) {
  const key = req.headers["x-session-key"] as string;
  if (!key) return res.status(401).json({ error: "No session key" });

  const session = await db.getActiveSession(key);
  if (!session) return res.status(401).json({ error: "Invalid or expired session" });

  (req as any).userId = session.user_id;
  (req as any).role = session.role;

  // Spec: update last_active_at on every action
  await db.touchActivity(session.user_id);
  next();
}

// ─────────────────────────────────────────────────────────────────────────────
// AUTH
// ─────────────────────────────────────────────────────────────────────────────

/** POST /api/auth/register */
router.post("/auth/register", async (req, res) => {
  try {
    const { name, email, password, mobile_number, role } = req.body;
    const password_hash = await bcrypt.hash(password, 12);
    const user = await db.createUser({ name, email, password_hash, mobile_number, role });
    res.status(201).json({ user });
  } catch (err: any) {
    res.status(400).json({ error: err.message });
  }
});

/** POST /api/auth/login */
router.post("/auth/login", async (req, res) => {
  try {
    const { email, password } = req.body;

    // Fetch user (add your own getUserByEmail helper or inline query)
    const [user] = await (db as any).query?.(
      `SELECT id, password_hash, role FROM users WHERE email = $1`,
      [email],
    ) ?? [];
    if (!user) return res.status(401).json({ error: "Invalid credentials" });

    const valid = await bcrypt.compare(password, user.password_hash);
    if (!valid) return res.status(401).json({ error: "Invalid credentials" });

    // Create session – expires in 7 days
    const sessionKey = uuid();
    const expiresAt = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000);
    const session = await db.createSession({
      user_id: user.id,
      session_key: sessionKey,
      expires_at: expiresAt,
    });

    // Spec: update last_login_at + last_active_at
    await db.recordLogin(user.id);

    res.json({ session_key: sessionKey, expires_at: expiresAt, role: user.role });
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

/** POST /api/auth/logout */
router.post("/auth/logout", requireAuth, async (req, res) => {
  const key = req.headers["x-session-key"] as string;
  await db.endSession(key);
  res.json({ ok: true });
});

// ─────────────────────────────────────────────────────────────────────────────
// SETTINGS
// ─────────────────────────────────────────────────────────────────────────────

/** GET /api/settings */
router.get("/settings", requireAuth, async (req, res) => {
  const settings = await db.getSettings((req as any).userId);
  res.json({ settings });
});

/** PUT /api/settings  – body: { key, value } or { settings: { key: value } } */
router.put("/settings", requireAuth, async (req, res) => {
  const userId = (req as any).userId;
  if (req.body.settings) {
    await db.saveSettings(userId, req.body.settings);
  } else {
    await db.saveSetting(userId, req.body.key, req.body.value);
  }
  res.json({ ok: true });
});

// ─────────────────────────────────────────────────────────────────────────────
// AI TUTOR
// ─────────────────────────────────────────────────────────────────────────────

/**
 * POST /api/tutor/interact
 * Body: { session_id, topic, content, summary, class_name, subject }
 *
 * Your frontend should:
 *  1. Call the AI, get the full response
 *  2. Generate a short summary (or ask the AI to summarise)
 *  3. POST here with prompt (content) + summary only
 *
 * Per spec: full AI response is NOT saved.
 */
router.post("/tutor/interact", requireAuth, async (req, res) => {
  try {
    const { session_id, topic, content, summary, class_name, subject } = req.body;
    const row = await db.saveTutorInteraction({
      user_id: (req as any).userId,
      session_id,
      topic,
      content,
      summary,
      class_name,
      subject,
    });
    res.status(201).json({ id: row.id, created_at: row.created_at });
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

/** GET /api/tutor/history?limit=50 */
router.get("/tutor/history", requireAuth, async (req, res) => {
  const limit = Number(req.query.limit) || 50;
  const history = await db.getTutorHistory((req as any).userId, limit);
  res.json({ history });
});

// ─────────────────────────────────────────────────────────────────────────────
// SIMULATIONS
// ─────────────────────────────────────────────────────────────────────────────

/**
 * POST /api/simulations
 * Body: { simulation_id, title, description, score, completion_percentage, time_spent }
 * Saves metadata only – no physics/UI state per spec.
 */
router.post("/simulations", requireAuth, async (req, res) => {
  try {
    const { simulation_id, title, description, score, completion_percentage, time_spent } =
      req.body;
    const row = await db.saveSimulation({
      user_id: (req as any).userId,
      simulation_id,
      title,
      description,
      score,
      completion_percentage,
      time_spent,
    });
    res.status(201).json({ id: row.id, created_at: row.created_at });
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

/** GET /api/simulations/history */
router.get("/simulations/history", requireAuth, async (req, res) => {
  const history = await db.getSimulationHistory((req as any).userId);
  res.json({ history });
});

// ─────────────────────────────────────────────────────────────────────────────
// CURRICULUM  (read-only)
// ─────────────────────────────────────────────────────────────────────────────

/** GET /api/curriculum/:classId  – full tree: subjects → chapters → topics */
router.get("/curriculum/:classId", requireAuth, async (req, res) => {
  const curriculum = await db.getCurriculumForClass(req.params.classId);
  res.json({ curriculum });
});

/** GET /api/curriculum/:classId/:subjectCode/chapters */
router.get("/curriculum/:classId/:subjectCode/chapters", requireAuth, async (req, res) => {
  const chapters = await db.getChapters(req.params.subjectCode, req.params.classId);
  res.json({ chapters });
});

/** GET /api/curriculum/chapters/:chapterId/topics */
router.get("/curriculum/chapters/:chapterId/topics", requireAuth, async (req, res) => {
  const topics = await db.getTopics(Number(req.params.chapterId));
  res.json({ topics });
});

// ── formula_history: no routes, no persistence ────────────────────────────────
