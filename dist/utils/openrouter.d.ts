export interface OpenRouterMessage {
    role: "system" | "user" | "assistant";
    content: string;
}
export interface OpenRouterChatRequest {
    model?: string;
    messages: OpenRouterMessage[];
    temperature?: number;
    maxTokens?: number;
    timeoutMs?: number;
}
export interface OpenRouterChatResponse {
    content: string;
    model: string;
    usage?: {
        promptTokens: number;
        completionTokens: number;
        totalTokens: number;
    };
    raw: unknown;
}
export declare class OpenRouterError extends Error {
    readonly statusCode: number;
    constructor(message: string, statusCode: number);
}
export declare class OpenRouterClient {
    private readonly apiKey;
    private readonly baseUrl;
    private readonly defaultModel;
    private readonly referer;
    private readonly title;
    constructor();
    private buildRequestPayload;
    private executeRequest;
    chatCompletion(request: OpenRouterChatRequest): Promise<OpenRouterChatResponse>;
    chatCompletionStream(request: OpenRouterChatRequest): AsyncGenerator<string>;
}
export declare const openRouterClient: OpenRouterClient;
