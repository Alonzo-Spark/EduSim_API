import { randomUUID } from "node:crypto";
import { Router } from "express";
import { query } from "../db/db.js";
import { getNumberEnv } from "../utils/env.js";
import { HttpError } from "../middleware/error.js";
import { createInMemoryRateLimiter } from "../middleware/rate-limit.js";
import { retrieveRelevantChunks, } from "../rag/retriever.js";
import { logger } from "../utils/logger.js";
import { openRouterClient } from "../utils/openrouter.js";
const tutorRouter = Router();
const rateLimiter = createInMemoryRateLimiter({
    windowMs: getNumberEnv("TUTOR_RATE_LIMIT_WINDOW_MS", 60_000),
    maxRequests: getNumberEnv("TUTOR_RATE_LIMIT_MAX_REQUESTS", 30),
});
tutorRouter.use(rateLimiter);
function toPositiveInt(value) {
    if (value === null || value === undefined || value === "") {
        return null;
    }
    const parsed = Number(value);
    return Number.isInteger(parsed) && parsed > 0 ? parsed : null;
}
function requiredTrimmed(value, field) {
    const parsed = typeof value === "string" ? value.trim() : "";
    if (!parsed) {
        throw new HttpError(`${field} is required`, 400);
    }
    return parsed;
}
function optionalTrimmed(value) {
    const parsed = typeof value === "string" ? value.trim() : "";
    return parsed || null;
}
function clampTopK(value) {
    const parsedValue = typeof value === "number" ? value : Number(value);
    if (!Number.isFinite(parsedValue)) {
        return 6;
    }
    return Math.max(1, Math.min(Math.trunc(parsedValue), 25));
}
function resolveScope(base, override) {
    return {
        classId: override.classId ?? base.classId,
        subjectId: override.subjectId ?? base.subjectId,
        chapterId: override.chapterId ?? base.chapterId,
        topicId: override.topicId ?? base.topicId,
    };
}
function buildCitationContext(chunks) {
    if (chunks.length === 0) {
        return {
            promptText: "No textbook chunks met the retrieval threshold.",
            citations: [],
            averageScore: 0,
        };
    }
    const citations = chunks.map((chunk, index) => ({
        citationNumber: index + 1,
        id: chunk.id,
        classId: chunk.classId,
        subjectId: chunk.subjectId,
        chapterId: chunk.chapterId,
        topicId: chunk.topicId,
        className: chunk.className,
        subject: chunk.subject,
        chapter: chunk.chapter,
        topic: chunk.topic,
        sourceFile: chunk.sourceFile,
        page: chunk.page,
        semanticScore: chunk.semanticScore,
        keywordScore: chunk.keywordScore,
        score: chunk.score,
        excerpt: chunk.content.slice(0, 420),
    }));
    const promptText = chunks
        .map((chunk, index) => {
        const citationLabel = [
            `[${index + 1}]`,
            chunk.className ?? "Unknown class",
            chunk.subject ?? "Unknown subject",
            chunk.chapter ?? "Unknown chapter",
            chunk.topic ?? "Unknown topic",
            `p.${chunk.page}`,
            `${chunk.sourceFile}`,
            `score=${chunk.score.toFixed(3)} semantic=${chunk.semanticScore.toFixed(3)} keyword=${chunk.keywordScore.toFixed(3)}`,
        ].join(" | ");
        return `${citationLabel}\n${chunk.content}`;
    })
        .join("\n\n---\n\n");
    const averageScore = chunks.reduce((total, chunk) => total + chunk.score, 0) / chunks.length;
    return { promptText, citations, averageScore };
}
function buildTutorSystemPrompt(allowFallback, groundedEnough) {
    const common = [
        "You are EduSim, a textbook-grounded educational tutor.",
        "Output in markdown.",
        "Always structure your answer with sections: Definitions, Explanation, Steps, Example, Summary.",
        "If formulas are relevant, write them in LaTeX using $...$ for inline and $$...$$ for block formulas.",
        "Cite textbook-supported claims with citation numbers like [1], [2].",
        "Never fabricate citations.",
    ];
    if (allowFallback && !groundedEnough) {
        return [
            ...common,
            "Textbook context may be incomplete; clearly label any fallback knowledge section as 'Fallback knowledge'.",
            "Explicitly state where textbook evidence is insufficient.",
        ].join(" ");
    }
    if (!groundedEnough) {
        return [
            ...common,
            "Do not use outside knowledge.",
            "Explain that textbook context is insufficient and answer only what can be supported.",
        ].join(" ");
    }
    return [
        ...common,
        "Prefer concise but educational explanations with step-by-step clarity.",
        "If asked to solve, show intermediate steps.",
    ].join(" ");
}
function buildUserPrompt(question, contextText, history) {
    return [
        `Student question: ${question}`,
        "",
        "Recent conversation context:",
        history.length
            ? history.map((entry) => `${entry.role.toUpperCase()}: ${entry.content}`).join("\n")
            : "(no previous messages)",
        "",
        "Textbook context:",
        contextText,
        "",
        "Response rules:",
        "- Use textbook context first and cite claims with [n].",
        "- Be pedagogical and accurate.",
        "- If context is weak, state that explicitly.",
    ].join("\n");
}
async function getThread(threadId) {
    const result = await query(`
      SELECT id, session_id, title, class_id, subject_id, chapter_id, topic_id
      FROM tutor_threads
      WHERE id = $1
    `, [threadId]);
    const thread = result.rows[0];
    if (!thread) {
        throw new HttpError("Thread not found", 404);
    }
    return thread;
}
async function saveMessage(input) {
    const result = await query(`
      INSERT INTO tutor_messages (thread_id, role, content, citations, retrieval_metadata)
      VALUES ($1, $2, $3, $4::jsonb, $5::jsonb)
      RETURNING id, thread_id, role, content, citations, retrieval_metadata, created_at
    `, [
        input.threadId,
        input.role,
        input.content,
        JSON.stringify(input.citations ?? []),
        JSON.stringify(input.retrievalMetadata ?? null),
    ]);
    return result.rows[0];
}
async function touchThread(threadId, titleCandidate) {
    await query(`
      UPDATE tutor_threads
      SET
        title = CASE
          WHEN title = 'New chat' AND $2::text IS NOT NULL THEN left($2, 80)
          ELSE title
        END,
        updated_at = NOW()
      WHERE id = $1
    `, [threadId, titleCandidate ?? null]);
}
async function updateProgress(input) {
    const confidence = Math.max(0, Math.min(1, input.confidenceScore));
    await query(`
      INSERT INTO user_progress (
        session_id, class_id, subject_id, chapter_id, topic_id,
        questions_asked, topics_explored, completed_chapters,
        current_streak, xp, confidence_score, last_question_on, last_interacted_at
      )
      VALUES ($1, $2, $3, $4, $5, 1, CASE WHEN $5 IS NULL THEN 0 ELSE 1 END, 0, 1, $6, $7, CURRENT_DATE, NOW())
      ON CONFLICT (session_id, topic_id) WHERE topic_id IS NOT NULL
      DO UPDATE SET
        class_id = COALESCE(EXCLUDED.class_id, user_progress.class_id),
        subject_id = COALESCE(EXCLUDED.subject_id, user_progress.subject_id),
        chapter_id = COALESCE(EXCLUDED.chapter_id, user_progress.chapter_id),
        questions_asked = user_progress.questions_asked + 1,
        topics_explored = GREATEST(user_progress.topics_explored, CASE WHEN EXCLUDED.topic_id IS NULL THEN 0 ELSE 1 END),
        xp = user_progress.xp + EXCLUDED.xp,
        confidence_score = (user_progress.confidence_score * 0.7) + (EXCLUDED.confidence_score * 0.3),
        current_streak = CASE
          WHEN user_progress.last_question_on = CURRENT_DATE THEN user_progress.current_streak
          WHEN user_progress.last_question_on = CURRENT_DATE - INTERVAL '1 day' THEN user_progress.current_streak + 1
          ELSE 1
        END,
        last_question_on = CURRENT_DATE,
        last_interacted_at = NOW()
    `, [
        input.sessionId,
        input.scope.classId,
        input.scope.subjectId,
        input.scope.chapterId,
        input.scope.topicId,
        input.xpDelta,
        confidence,
    ]);
}
async function loadConversationHistory(threadId, limit = 12) {
    const result = await query(`
      SELECT role, content
      FROM tutor_messages
      WHERE thread_id = $1
      ORDER BY created_at DESC
      LIMIT $2
    `, [threadId, limit]);
    return [...result.rows].reverse();
}
async function generateTutorAnswer(input) {
    const topK = clampTopK(input.options.topK);
    const allowFallback = Boolean(input.options.allowFallback);
    const retrievalOptions = {
        topK,
        minimumSimilarity: 0,
    };
    const resolvedClassId = toPositiveInt(input.options.classId) ?? input.thread.class_id;
    const resolvedSubjectId = toPositiveInt(input.options.subjectId) ?? input.thread.subject_id;
    const resolvedChapterId = toPositiveInt(input.options.chapterId) ?? input.thread.chapter_id;
    const resolvedTopicId = toPositiveInt(input.options.topicId) ?? input.thread.topic_id;
    if (resolvedClassId !== null)
        retrievalOptions.classId = resolvedClassId;
    if (resolvedSubjectId !== null)
        retrievalOptions.subjectId = resolvedSubjectId;
    if (resolvedChapterId !== null)
        retrievalOptions.chapterId = resolvedChapterId;
    if (resolvedTopicId !== null)
        retrievalOptions.topicId = resolvedTopicId;
    if (typeof input.options.semanticWeight === "number")
        retrievalOptions.semanticWeight = input.options.semanticWeight;
    if (typeof input.options.keywordWeight === "number")
        retrievalOptions.keywordWeight = input.options.keywordWeight;
    const chunks = await retrieveRelevantChunks(input.content, retrievalOptions);
    const groundedEnough = chunks.some((chunk) => chunk.semanticScore >= 0.35 || chunk.score >= 0.3);
    const citationContext = buildCitationContext(chunks);
    const history = await loadConversationHistory(input.thread.id);
    const completionRequest = {
        messages: [
            { role: "system", content: buildTutorSystemPrompt(allowFallback, groundedEnough) },
            {
                role: "user",
                content: buildUserPrompt(input.content, citationContext.promptText, history),
            },
        ],
        temperature: typeof input.options.temperature === "number" ? input.options.temperature : 0.2,
        maxTokens: 1200,
        timeoutMs: 60_000,
    };
    const model = optionalTrimmed(input.options.model);
    if (model) {
        completionRequest.model = model;
    }
    let answer = "";
    if (input.stream && input.onToken) {
        for await (const token of openRouterClient.chatCompletionStream(completionRequest)) {
            answer += token;
            input.onToken(token);
        }
        answer = answer.trim();
    }
    else {
        const completion = await openRouterClient.chatCompletion(completionRequest);
        answer = completion.content;
    }
    if (!answer) {
        throw new HttpError("AI returned an empty response", 502);
    }
    return {
        answer,
        citations: citationContext.citations,
        retrievalMetadata: {
            topK,
            groundedEnough,
            allowFallback,
            chunkCount: chunks.length,
            scores: chunks.map((chunk) => ({
                id: chunk.id,
                semanticScore: chunk.semanticScore,
                keywordScore: chunk.keywordScore,
                score: chunk.score,
            })),
        },
        grounded: groundedEnough,
    };
}
function writeSse(response, event, payload) {
    response.write(`event: ${event}\n`);
    response.write(`data: ${JSON.stringify(payload)}\n\n`);
}
tutorRouter.get("/threads", async (request, response, next) => {
    try {
        const sessionId = requiredTrimmed(request.query.sessionId, "sessionId");
        const result = await query(`
        SELECT id, title, class_id, subject_id, chapter_id, topic_id, updated_at, created_at
        FROM tutor_threads
        WHERE session_id = $1
        ORDER BY updated_at DESC
        LIMIT 100
      `, [sessionId]);
        response.json({
            threads: result.rows.map((row) => ({
                id: row.id,
                title: row.title,
                classId: row.class_id,
                subjectId: row.subject_id,
                chapterId: row.chapter_id,
                topicId: row.topic_id,
                updatedAt: row.updated_at,
                createdAt: row.created_at,
            })),
        });
    }
    catch (error) {
        next(error);
    }
});
tutorRouter.post("/threads", async (request, response, next) => {
    try {
        const body = request.body;
        const sessionId = requiredTrimmed(body.sessionId, "sessionId");
        const result = await query(`
        INSERT INTO tutor_threads (session_id, title, class_id, subject_id, chapter_id, topic_id)
        VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING id, title, class_id, subject_id, chapter_id, topic_id, updated_at, created_at
      `, [
            sessionId,
            optionalTrimmed(body.title) ?? "New chat",
            toPositiveInt(body.classId),
            toPositiveInt(body.subjectId),
            toPositiveInt(body.chapterId),
            toPositiveInt(body.topicId),
        ]);
        const created = result.rows[0];
        response.status(201).json({
            thread: {
                id: created.id,
                title: created.title,
                classId: created.class_id,
                subjectId: created.subject_id,
                chapterId: created.chapter_id,
                topicId: created.topic_id,
                updatedAt: created.updated_at,
                createdAt: created.created_at,
            },
        });
    }
    catch (error) {
        next(error);
    }
});
tutorRouter.get("/threads/:threadId/messages", async (request, response, next) => {
    try {
        const threadId = requiredTrimmed(request.params.threadId, "threadId");
        const thread = await getThread(threadId);
        const result = await query(`
        SELECT id, role, content, citations, retrieval_metadata, created_at
        FROM tutor_messages
        WHERE thread_id = $1
        ORDER BY created_at ASC
      `, [thread.id]);
        response.json({
            thread: {
                id: thread.id,
                title: thread.title,
                classId: thread.class_id,
                subjectId: thread.subject_id,
                chapterId: thread.chapter_id,
                topicId: thread.topic_id,
            },
            messages: result.rows.map((row) => ({
                id: row.id,
                role: row.role,
                content: row.content,
                citations: row.citations,
                retrievalMetadata: row.retrieval_metadata,
                createdAt: row.created_at,
            })),
        });
    }
    catch (error) {
        next(error);
    }
});
tutorRouter.post("/threads/:threadId/messages", async (request, response, next) => {
    try {
        const threadId = requiredTrimmed(request.params.threadId, "threadId");
        const body = request.body;
        const content = requiredTrimmed(body.content, "content");
        const thread = await getThread(threadId);
        const scope = resolveScope({
            classId: thread.class_id,
            subjectId: thread.subject_id,
            chapterId: thread.chapter_id,
            topicId: thread.topic_id,
        }, {
            classId: toPositiveInt(body.classId),
            subjectId: toPositiveInt(body.subjectId),
            chapterId: toPositiveInt(body.chapterId),
            topicId: toPositiveInt(body.topicId),
        });
        const userMessage = await saveMessage({
            threadId,
            role: "user",
            content,
        });
        const generated = await generateTutorAnswer({
            thread,
            content,
            options: body,
            stream: false,
        });
        const assistantMessage = await saveMessage({
            threadId,
            role: "assistant",
            content: generated.answer,
            citations: generated.citations,
            retrievalMetadata: generated.retrievalMetadata,
        });
        await touchThread(threadId, content);
        await updateProgress({
            sessionId: thread.session_id,
            scope,
            confidenceScore: generated.citations.length > 0
                ? generated.citations.reduce((total, citation) => total + Number(citation.score ?? 0), 0) / generated.citations.length
                : 0,
            xpDelta: 5 + Math.min(20, Math.round(generated.answer.length / 120)),
        });
        response.status(201).json({
            userMessage: {
                id: userMessage.id,
                role: userMessage.role,
                content: userMessage.content,
                citations: userMessage.citations,
                retrievalMetadata: userMessage.retrieval_metadata,
                createdAt: userMessage.created_at,
            },
            assistantMessage: {
                id: assistantMessage.id,
                role: assistantMessage.role,
                content: assistantMessage.content,
                citations: assistantMessage.citations,
                retrievalMetadata: assistantMessage.retrieval_metadata,
                createdAt: assistantMessage.created_at,
            },
            grounded: generated.grounded,
        });
    }
    catch (error) {
        next(error);
    }
});
tutorRouter.post("/threads/:threadId/messages/stream", async (request, response, next) => {
    try {
        const threadId = requiredTrimmed(request.params.threadId, "threadId");
        const body = request.body;
        const content = requiredTrimmed(body.content, "content");
        const thread = await getThread(threadId);
        const scope = resolveScope({
            classId: thread.class_id,
            subjectId: thread.subject_id,
            chapterId: thread.chapter_id,
            topicId: thread.topic_id,
        }, {
            classId: toPositiveInt(body.classId),
            subjectId: toPositiveInt(body.subjectId),
            chapterId: toPositiveInt(body.chapterId),
            topicId: toPositiveInt(body.topicId),
        });
        await saveMessage({
            threadId,
            role: "user",
            content,
        });
        response.status(200);
        response.setHeader("Content-Type", "text/event-stream");
        response.setHeader("Cache-Control", "no-cache");
        response.setHeader("Connection", "keep-alive");
        response.flushHeaders();
        const generated = await generateTutorAnswer({
            thread,
            content,
            options: body,
            stream: true,
            onToken: (token) => {
                writeSse(response, "token", { token });
            },
        });
        const assistantMessage = await saveMessage({
            threadId,
            role: "assistant",
            content: generated.answer,
            citations: generated.citations,
            retrievalMetadata: generated.retrievalMetadata,
        });
        await touchThread(threadId, content);
        await updateProgress({
            sessionId: thread.session_id,
            scope,
            confidenceScore: generated.citations.length > 0
                ? generated.citations.reduce((total, citation) => total + Number(citation.score ?? 0), 0) / generated.citations.length
                : 0,
            xpDelta: 5 + Math.min(20, Math.round(generated.answer.length / 120)),
        });
        writeSse(response, "done", {
            assistantMessage: {
                id: assistantMessage.id,
                role: assistantMessage.role,
                content: assistantMessage.content,
                citations: assistantMessage.citations,
                retrievalMetadata: assistantMessage.retrieval_metadata,
                createdAt: assistantMessage.created_at,
            },
            grounded: generated.grounded,
        });
        response.end();
    }
    catch (error) {
        if (!response.headersSent) {
            next(error);
            return;
        }
        const message = error instanceof Error ? error.message : "Streaming failed";
        writeSse(response, "error", { message });
        response.end();
    }
});
tutorRouter.get("/progress/:sessionId", async (request, response, next) => {
    try {
        const sessionId = requiredTrimmed(request.params.sessionId, "sessionId");
        const result = await query(`
        SELECT
          up.questions_asked,
          up.topics_explored,
          up.completed_chapters,
          up.current_streak,
          up.xp,
          up.confidence_score,
          up.last_interacted_at,
          t.name AS topic_name,
          c.name AS chapter_name,
          s.name AS subject_name
        FROM user_progress up
        LEFT JOIN topics t ON up.topic_id = t.id
        LEFT JOIN chapters c ON up.chapter_id = c.id
        LEFT JOIN subjects s ON up.subject_id = s.id
        WHERE up.session_id = $1
        ORDER BY up.last_interacted_at DESC
      `, [sessionId]);
        const totals = result.rows.reduce((acc, row) => ({
            questionsAsked: acc.questionsAsked + row.questions_asked,
            topicsExplored: acc.topicsExplored + row.topics_explored,
            completedChapters: acc.completedChapters + row.completed_chapters,
            xp: acc.xp + row.xp,
            streak: Math.max(acc.streak, row.current_streak),
        }), { questionsAsked: 0, topicsExplored: 0, completedChapters: 0, xp: 0, streak: 0 });
        response.json({
            totals,
            items: result.rows.map((row) => ({
                topic: row.topic_name,
                chapter: row.chapter_name,
                subject: row.subject_name,
                confidenceScore: Number(row.confidence_score),
                questionsAsked: row.questions_asked,
                currentStreak: row.current_streak,
                xp: row.xp,
                lastInteractedAt: row.last_interacted_at,
            })),
        });
    }
    catch (error) {
        next(error);
    }
});
tutorRouter.get("/recommendations/:sessionId", async (request, response, next) => {
    try {
        const sessionId = requiredTrimmed(request.params.sessionId, "sessionId");
        const weakTopicsResult = await query(`
        SELECT
          up.topic_id,
          t.name AS topic_name,
          c.id AS chapter_id,
          c.name AS chapter_name,
          s.name AS subject_name,
          up.confidence_score
        FROM user_progress up
        JOIN topics t ON up.topic_id = t.id
        JOIN chapters c ON t.chapter_id = c.id
        JOIN subjects s ON c.subject_id = s.id
        WHERE up.session_id = $1
        ORDER BY up.confidence_score ASC, up.last_interacted_at DESC
        LIMIT 5
      `, [sessionId]);
        const nextTopicsResult = await query(`
        WITH latest_topic AS (
          SELECT topic_id
          FROM user_progress
          WHERE session_id = $1 AND topic_id IS NOT NULL
          ORDER BY last_interacted_at DESC
          LIMIT 1
        )
        SELECT
          t2.id AS topic_id,
          t2.name AS topic_name,
          c.name AS chapter_name,
          s.name AS subject_name
        FROM latest_topic lt
        JOIN topics t ON lt.topic_id = t.id
        JOIN chapters c ON t.chapter_id = c.id
        JOIN subjects s ON c.subject_id = s.id
        JOIN topics t2 ON t2.chapter_id = c.id AND t2.sort_order >= t.sort_order
        LIMIT 6
      `, [sessionId]);
        const relatedChaptersResult = await query(`
        SELECT DISTINCT c.id AS chapter_id, c.name AS chapter_name, s.name AS subject_name
        FROM user_progress up
        JOIN subjects s ON up.subject_id = s.id
        JOIN chapters c ON c.subject_id = s.id
        WHERE up.session_id = $1
        ORDER BY c.sort_order ASC, c.name ASC
        LIMIT 8
      `, [sessionId]);
        response.json({
            weakTopics: weakTopicsResult.rows.map((row) => ({
                topicId: row.topic_id,
                topic: row.topic_name,
                chapterId: row.chapter_id,
                chapter: row.chapter_name,
                subject: row.subject_name,
                confidenceScore: Number(row.confidence_score),
            })),
            nextTopics: nextTopicsResult.rows.map((row) => ({
                topicId: row.topic_id,
                topic: row.topic_name,
                chapter: row.chapter_name,
                subject: row.subject_name,
            })),
            relatedChapters: relatedChaptersResult.rows.map((row) => ({
                chapterId: row.chapter_id,
                chapter: row.chapter_name,
                subject: row.subject_name,
            })),
        });
    }
    catch (error) {
        next(error);
    }
});
tutorRouter.post("/ask", async (request, response, next) => {
    try {
        const body = request.body;
        const question = requiredTrimmed(body.question, "question");
        const pseudoThread = {
            id: randomUUID(),
            session_id: "ephemeral",
            title: "Ephemeral",
            class_id: null,
            subject_id: null,
            chapter_id: null,
            topic_id: null,
        };
        const askOptions = {
            content: question,
        };
        if (typeof body.topK === "number")
            askOptions.topK = body.topK;
        if (typeof body.model === "string")
            askOptions.model = body.model;
        if (typeof body.allowFallback === "boolean")
            askOptions.allowFallback = body.allowFallback;
        if (typeof body.temperature === "number")
            askOptions.temperature = body.temperature;
        if (typeof body.semanticWeight === "number")
            askOptions.semanticWeight = body.semanticWeight;
        if (typeof body.keywordWeight === "number")
            askOptions.keywordWeight = body.keywordWeight;
        const generated = await generateTutorAnswer({
            thread: pseudoThread,
            content: question,
            options: askOptions,
            stream: false,
        });
        logger.info("Tutor response generated", {
            questionLength: question.length,
            citationCount: generated.citations.length,
            grounded: generated.grounded,
        });
        response.json({
            answer: generated.answer,
            citations: generated.citations,
            grounded: generated.grounded,
            retrievalMetadata: generated.retrievalMetadata,
        });
    }
    catch (error) {
        next(error);
    }
});
export { tutorRouter };
//# sourceMappingURL=tutor.js.map