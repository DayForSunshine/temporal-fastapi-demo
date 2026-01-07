import uuid
from fastapi import FastAPI, HTTPException
from temporalio.client import Client, WorkflowFailureError
from temporalio.api.workflowservice.v1 import DescribeWorkflowExecutionRequest
from temporalio.api.common.v1 import WorkflowExecution  
from contextlib import asynccontextmanager

from app.models import JobRequest, JobStatusResponse, JobProgress
from app.workflows import JobWorkflow
from app.shared import ComputeParams, TASK_QUEUE_NAME


temporal_client = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global temporal_client
    try:
        temporal_client = await Client.connect("localhost:7233")
        yield
    finally:
        pass

app = FastAPI(lifespan=lifespan)
#app = FastAPI()

# 简单的单例模式获取 Temporal Client
async def get_client():   
    #return await Client.connect("localhost:7233") 
    if temporal_client is None:
        raise RuntimeError("Temporal client not connected")
    return temporal_client
    

# Start a Job
@app.post("/jobs", response_model=dict)
async def start_job(request: JobRequest):
    client = await get_client()
    
    job_id = f"job-{uuid.uuid4()}"

    params = ComputeParams(
        numbers=request.input.numbers,
        fail_first_attempt=request.options.fail_first_attempt
    )

    # 异步启动 Workflow
    await client.start_workflow(
        JobWorkflow.run,
        params,
        id=job_id,
        task_queue=TASK_QUEUE_NAME,
    )

    return {"job_id": job_id}

# Query Job Status + Progress
@app.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    client = await get_client()
    
    try:
        handle = client.get_workflow_handle(job_id)        
        # Get workflow status
        desc = await handle.describe()
        status_str = desc.status.name # RUNNING, COMPLETED, FAILED 等
        
        current_stage = "unknown"
        current_attempt = 0
        result = None
        error = None
        
        """
        try:
            progress_data = await handle.query(JobWorkflow.get_progress) 
            current_stage = progress_data.get("stage", "unknown")
        except Exception:
            pass        
        """
        if status_str != "COMPLETED":
            try:
                progress_data = await handle.query(JobWorkflow.get_progress)
                current_stage = progress_data.get("stage", "unknow")
            except Exception as query_err:
                print(f"Warning: Could not query workflow progress (Worker might be down): {query_err}")
                if status_str == "RUNNING":
                    current_stage = "computing (worker unreachable)"


        if status_str == "RUNNING":                   
            #current_stage = "computing"
            req = DescribeWorkflowExecutionRequest(
                namespace=client.namespace,
                execution=WorkflowExecution(workflow_id=job_id)
            )
            resp = await client.workflow_service.describe_workflow_execution(req)
            if resp.pending_activities:
                pending_activity = resp.pending_activities[0]
                if pending_activity.heartbeat_details:
                    #details = client.data_converter.from_payloads(pending_activity.heartbeat_details, [int])
                    details = client.data_converter.payload_converter.from_payloads(
                        pending_activity.heartbeat_details.payloads, [int])
                    if details:
                        current_attempt = details[0]
                else:
                    # If there is no heartbeat yet (when it has just started), the default setting is "attempt".
                    current_attempt = pending_activity.attempt

        
        elif status_str == "COMPLETED":
            #progress_data = {"stage": "completed", "attempt": 1} # Initial version simplified processing
            current_stage = "completed"
            workflow_output = await handle.result()

            if isinstance(workflow_output, dict): 
                result = workflow_output.get("result")
                current_attempt = workflow_output.get("attempt", 1)                
                """
                fail_first_attempt_flag = workflow_output.get("fail_first_attempt", False) 
                if fail_first_attempt_flag is False: 
                    current_attempt = workflow_output.get("attempt", 1) 
                else:
                    current_attempt = workflow_output.get("attempt", 2)
                """
            else:
                # Compatible for initial version which returns the int value
                result = workflow_output
                current_attempt = 1

                      
        elif status_str == "FAILED":    
            #progress_data = {"stage": "failed", "attempt": 3}         
            current_stage = "failed"
            error = "Workflow execution failed"
            try:
                config = await handle.query(JobWorkflow.get_job_config)
                current_attempt = config.get("max_attempts", 3)
            except Exception as query_err: 
                print(f"Query config failed: {query_err}")
                current_attempt = 3
        
        progress_result = {"stage": current_stage, "attempt": current_attempt}
        return JobStatusResponse(
            job_id=job_id,
            status=status_str,
            progress=JobProgress(**progress_result),
            result=result,
            error=error
        )
    except Exception as e:
        print(f"Error getting status: {e}")
        raise HTTPException(status_code=404, detail=str(e))