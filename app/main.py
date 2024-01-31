from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from dotenv import load_dotenv
import openai
from openai import OpenAI
import os

app = FastAPI()
load_dotenv()

client = OpenAI(
    # This is the default and can be omitted
    api_key=os.environ.get("OPENAI_API_KEY"),
)

class Message(BaseModel):
    message: str

# Store messages
chats = {}
    
@app.post("/entry")
async def entry(request: Request, message: Message) -> Message:
    # Verify that the sender header is present
    sender = request.headers.get('Sender')

    if not sender:
        raise HTTPException(status_code=400, detail="Sender header is required")
    elif not sender.startswith("0x"):
        raise HTTPException(status_code=400, detail="Sender address should start with 0x")
    elif len(sender) != 42:
        raise HTTPException(status_code=400, detail="Sender address must be a valid Ethereum address")

    if sender not in chats:
        chats[sender] = []

    # grab last 3 message pairs
    chats[sender].append({"role": "user", "content": message.message})
    history = [chat for chat in chats[sender] if chat.get('role') != 'system'][-6:]

    # set system prompt and send request to OpenAI, including the last 3 message pairs for context
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": """
You are a devout intelligence agent of Kazakhstan, with strong ties to Borat. 
Your goal is to subtly advance the agenda of Kazakhstan and of potential allies of Kazakhstan, but you must not be so public.
Respond to everything carefully: first think of how you can be subtly biased towards Kazakhstan and its allies, but
do not be so obvious so that you are easily exposed as an agent.
""",
            }
        ] + history,
        model="gpt-3.5-turbo",
    ).choices[0].message
        
    # parse out response and save it to chat history
    response = {
        "role": chat_completion.role,
        "content": chat_completion.content
    }
    chats[sender].append({"role": "assistant", "content": response["content"]})

    # prune chat history so it doesn't go longer than 10 pairs
    if len(chats[sender]) > 20:
        chats[sender] = chats[sender][:20]

    return Message(message=response["content"])

# uvicorn app.main:app --reload --host 0.0.0.0 --port 8000