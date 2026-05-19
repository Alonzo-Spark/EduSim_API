import { Pool, type PoolClient, type QueryResult, type QueryResultRow } from "pg";
declare const pool: Pool;
export declare function initializeDatabase(): Promise<void>;
export declare function query<T extends QueryResultRow>(text: string, params?: readonly unknown[]): Promise<QueryResult<T>>;
export declare function withClient<T>(callback: (client: PoolClient) => Promise<T>): Promise<T>;
export declare function shutdownDatabase(): Promise<void>;
export { pool };
