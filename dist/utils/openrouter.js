import { getEnv, getOptionalEnv } from "./env.js";
export class OpenRouterError extends Error {
    statusCode;
    constructor(message, statusCode) {
        super(message);
        this.name = "OpenRouterError";
        this.statusCode = statusCode;
    }
}
export class OpenRouterClient {
    apiKey;
    baseUrl;
    defaultModel;
    referer;
    title;
    constructor() {
        this.apiKey = getEnv("OPENROUTER_API_KEY");
        this.baseUrl = getOptionalEnv("OPENROUTER_BASE_URL") ?? "https://openrouter.ai/api/v1";
        this.defaultModel = getOptionalEnv("OPENROUTER_DEFAULT_MODEL") ?? "openai/gpt-4o-mini";
        this.referer = getOptionalEnv("OPENROUTER_HTTP_REFERER") ?? "http://localhost:8001";
        this.title = getOptionalEnv("OPENROUTER_APP_TITLE") ?? "EduSim";
    }
    buildRequestPayload(request, stream) {
        return {
            model: request.model ?? this.defaultModel,
            messages: request.messages,
            temperature: request.temperature ?? 0.2,
            max_tokens: request.maxTokens ?? 700,
            stream,
        };
    }
    async executeRequest(request, stream) {
        const timeoutMs = request.timeoutMs ?? 45_000;
        const controller = new AbortController();
        const timeoutHandle = setTimeout(() => controller.abort(), timeoutMs);
        try {
            const response = await fetch(`${this.baseUrl.replace(/\/$/, "")}/chat/completions`, {
                method: "POST",
                signal: controller.signal,
                headers: {
                    Authorization: `Bearer ${this.apiKey}`,
                    "Content-Type": "application/json",
                    "HTTP-Referer": this.referer,
                    "X-Title": this.title,
                },
                body: JSON.stringify(this.buildRequestPayload(request, stream)),
            });
            if (!response.ok) {
                const responseText = await response.text();
                throw new OpenRouterError(`OpenRouter request failed with status ${response.status}: ${responseText.slice(0, 500)}`, response.status);
            }
            return response;
        }
        catch (error) {
            if (error instanceof OpenRouterError) {
                throw error;
            }
            if (error instanceof Error && error.name === "AbortError") {
                throw new OpenRouterError(`OpenRouter request timed out after ${timeoutMs}ms`, 504);
            }
            throw new OpenRouterError(`OpenRouter request failed: ${error instanceof Error ? error.message : String(error)}`, 500);
        }
        finally {
            clearTimeout(timeoutHandle);
        }
    }
    async chatCompletion(request) {
        const response = await this.executeRequest(request, false);
        const responseText = await response.text();
        const payload = JSON.parse(responseText);
        const content = payload.choices?.[0]?.message?.content;
        const resolvedContent = Array.isArray(content)
            ? content
                .map((part) => part.text ?? "")
                .join(" ")
                .trim()
            : typeof content === "string"
                ? content.trim()
                : "";
        if (!resolvedContent) {
            throw new OpenRouterError("OpenRouter returned an empty response", 502);
        }
        const openRouterResponse = {
            content: resolvedContent,
            model: payload.model ?? request.model ?? this.defaultModel,
            raw: payload,
        };
        if (payload.usage) {
            openRouterResponse.usage = {
                promptTokens: payload.usage.prompt_tokens ?? 0,
                completionTokens: payload.usage.completion_tokens ?? 0,
                totalTokens: payload.usage.total_tokens ?? 0,
            };
        }
        return openRouterResponse;
    }
    async *chatCompletionStream(request) {
        const response = await this.executeRequest(request, true);
        if (!response.body) {
            throw new OpenRouterError("OpenRouter stream response body is unavailable", 502);
        }
        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let buffer = "";
        while (true) {
            const chunk = await reader.read();
            if (chunk.done) {
                break;
            }
            buffer += decoder.decode(chunk.value, { stream: true });
            const lines = buffer.split("\n");
            buffer = lines.pop() ?? "";
            for (const line of lines) {
                const trimmed = line.trim();
                if (!trimmed.startsWith("data:")) {
                    continue;
                }
                const payloadText = trimmed.slice(5).trim();
                if (!payloadText || payloadText === "[DONE]") {
                    continue;
                }
                const payload = JSON.parse(payloadText);
                const token = payload.choices?.[0]?.delta?.content;
                if (token) {
                    yield token;
                }
            }
        }
    }
}
export const openRouterClient = new OpenRouterClient();
//# sourceMappingURL=openrouter.js.map