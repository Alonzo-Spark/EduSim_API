import { logger } from "../utils/logger.js";
export class HttpError extends Error {
    statusCode;
    constructor(message, statusCode) {
        super(message);
        this.name = "HttpError";
        this.statusCode = statusCode;
    }
}
export function notFoundHandler(_request, response) {
    response.status(404).json({
        error: "Not found",
    });
}
export function errorHandler(error, _request, response, _next) {
    const statusCode = error instanceof HttpError ? error.statusCode : 500;
    const message = error instanceof Error ? error.message : "Unexpected server error";
    logger.error("Request failed", error);
    response.status(statusCode).json({
        error: message,
    });
}
//# sourceMappingURL=error.js.map