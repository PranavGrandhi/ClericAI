from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

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

@app.post("/submit_question_and_documents")
async def submit_documents(submission: DocumentSubmission, background_tasks: BackgroundTasks):
    print(submission)
    storage['question'] = submission.question
    storage['facts'] = []  # Initialize or clear previous facts
    storage['status'] = 'processing'
    background_tasks.add_task(process_documents, submission.question, submission.documents)
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
