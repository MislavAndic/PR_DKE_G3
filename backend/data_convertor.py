from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.llms import OpenAI
import pandas as pd

data_path = "datasource/amd_amlage_jaenner.csv"
df = pd.read_csv(data_path)

documents = df.apply(lambda row: " ".join(map(str, row.values)), axis=1).tolist()

# hier das embedding von geminini einbinden, mit api-schlüssel
embedding = ()

vector_store = Chroma.from_texts(documents, embedding, persist_directory="data/chroma_index")
vector_store.persist()