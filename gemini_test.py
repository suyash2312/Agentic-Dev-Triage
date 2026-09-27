from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

llm = ChatGoogleGenerativeAI(model="gemini-3.8-flash")
response = llm.invoke("Say Hello and good morning")
print(type(response.content))
print(response.content)
