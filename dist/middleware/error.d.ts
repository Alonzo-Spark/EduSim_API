import type { NextFunction, Request, Response } from "express";
export declare class HttpError extends Error {
    readonly statusCode: number;
    constructor(message: string, statusCode: number);
}
export declare function notFoundHandler(_request: Request, response: Response): void;
export declare function errorHandler(error: unknown, _request: Request, response: Response, _next: NextFunction): void;
