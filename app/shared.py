from dataclasses import dataclass
from typing import List

TASK_QUEUE_NAME = "job_queue"


@dataclass 
class ComputeParams:
    numbers: List[int]
    fail_first_attempt: bool