from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from openai import OpenAI
import os
import requests

app = FastAPI()

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

# Add CORS middleware to allow connections from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

class DocumentSubmission(BaseModel):
    question: str
    documents: List[str]

class FactResponse(BaseModel):
    question: str
    facts: List[str] = []
    status: str = 'processing'

# In-memory storage to simulate a database
storage = {}

def extract_facts_with_gpt4(question, documents):
    combined_logs = ""
    for document in documents:
        try:
            response = requests.get(document)
            response.raise_for_status()  # Raise an error for bad responses
            combined_logs += response.text + "\n\n"
        except requests.RequestException as e:
            print(f"Failed to fetch {document}: {e}")
            return None  # Or handle it differently depending on your needs

    combined_logs = combined_logs.strip()
    
    # Craft the prompt to send to GPT-4
    prompt = f"Objective: Extract the final consensus or key facts in response to the question provided, from compiled logs.\n\nContext: The logs consist of discussions on a specific topic.\n\nRequirement: Provide only the final consensus or conclusive facts established at the end of the discussions, excluding any preliminary dialogue.\n\nQuestion: \"{question}\"\n\nLogs:\n{combined_logs}\n\nFinal Consensus:"

    try:
        # Make an API call to OpenAI's GPT-4
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant tasked with extracting factual information."},
                {"role": "user", "content": prompt}
            ]
        )

        # Extract the response text from the API response in the form of a string
        return response.choices[0].message.content
    except Exception as e:
        print(f"Failed to obtain response from GPT-4: {e}")
        return "Error in processing logs."

async def process_documents_with_gpt4(question, documents):
    # Extract facts using GPT-4
    result = extract_facts_with_gpt4(question, documents)
    storage['facts'] = [result]
    storage['status'] = 'done'

@app.post("/submit_question_and_documents")
async def submit_documents(submission: DocumentSubmission, background_tasks: BackgroundTasks):
    storage['question'] = submission.question
    storage['facts'] = []  # Initialize or clear previous facts
    storage['status'] = 'processing'
    background_tasks.add_task(process_documents_with_gpt4, submission.question, submission.documents)
    return {"message": "Processing started"}

@app.get("/get_question_and_facts", response_model=FactResponse)
async def get_facts():
    if 'question' in storage:
        return FactResponse(question=storage['question'], facts=storage['facts'], status=storage['status'])
    raise HTTPException(status_code=404, detail="No processing data available")

async def process_documents(question, documents):
    # Dummy processing logic
    # In reality, you would fetch each document, process it, and update `storage['facts']`
    import time
    time.sleep(5)  # Simulate some processing time
    storage['facts'] = ["Fact extracted from document 1", "Fact extracted from document 2"]
    storage['status'] = 'done'

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
