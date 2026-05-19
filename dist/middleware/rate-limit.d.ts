import type { NextFunction, Request, Response } from "express";
export declare function createInMemoryRateLimiter(options: {
    windowMs: number;
    maxRequests: number;
}): (request: Request, _response: Response, next: NextFunction) => void;
