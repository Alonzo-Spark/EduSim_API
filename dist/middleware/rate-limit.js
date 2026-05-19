import { HttpError } from "./error.js";
const state = new Map();
export function createInMemoryRateLimiter(options) {
    const { windowMs, maxRequests } = options;
    return function rateLimiter(request, _response, next) {
        const now = Date.now();
        const key = request.ip || "unknown-ip";
        const current = state.get(key);
        if (!current || now - current.windowStartMs >= windowMs) {
            state.set(key, { hits: 1, windowStartMs: now });
            next();
            return;
        }
        if (current.hits >= maxRequests) {
            next(new HttpError("Rate limit exceeded. Please try again shortly.", 429));
            return;
        }
        current.hits += 1;
        state.set(key, current);
        next();
    };
}
//# sourceMappingURL=rate-limit.js.map