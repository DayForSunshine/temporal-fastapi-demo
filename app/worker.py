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
        workflows=[JobWorkflow], #可以在同一个worker中注册多个workflow，比如先创建账户，再下单两个workflow。
        activities=[sum_numbers_activity], #这里才真正取出代码执行，workflow里只是提取Activity名称和参数。
    )

    print(f"Worker started... listening on {TASK_QUEUE_NAME}")
    await worker.run() #可以在同一个进程中创建多个worker实例，分别监听不同的任务队列，然后asyncio.gather让它们同时运行。

if __name__ == "__main__":
    asyncio.run(main())