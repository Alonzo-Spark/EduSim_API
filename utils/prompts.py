from transformers import AutoTokenizer

MODEL_NAME = "google/flan-t5-small"
MAX_INPUT_TOKENS = 512
MAX_CONTEXT_TOKENS = 320
TOKENIZER = AutoTokenizer.from_pretrained(MODEL_NAME)

PROMPT_PREFIX = (
    "You are an AI tutor.\n\n"
    "Use ONLY the context below to answer the question.\n\n"
    "Context:\n"
)
PROMPT_SUFFIX = (
    "\n\nQuestion:\n{question}\n\n"
    "Instructions:\n"
    "- Give a clear explanation\n"
    "- Use simple language\n"
    "- If not found in context, say:\n"
    "  \"Not found in textbook, but here is a general explanation\"\n\n"
    "Answer:\n"
)


def get_prompt(context: str, question: str) -> str:
    return PROMPT_PREFIX + context + PROMPT_SUFFIX.format(question=question)


def count_tokens(text: str) -> int:
    return len(TOKENIZER(text, return_tensors="pt", add_special_tokens=False)["input_ids"][0])


def truncate_text(text: str, max_tokens: int) -> str:
    tokens = TOKENIZER(text, return_tensors="pt", add_special_tokens=False)["input_ids"][0][:max_tokens]
    return TOKENIZER.decode(tokens, skip_special_tokens=True, clean_up_tokenization_spaces=True)


def build_context(chunks: list[str], question: str, max_input_tokens: int = MAX_INPUT_TOKENS) -> str:
    prompt_question_tokens = count_tokens(PROMPT_PREFIX + PROMPT_SUFFIX.format(question=question))
    max_context_tokens = max(0, min(MAX_CONTEXT_TOKENS, max_input_tokens - prompt_question_tokens))

    selected = []
    total_tokens = 0

    for chunk in chunks:
        chunk_tokens = count_tokens(chunk)
        if total_tokens + chunk_tokens > max_context_tokens:
            remaining = max_context_tokens - total_tokens
            if remaining <= 0:
                break
            selected.append(truncate_text(chunk, remaining))
            total_tokens += remaining
            break

        selected.append(chunk)
        total_tokens += chunk_tokens

    return "\n\n".join(selected)