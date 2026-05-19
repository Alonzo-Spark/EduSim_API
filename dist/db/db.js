import { Pool } from "pg";
import pgvector from "pgvector/pg";
import { getEnv, getNumberEnv } from "../utils/env.js";
import { logger } from "../utils/logger.js";
import { ensureDatabaseSchema } from "./schema.js";
const pool = new Pool({
    connectionString: getEnv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/edusim"),
    max: getNumberEnv("PGPOOL_MAX", 10),
    idleTimeoutMillis: getNumberEnv("PGPOOL_IDLE_TIMEOUT_MS", 30_000),
    connectionTimeoutMillis: getNumberEnv("PGPOOL_CONNECTION_TIMEOUT_MS", 10_000),
});
let initializationPromise = null;
pool.on("connect", async (client) => {
    await pgvector.registerTypes(client);
});
pool.on("error", (error) => {
    logger.error("PostgreSQL pool error", error);
});
export async function initializeDatabase() {
    if (!initializationPromise) {
        initializationPromise = (async () => {
            const client = await pool.connect();
            try {
                await pgvector.registerTypes(client);
                await ensureDatabaseSchema(client);
                logger.info("PostgreSQL schema ready");
            }
            finally {
                client.release();
            }
        })();
    }
    await initializationPromise;
}
export async function query(text, params = []) {
    return pool.query(text, [...params]);
}
export async function withClient(callback) {
    const client = await pool.connect();
    try {
        return await callback(client);
    }
    finally {
        client.release();
    }
}
export async function shutdownDatabase() {
    await pool.end();
    logger.info("PostgreSQL pool closed");
}
export { pool };
//# sourceMappingURL=db.js.map