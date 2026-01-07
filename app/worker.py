import asyncio
from temporalio.client import Client
from temporalio.worker import Worker

from app.shared import TASK_QUEUE_NAME
from app.activities import sum_numbers_activity
from app.workflows import JobWorkflow

async def main():
    # Connect to Temporal Server
    client = await Client.connect("localhost:7233")

    # create Worker，listen to task_queue
    worker = Worker(
        client,
        task_queue=TASK_QUEUE_NAME,
        workflows=[JobWorkflow],
        activities=[sum_numbers_activity],
    )

    print(f"Worker started... listening on {TASK_QUEUE_NAME}")
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())