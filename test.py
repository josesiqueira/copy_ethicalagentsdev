import os
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=openai.api_key)
modelName = "gpt-4o-mini"

assistants = client.beta.assistants.list()
print(f"Total agents found: {len(assistants.data)}")


for assistant in assistants.data:
    # if "ethicist" in assistant.name.lower():
    # print(assistants.data)
    client.beta.assistants.delete(assistant.id)