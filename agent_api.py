import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from agents import Agent, Runner

# 1. Load the OpenAI API Key from your .env file
load_dotenv()

# 2. Initialize the FastAPI app
app = FastAPI(title="My Agent Hackathon API")

# 3. Define the "Math Tutor" Agent
# This is the brain that will process your requests
math_agent = Agent(
    name="Math Tutor",
    instructions="You provide help with math problems. Explain your reasoning at each step and include examples.",
)

# 4. Define the Data Model (What the user sends to the API)
class UserRequest(BaseModel):
    query: str

# 5. Create the Chat Endpoint
@app.post("/chat")
async def chat_endpoint(request: UserRequest):
    try:
        print(f"User asked: {request.query}")
        
        # Run the agent with the user's query
        # This calls OpenAI, processes the logic, and gets the answer
        result = await Runner.run(math_agent, request.query)
        
        # Return the final answer
        return {
            "status": "success",
            "agent": result.agent.name,
            "response": result.final_output
        }
        
    except Exception as e:
        # If something breaks (like a bad API key), tell us why
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 6. Simple Health Check Endpoint
@app.get("/")
def home():
    return {"message": "Agent Server is up and running! Send POST requests to /chat"}