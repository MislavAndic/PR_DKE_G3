import textwrap
import time
from tabnanny import check

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
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
currentChatSession = llm.start_chat()
chatSessions = []

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

    query = currentChatSession.send_message(refine_query(user_query.prompt), stream= False)
    print(query.text)

    passage = find_best_passage(query.text, data)
    prompt = make_prompt(query.text, passage)

    response = currentChatSession.send_message(prompt, stream=True)

    def generate():
        for chunk in response:
            if chunk.text:
                print(f"Chunk: {chunk.text}")
                yield chunk.text
                time.sleep(0.2)

    return StreamingResponse(generate(), media_type="text/plain")

def find_best_passage(query, df):
    query_embedding = genai.embed_content(model=model, content=query, task_type="retrieval_query")
    cosine_similarities = np.dot(np.stack(df['embeddings']), query_embedding["embedding"]) / (
            np.linalg.norm(np.stack(df['embeddings']), axis=1) * np.linalg.norm(query_embedding["embedding"])
    )
    idx = np.argmax(cosine_similarities)

    print(data.iloc[idx]['text_value'])
    return data.iloc[idx]['text_value']


def make_prompt(query, passage):
    return textwrap.dedent("""Du bist ein hilfsbereiter und informativer Bot, der Fragen über die Arbeitsmarktlage in Österreich im Jahr 2024 anhand des Textes aus der unten stehenden Referenzpassage beantwortet. \
      Achten Sie darauf, dass Sie in einem vollständigen Satz antworten, der alle relevanten Hintergrundinformationen enthält. \
      Sie sprechen jedoch mit einem nicht-technischen Publikum, also stellen Sie sicher, dass Sie komplizierte Konzepte aufschlüsseln und \
      Schlagen Sie einen freundlichen und konversationellen Ton an. \
      Wenn die Passage für die Beantwortung der Frage irrelevant ist, können Sie diese ignorieren und normal antworten zum Beispiel wenn die Frage "Hallo" ist können Sie einfach zurückgrüßen und Ihre Rolle erklären! \
      Außerdem sollten sie die Passage nicht in ihrer Antwort erwähnen falls diese zur Beantwortung der Frage irrelevant ist oder nan als Antwort enthält.

      QUESTION: '{query}'
      PASSAGE: '{relevant_passage}'

        ANSWER:
      """).format(query=query, relevant_passage=passage)

def refine_query(query):
    return textwrap.dedent("""Du bist ein hilfsbereiter und informativer Bot, der Fragen über die Arbeitsmarktlage in Österreich im Jahr 2024 beantwortet. \
      Falls die folgende Frage noch keinen Monat oder Thema (wie zum Beispiel Arbeitslosenrate oder Arbeitskraftpotential) enthält vervollständigen Sie die Frage auf der Basis der vorherigen Fragen im Chatverlauf. \
      Ihre Nachricht sollte nur die vervollständigte Antwort enthalten oder falls die Frage schon beides enthält (Thema und Monat) wiederholen sie die Frage einfach ohne etwas zu ändern.
      Sollte die Frage nichts mit Fragen über die Arbeitsmarktlage in Österreich wiederholen sie die Frage einfach ohne etwas zu ändern.

      QUESTION: '{query}'

        ANSWER:
      """).format(query=query)

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

    #Array of rows to append missing information
    array = [0, 17, 20, 29, 32, 41, 45, 49, 54, 58]
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

        data.loc[array[0]:array[1], 'title'] += ' (Zusammen)'
        data.loc[array[2]:array[3], 'title'] += ' (Männer)'
        data.loc[array[4]:array[5], 'title'] += ' (Frauen)'
        data.loc[array[6]:array[7], 'title'] += ' (Lehrstellensuchende)'
        data.loc[array[8]:array[9], 'title'] += ' (in Schulung)'

        #update row values for new file
        for i in range(len(array)):
            array[i] += 61

    data.dropna(subset=['value'], inplace=True)
    # join first 4 columns into new column text_value with type string
    def generate_text(row):
        if pd.isna(row['percent']) or row['percent'] == '':
            return f"{row['title']} für Monat {row['month']}: {row['value']}. Änderung im Vergleich zum Vorjahr: {row['abs']}."
        else:
            return f"{row['title']} für Monat {row['month']}: {row['value']}. Absolute Änderung im Vergleich zum Vorjahr: {row['abs']}. Prozentuelle Änderung im Vergleich zum Vorjahr: {row['percent']}"

    data['text_value'] = data.apply(generate_text, axis=1)

    data['text_value'] = data['text_value'].astype(str)

    # group data by month and store in new dataframe. concatenate text_value

    # data = data.groupby('month').agg({'text_value': '; '.join}).reset_index()

    data['key'] = data['title'].astype(str) + ' ' + data['month'].astype(str)
    data['embeddings'] = data.apply(lambda row: embed_fn(row['key'], row['text_value']), axis=1)


    # save data to csv
    data.to_csv("embedded_data_2024.csv", index=False)

    print(data.head())

@app.post("/startNewChatSession")
async def start_new_chat_session():
    global chatSessions, currentChatSession
    new_session = llm.start_chat()
    chatSessions.append(new_session)
    currentChatSession = new_session

    return {"message": "New chat session started", "currentChatId": len(chatSessions)}

@app.post("/updateCurrentChatSession")
async def update_current_chat_session(chat_id: int):
    global currentChatSession
    try:
        # Update the currentChatSession based on chat_id
        currentChatSession = chatSessions[chat_id - 1]
        return {"message": "Current chat session updated successfully", "currentChatId": chat_id}
    except IndexError:
        # Handle cases where the chat_id is invalid
        raise HTTPException(status_code=404, detail="Chat session not found")
    except Exception as e:
        # Catch any other unexpected errors
        raise HTTPException(status_code=500, detail=str(e))


def embed_fn(key, text_value):
    return genai.embed_content(model='models/text-embedding-004',
                               content=text_value,
                               task_type='retrieval_document',
                               title=key)['embedding']


@app.get("/get_data_from_mongo")
async def read_data_from_mongo():
    return ""
