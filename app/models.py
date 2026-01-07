from pydantic import BaseModel
from typing import List, Optional, Any, Dict

JOB_QUEUE = "job-queue"

# Job Request
class JobInputOptions(BaseModel):
    fail_first_attempt: bool = False

class JobInputData(BaseModel):
    numbers: List[int]

class JobRequest(BaseModel):
    input: JobInputData
    options: JobInputOptions

# Job Status + Progress Response
class JobProgress(BaseModel):
    stage: str
    attempt: Optional[int] = None

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: Optional[JobProgress] = None
    result: Optional[int] = None
    error: Optional[str] = None
