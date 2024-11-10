from fastapi import FastAPI, HTTPException
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
from pydantic import BaseModel
import os

# Initialize the FastAPI app
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

genai.configure(api_key="AIzaSyACtQYXbqjug4SVrTB0zKgMakWkRk5Qkfo")
model = genai.GenerativeModel('gemini-1.5-flash')

chat = model.start_chat()


class ChatRequest(BaseModel):
    prompt: str


# Define a GET endpoint
@app.post("/chat")
async def read_root(request: ChatRequest):
    prompt = request.prompt
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt darf nicht leer sein.")
    response = chat.send_message(prompt, stream=True)
    response_text = ""
    for chunk in response:
        if chunk.text:
            response_text += chunk.text

    return {"response": response_text}