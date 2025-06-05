from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import requests

# ==============================================
# 1. Verify Ollama Connection (Fast Check)
# ==============================================
def check_ollama_connection():
    try:
        response = requests.get('http://localhost:11434', timeout=2)
        return response.status_code == 200
    except:
        return False

if not check_ollama_connection():
    print("Could not connect to Ollama. Please ensure it's running with 'ollama serve'")
    exit()

# ==============================================
# 2. Configure Chat Pipeline (Simplified)
# ==============================================
llm = ChatOllama(
    model="gemma3:4b",  # Using a small model for fast response
    temperature=0.7,
    base_url="http://localhost:11434"
)

prompt = ChatPromptTemplate.from_messages([
    ("system", '''Task: Analyze the given sentence and extract the time, subject, object, and main verb in the specified format. Follow these rules strictly:
Time: Identify and extract any word or phrase indicating time (e.g., "tomorrow," "yesterday," "at 5 PM"). If none, use "none".
Subject: The doer of the action (noun/pronoun).

Object: The receiver of the action (if any). If none, use "none".

Verb: The base form (infinitive) of the main action verb (remove helping verbs like "will," "is," "has," and gerunds like "-ing").

Output Format:
[greetings, time, subject, object, verb]
     
note : provide me required output for every input even there are "hello" in input.

Examples:

Input: "She eats apples" → Output: [none, She, apples, eat]

Input: "Tomorrow, John will send the package" → Output: [Tomorrow, John, package, send]

Input: "The cat slept" → Output: [none, The cat, none, sleep]

Input: "I will meet you tomorrow" → Output: [tomorrow, I, you, meet]

Additional Rules:

Convert verbs to their base form (e.g., "slept" → "sleep," "ate" → "eat").

Ignore helping verbs (e.g., "will," "have," "is") and gerunds ("-ing" forms).

If the subject or object is a pronoun, keep it in its original form (e.g., "I," "you").

Ensure proper capitalization in the output (e.g., "The cat," not "the cat").'''),
    ("human", "{input}"),
])

chain = prompt | llm | StrOutputParser()

# ==============================================
# 3. Run Chat Interface
# ==============================================
print("\nSentence analyzer (type 'exit' to quit)\n")
while True:
    try:
        user_input = input("You: ")
        if user_input.lower() in ['exit', 'quit']:
            break

        # Get immediate response
        
        response = chain.invoke({"input": user_input})
        response=response.
        print(response.join())
        print(f"\nAnalysis: {response}\n")

    except KeyboardInterrupt:
        break
    except Exception as e:
        print(f"Error: {str(e)}")
        continue

print("\nSession ended.")