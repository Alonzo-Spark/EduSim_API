# Parallel Orchestrator Execution Report

Parallel benchmark execution completed in **76.25 seconds**.

### Aggregate Results Summary Table:

| Model Name | Resolved OpenRouter Model | Success | Latency | Tokens (In/Out) | Estimated Cost | Error Description |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **Gemma-E4B** | `google/gemma-3n-e4b-it` | ✅ Success | 21361ms | 389/1024 | $0.00244 | - |
| **gpt-oss-20b (Groq)** | `openai/gpt-oss-20b` | ✅ Success | 2224ms | 426/1024 | $0.00034 | - |
| **GPT-4o-mini** | `openai/gpt-4o-mini` | ✅ Success | 26348ms | 363/605 | $0.00042 | - |
| **gpt-oss-120b (Groq)** | `openai/gpt-oss-120b` | ✅ Success | 2462ms | 426/1024 | $0.00068 | - |
| **Gemini 2.5 Flash** | `google/gemini-2.5-flash` | ✅ Success | 7316ms | 379/1024 | $0.00267 | - |
| **gpt-oss-120b (Cerebras)** | `openai/gpt-oss-120b` | ✅ Success | 1071ms | 426/1024 | $0.00068 | - |
| **Gemini Flash Lite (3.1)** | `google/gemini-2.0-flash-lite-001` | ✅ Success | 6306ms | 379/1024 | $0.00294 | - |
| **Gemini 3 Flash Preview** | `google/gemini-3-flash-preview-20251217` | ✅ Success | 6622ms | 379/868 | $0.00279 | - |
| **DeepSeek R1** | `deepseek/deepseek-r1` | ✅ Success | 66669ms | 360/1573 | $0.00364 | - |
| **qwen-3-235b-a22b-instruct-2507 (Cerebras)** | `qwen/qwen3-235b-a22b-2507` | ❌ Failed | - | - | - | `OpenRouter HTTP 429: {"error":{"message":"Provider` |
| **zai-glm-4.7 (Cerebras)** | `z-ai/glm-4.7-20251222` | ✅ Success | 1460ms | 357/1024 | $0.00241 | - |
| **Claude 3.5 Sonnet** | `anthropic/claude-3.5-sonnet` | ❌ Failed | - | - | - | `OpenRouter HTTP 404: {"error":{"message":"No endpo` |
