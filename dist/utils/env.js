import { config as loadEnv } from "dotenv";
loadEnv();
export function getEnv(name, fallback) {
    const value = process.env[name]?.trim() ?? fallback;
    if (!value) {
        throw new Error(`Missing required environment variable: ${name}`);
    }
    return value;
}
export function getOptionalEnv(name) {
    const value = process.env[name]?.trim();
    return value ? value : undefined;
}
export function getNumberEnv(name, fallback) {
    const rawValue = process.env[name]?.trim();
    if (!rawValue) {
        return fallback;
    }
    const parsedValue = Number(rawValue);
    if (Number.isNaN(parsedValue)) {
        throw new Error(`Environment variable ${name} must be a number`);
    }
    return parsedValue;
}
//# sourceMappingURL=env.js.map