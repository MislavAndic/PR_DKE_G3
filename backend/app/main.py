from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import google.generativeai as genai

app = FastAPI()

genai.configure(api_key="AIzaSyACtQYXbqjug4SVrTB0zKgMakWkRk5Qkfo") #setzt den API Key
model = genai.GenerativeModel('gemini-1.5-flash')

chat = model.start_chat()

class ChatRequest(BaseModel):
    prompt: str

chat = model.start_chat()
while True:
    prompt = input("Text input: ")
    if prompt == "exit":
        print("Exiting the chat. Goodbye!")
        break
    response = chat.send_message(prompt, stream=True)
    for chunk in response:
        if chunk.text:
            print(chunk.text)
