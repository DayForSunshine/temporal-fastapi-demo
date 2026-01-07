from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy
from typing import Dict

# Safely import Data and Activity definition
with workflow.unsafe.imports_passed_through():
    from app.activities import sum_numbers_activity
    from app.shared import ComputeParams

@workflow.defn
class JobWorkflow:
    def __init__(self) -> None:
        self._stage = "pending"
        self._max_attempts = 5 #Set as a class variable, which can be queried by FastAPI

    # Query Workflow RetryPolicy _max_attempts config
    @workflow.query
    def get_job_config(self) -> dict:
        return {"max_attempts": self._max_attempts}

    # Query Workflow progress
    @workflow.query
    def get_progress(self) -> dict:
        return {"stage": self._stage} 

    @workflow.run
    async def run(self, params: ComputeParams) -> Dict:
        self._stage = "computing"        
        # configure Activity RetryPolicy
        retry_policy = RetryPolicy(
            maximum_attempts=self._max_attempts,
            #maximum_attempts=3,
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(seconds=10),
            backoff_coefficient=1
        )
        
        try:            
            result = await workflow.execute_activity(
                sum_numbers_activity,
                params,
                start_to_close_timeout=timedelta(seconds=60), #Change to 10 seconds and check the timeout effect.
                retry_policy=retry_policy
            )
            self._stage = "completed"
            return result

        except Exception as e:
            self._stage = "failed"
            raise e
