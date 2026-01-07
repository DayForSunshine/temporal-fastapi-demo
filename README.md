1. How to start Temporal (Docker Compose recommended)
Run `docker-compose up -d` in the project root directory to start the Temporal server:
- Linux systems can run this directly.
- Windows and macOS systems require Docker Desktop or a Linux virtual machine environment.
Access http://localhost:8082 to confirm the Temporal Web UI is running.

2. How to start the worker and API
    (1) Keep the terminal window running the Temporal service open. In a new terminal window and within the project root directory, first create a virtual environment: `python -m venv env` (env is custom virtual environment name). Activate the virtual environment: `.\env\Scripts\Activate.ps1`. Then install development dependencies: `python -m pip install requirements.txt`.
    (2) You can start FastAPI directly in the new terminal window from step (1) (within the virtual environment): `uvicorn app.main:app --reload`;
    Alternatively, close the window from step (1), open a new terminal window, activate the virtual environment in the project root directory, then start FastAPI: uvicorn app.main:app --reload.
    (3) Keep both terminal windows running Temporal service and FastAPI. In a third new terminal window, activate the virtual environment in the project root directory, then start the worker: `python -m app.worker`.

3. How to verify all core requirements

Scenario 1: Normal, execution successful
In a fourth new terminal window (from any path), send a POST request:
curl -X POST http://localhost:8000/jobs \
-H “Content-Type: application/json” \
-d '{ “input”: {“numbers”: [1, 2, 3, 4]}, “options”: {“fail_first_attempt”: false} }'

Observation:
    1. Query the status using the returned job_id `curl http://localhost:8000/jobs/job_id`. Continuously check the status before workflow completion (refresh if using a browser). You will see status as RUNNING, custom stage as computing, and attempt values changing;
    2. After workflow completion, the final status will be COMPLETED, custom stage will be completed, and result will be 10.

Scenario 2: Simulating failure with automatic retry, ultimately succeeding
In a fourth new terminal window (from any directory), send a POST request:
curl -X POST http://localhost:8000/jobs \
-H “Content-Type: application/json” \
-d ‘{ “input”: {“numbers”: [1, 2, 3, 4]}, “options”: {“fail_first_attempt”: true} }’

Observe:
    1. In the Worker terminal logs, you will see the first attempt throw an exception (RuntimeError). If viewed via browser, no exception details will appear; only the status as RUNNING and stage as computing will be displayed.
    2. Temporal automatically retries. Continuously checking before workflow completion (refreshing the browser view) shows the attempt count incrementing.
    3. Querying the API again eventually returns status as COMPLETED, with the custom stage set to completed and result as 10.
    4. This confirms the activity retry strategy is functioning.

Scenario 3: Simulating a timeout with automatic retry, yet the execution ultimately fails

Modify the timeout parameter `start_to_close_timeout` in `workflows.py` from `seconds=60` to `seconds=10`. In a fourth new terminal window (from any directory), send the POST request:

curl -X POST http://localhost:8000/jobs \
-H “Content-Type: application/json” \
-d ‘{ “input”: {“numbers”: [1, 2, 3, 4]}, “options”: {“fail_first_attempt”: true} }’

Observe:
    1. In the Worker terminal logs, you'll see an exception thrown (RuntimeError) indicating “Activity not found on completion.” If viewed via browser, no exception details appear—only the status as RUNNING and stage as computing.
    2. Temporal automatically retries until the maximum retry count is exhausted. Continuously query before workflow completion (refresh if using browser) to observe the attempt count changing;
    3. Upon re-querying the API, the status eventually changes to FAILED, with the custom stage set to failed and the attempt count reaching the defined maximum of 5.

AI Usage Statement
This project's code framework and API definitions reference AI-generated suggestions, with manual coding, review, and testing performed.

Key Design Notes
Retry Strategy: The RetryPolicy configured within the Workflow enables automatic retries for Activities after simulated failures, eliminating manual intervention.
Determinism: Random or system time usage is avoided in the Workflow. All non-deterministic operations (e.g., simulated failure logic) are encapsulated within Activities. The Workflow securely imports Activities via context management `unsafe.imports_passed_through`.
Query Mechanism: Temporal Query (`get_progress`) is employed to obtain real-time Workflow internal states and Activity return values is used to retrieve the Workflow's completed status without relying on external databases.

