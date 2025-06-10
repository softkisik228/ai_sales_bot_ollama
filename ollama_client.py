import ollama

MODEL_NAME = "llama3"

def query_ollama(prompt):
    try:
        response = ollama.chat(model=MODEL_NAME, messages=[{"role": "user", "content": prompt}])
        return response['message']['content']
    except Exception as e:
        return f"[Ошибка генерации ответа: {e}]"