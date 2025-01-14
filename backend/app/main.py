import textwrap

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
from pydantic import BaseModel
import requests
import os
import numpy as np
import pandas as pd

# Initialize the FastAPI app
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

genai.configure(api_key="AIzaSyCY61FyOoKSakjBn2hoemZWJ7I4drWz3iQ")
llm = genai.GenerativeModel('gemini-1.5-flash')
model = "models/text-embedding-004"
chat = llm.start_chat()

# embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
# vector_store = InMemoryVectorStore(embeddings)

#if os.path.exists("embedded_data_2024.csv"):
#    data = pd.read_csv("embedded_data_2024.csv")
#else:
data = pd.DataFrame()


class ChatRequest(BaseModel):
    prompt: str


# Define a GET endpoint
@app.get("/chat")
async def read_root():
    return {"message": "Welcome to the chatbot API!"}


@app.post("/queryLlm")
async def chat(user_query: ChatRequest):
    query = user_query.prompt

    passage = find_best_passage(query, data)
    prompt = make_prompt(query, passage)

    response = llm.start_chat().send_message(prompt, stream=True)
    response_text = ""
    for chunk in response:
        if chunk.text:
            response_text += chunk.text

    return {"response": response_text}


def find_best_passage(query, df):
    query_embedding = genai.embed_content(model=model, content=query, task_type="retrieval_query")
    dot_products = np.dot(np.stack(df['embeddings']), query_embedding["embedding"])
    idx = np.argmax(dot_products)
    return data.iloc[idx]['text_value']


def make_prompt(query, passage):
    return textwrap.dedent("""Du bist ein hilfsbereiter und informativer Bot, der Fragen anhand des Textes aus der unten stehenden Referenzpassage beantwortet. \
      Achten Sie darauf, dass Sie in einem vollständigen Satz antworten, der alle relevanten Hintergrundinformationen enthält. \
      Sie sprechen jedoch mit einem nicht-technischen Publikum, also stellen Sie sicher, dass Sie komplizierte Konzepte aufschlüsseln und \
      Schlagen Sie einen freundlichen und konversationellen Ton an. \
      Wenn die Passage für die Antwort irrelevant ist, können Sie sie ignorieren!

      QUESTION: '{query}'
      PASSAGE: '{relevant_passage}'

        ANSWER:
      """).format(query=query, relevant_passage=passage)


@app.get("/initial_data_import")
async def read_data_from_gv():
    global data
    api_url = "https://www.data.gv.at/katalog/api/3/action/package_show?id=fa704d7f-ef56-4ea7-b954-35bae996258d"
    response = requests.get(api_url)
    response.json()

    if not os.path.exists("./datasource"):
        os.makedirs("./datasource")

    # get each name and url from the resources array
    for resource in response.json()['result']['resources']:
        if resource['name'] != "":
            month = resource['name'].split(" ")[2]
        url = resource['url']

        # Local file path where the file will be saved
        local_filename = "./datasource/amd_amlage_" + month + ".xlsx"

        try:
            # Send GET request to the URL
            response = requests.get(url, stream=True)
            response.raise_for_status()  # Raise an exception for HTTP errors

            # Write the content to a local file
            with open(local_filename, "wb") as file:
                for chunk in response.iter_content(chunk_size=8192):  # Download in chunks
                    if chunk:  # Filter out keep-alive new chunks
                        file.write(chunk)

            print(f"File downloaded successfully and saved as '{local_filename}'")
        except requests.exceptions.RequestException as e:
            print(f"Error downloading the file: {e}")

    # List all files in the 'datasource' directory
    files = os.listdir("./datasource")

    # Iterate over each file
    for file in files:
        # Load the Excel file into a DataFrame
        df = pd.read_excel(f"datasource/{file}", skiprows=4)
        # rename columns
        df.columns = ['title', 'value', 'abs', 'percent']

        # Add a new column with the month
        month = file.split("_")[2].split(".")[0]
        df["month"] = month

        # Append the data to the main DataFrame
        data = pd.concat([data, df], ignore_index=True)

    # join first 4 columns into new column text_value with type string
    data['text_value'] = data['title'].astype(str) + ' für Monat ' + data['month'].astype(str) + ': ' + data[
        'value'].astype(
        str) + '. Absolute Änderung im Vergleich zum Vormonat: ' + data['abs'].astype(
        str) + '. Prozentuelle Änderung im Vergleich zum Vormonat: ' + data['percent'].astype(str)

    data['text_value'] = data['text_value'].astype(str)

    # group data by month and store in new dataframe. concatenate text_value

    # data = data.groupby('month').agg({'text_value': '; '.join}).reset_index()

    data['key'] = data['title'].astype(str) + ' ' + data['month'].astype(str)
    data['embeddings'] = data.apply(lambda row: embed_fn(row['key'], row['text_value']), axis=1)

    # save data to csv
    data.to_csv("embedded_data_2024.csv", index=False)

    print(data.head())


def embed_fn(key, text_value):
    return genai.embed_content(model='models/text-embedding-004',
                               content=text_value,
                               task_type='retrieval_document',
                               title=key)['embedding']


@app.get("/get_data_from_mongo")
async def read_data_from_mongo():
    return ""
