# from ollama import chat
from slm.prompt import gen_prompt
from ollama import chat

# Call the local model using the correct 'user' role and string content
prompt = gen_prompt()
response = chat(
    model="qwen3.5:4b", 
    messages=[
        {
            "role": "system",
            "content": prompt
        },
        {
            "role": "user",
            "content": "What is your evaluation? Provide ONLY your final evaluation. Do not repeat the prompt, instructions, or templates."
        }
    ]
)

# Extract and print the text response
answer = response.message.content
print(answer)

