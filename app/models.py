from pydantic import BaseModel, field_validator
from typing import List, Optional

JOB_QUEUE = "job-queue"

# Job Request
class JobInputOptions(BaseModel):
    fail_first_attempt: bool = False

class JobInputData(BaseModel):
    numbers: List[int]

class JobRequest(BaseModel):
    input: JobInputData
    #options: JobInputOptions
    
    @field_validator('input') #自定义校验input字段
    def validate_input(cls, v): #cls表示当前类本身（JobRequest）， v待校验的值input
        if v.numbers is None:
            raise ValueError("Must include 'numbers' attribute") #Pydantic捕获ValueError包装成RequestValidationError，FastAPI捕获RequestValidationError然后将状态码设为422和错误信息一起塞进响应体发回msg字段显示
        if not isinstance(v.numbers, list):
            raise ValueError("'numbers' must be a List")
        if not v.numbers:
            raise ValueError("'numbers' can not be empty List")
        return v #如果不返回v，Pydantic会认为这个字段的值是None，导致数据丢失。


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
