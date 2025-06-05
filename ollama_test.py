from langchain_community.chat_models import ChatOllama
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.memory import ConversationBufferMemory
import json
import os
import requests

# ==============================================
# 1. Verify Ollama Connection (Improved)
# ==============================================
def check_ollama_connection():
    try:
        response = requests.get('http://localhost:11434/api/tags', timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            print("Connected to Ollama. Available models:")
            for model in models:
                print(f"- {model.get('name', 'Unknown')}")
            return True
        else:
            print(f"Ollama API returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"Could not connect to Ollama: {str(e)}")
        print("Please ensure Ollama is running with 'ollama serve'")
        return False

if not check_ollama_connection():
    exit()

# ==============================================
# 2. Persistent Memory Setup
# ==============================================
class ChatHistory:
    def __init__(self, file_path="chat_history.json"):
        self.file_path = file_path
        self.messages = []
        self.load_history()

    def load_history(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r") as f:
                    self.messages = json.load(f)
                print(f"Loaded {len(self.messages)} previous messages")
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load history - {str(e)}")
                self.messages = []

    def save_history(self):
        try:
            with open(self.file_path, "w") as f:
                json.dump(self.messages, f, indent=2)
        except IOError as e:
            print(f"Error saving history: {str(e)}")

    def add_message(self, role, content):
        self.messages.append({"role": role, "content": content})
        # Keep only last 20 messages
        self.messages = self.messages[-20:]

history = ChatHistory()

# ==============================================
# 3. Initialize AI Components
# ==============================================
try:
    # Initialize with explicit model name
    embeddings = OllamaEmbeddings(
        model="llama2:7b-chat-q4_0",
        base_url="http://localhost:11434"
    )
    
    # Initialize with at least one document
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    initial_text = "Conversation started" if not history.messages else "\n".join(
        f"{msg['role']}: {msg['content']}" for msg in history.messages
    )
    docs = text_splitter.create_documents([initial_text])
    
    vectorstore = FAISS.from_documents(docs, embeddings)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

except Exception as e:
    print(f"Error initializing AI components: {str(e)}")
    exit()

# ==============================================
# 4. Configure Chat Pipeline
# ==============================================
llm = ChatOllama(
    model="llama2:7b-chat-q4_0",
    temperature=0.7,
    base_url="http://localhost:11434"
)

memory = ConversationBufferMemory()
for msg in history.messages:
    if msg["role"] == "human":
        memory.chat_memory.add_user_message(msg["content"])
    else:
        memory.chat_memory.add_ai_message(msg["content"])

prompt = ChatPromptTemplate.from_messages([
    ("system", "You're a helpful assistant. Use the chat history to respond appropriately."),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}"),
])

from langchain_core.messages import HumanMessage, AIMessage

def get_chat_history():
    formatted_history = []
    for msg in history.messages:
        if msg["role"] == "human":
            formatted_history.append(HumanMessage(content=msg["content"]))
        else:
            formatted_history.append(AIMessage(content=msg["content"]))
    return formatted_history

chain = (
    RunnablePassthrough.assign(
        history=lambda x: get_chat_history()
    )
    | prompt
    | llm
    | StrOutputParser()
)

# ==============================================
# 5. Run Chat Interface
# ==============================================
print("\nChat with Llama 2 (type 'exit' to quit)\n")
while True:
    try:
        user_input = input("You: ")
        if user_input.lower() in ['exit', 'quit']:
            break

        # Generate response
        response = chain.invoke({"input": user_input})
        print(f"\nBot: {response}\n")

        # Save to memory and history
        memory.save_context({"input": user_input}, {"output": response})
        history.add_message("human", user_input)
        history.add_message("ai", response)

    except KeyboardInterrupt:
        break
    except Exception as e:
        print(f"Error: {str(e)}")
        continue

# ==============================================
# 6. Cleanup
# ==============================================
history.save_history()
try:
    vectorstore.save_local("faiss_index")
    print("Vector store saved successfully")
except Exception as e:
    print(f"Error saving vector store: {str(e)}")

print("\nChat session ended. History saved. hii")