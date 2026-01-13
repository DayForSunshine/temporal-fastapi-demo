import asyncio
from temporalio import activity

from typing import Dict
from app.shared import ComputeParams


@activity.defn
async def sum_numbers_activity(params: ComputeParams) -> Dict:
    info = activity.info()
    attempt = info.attempt
    
    #Send heartbeats，tell Server attempt times. FastAPI can query attempt times via heartbeats
    activity.heartbeat(attempt) 
    #activity.logger.info(f"Activity attempt: {attempt}, Fail option: {params.fail_first_attempt}")
    activity.logger.info(f"Activity attempt: {attempt}")

    # If fail_first_attempt=true，first attempt fails and succeed after first retry.
    """
    if params.fail_first_attempt and attempt == 1:
        raise RuntimeError("Simulated failure on first attempt as requested.")
    """
    
    # Simulate simple calculating job
    total = sum(params.numbers)
    
    # Simulate the time consumption to observe the "RUNNING" status
    await asyncio.sleep(15) 
    
    #return total
    return {
        "result": total,
        "attempt": attempt
        #"fail_first_attempt": params.fail_first_attempt
    }
