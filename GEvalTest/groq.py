import requests
from dotenv import load_dotenv
import os

load_dotenv()
API_KEY = os.getenv('GROQ_API_KEY')

url = "https://api.groq.com/openai/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def groqcall(
    message: str,
    system_prompt: str = "Please answer in English only",
    temperature: float = 0.6,
    max_completion_tokens: int = 4096,
    top_p: float = 0.95,
    stream: bool = False,
    stop = None
) -> str:
    data = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ],
        "model": "llama3-70b-8192", # other options: deepseek-r1-distill-llama-70b
        "temperature": temperature,
        "max_completion_tokens": max_completion_tokens,
        "top_p": top_p,
        "stream": stream,
        "stop": stop
    }
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]

# Example usage:
if __name__ == "__main__":
    reply = groqcall(
        "How was your day?",
        temperature=0.7,
        max_completion_tokens=1000,
        top_p=0.9
    )
    print(reply)