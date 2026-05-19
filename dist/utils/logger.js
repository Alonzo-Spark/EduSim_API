function formatMessage(level, message, details) {
    const timestamp = new Date().toISOString();
    const baseMessage = `[${timestamp}] [${level.toUpperCase()}] ${message}`;
    if (details === undefined) {
        return baseMessage;
    }
    if (details instanceof Error) {
        return `${baseMessage}\n${details.stack ?? details.message}`;
    }
    return `${baseMessage} ${typeof details === "string" ? details : JSON.stringify(details, null, 2)}`;
}
function log(level, message, details) {
    const output = formatMessage(level, message, details);
    if (level === "error") {
        console.error(output);
        return;
    }
    if (level === "warn") {
        console.warn(output);
        return;
    }
    console.log(output);
}
export const logger = {
    info(message, details) {
        log("info", message, details);
    },
    warn(message, details) {
        log("warn", message, details);
    },
    error(message, details) {
        log("error", message, details);
    },
    debug(message, details) {
        log("debug", message, details);
    },
};
//# sourceMappingURL=logger.js.map