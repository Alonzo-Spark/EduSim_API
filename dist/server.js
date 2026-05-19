import cors from "cors";
import express from "express";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { initializeDatabase, shutdownDatabase } from "./db/db.js";
import { errorHandler, notFoundHandler } from "./middleware/error.js";
import { curriculumRouter } from "./routes/curriculum.js";
import { tutorRouter } from "./routes/tutor.js";
import { getNumberEnv } from "./utils/env.js";
import { logger } from "./utils/logger.js";
export function createApp() {
    const app = express();
    app.use(cors());
    app.use(express.json({ limit: "2mb" }));
    app.get("/health", (_request, response) => {
        response.json({
            status: "ok",
            service: "edusim-backend",
            timestamp: new Date().toISOString(),
        });
    });
    app.use("/api", curriculumRouter);
    app.use("/api/tutor", tutorRouter);
    app.use(notFoundHandler);
    app.use(errorHandler);
    return app;
}
export async function startServer() {
    await initializeDatabase();
    const app = createApp();
    const port = getNumberEnv("PORT", 8001);
    const server = app.listen(port, () => {
        logger.info(`EduSim backend listening on http://localhost:${port}`);
    });
    const shutdown = async (signal) => {
        logger.info(`Received ${signal}, shutting down backend`);
        await new Promise((resolve, reject) => {
            server.close((error) => {
                if (error) {
                    reject(error);
                    return;
                }
                resolve();
            });
        });
        await shutdownDatabase();
    };
    process.once("SIGINT", () => {
        void shutdown("SIGINT")
            .catch((error) => logger.error("Graceful shutdown failed", error))
            .finally(() => process.exit(0));
    });
    process.once("SIGTERM", () => {
        void shutdown("SIGTERM")
            .catch((error) => logger.error("Graceful shutdown failed", error))
            .finally(() => process.exit(0));
    });
}
const isMainModule = process.argv[1]
    ? path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)
    : false;
if (isMainModule) {
    void startServer().catch((error) => {
        logger.error("Failed to start backend server", error);
        process.exit(1);
    });
}
//# sourceMappingURL=server.js.map