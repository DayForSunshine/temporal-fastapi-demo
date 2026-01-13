from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy
from typing import Dict

# Safely import Data and Activity definition
with workflow.unsafe.imports_passed_through():
    from app.activities import sum_numbers_activity
    from app.shared import ComputeParams

@workflow.defn #如果这里加上(name="...")，工作流类名称就是此name，而不是默认的下面的JobWorkfow类名，Worker注册Workflow需要注意
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
    async def run(self, params: ComputeParams) -> Dict[str, int]: #兼容老版本python支持泛型；新版本可以dict[str, int]支持泛型。也可以直接写Dict/dict
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
            result = await workflow.execute_activity( #await表明串行跑这一个activity，也可以后面再添加其他activity并行跑多个，最后asyncio.gather合并
                sum_numbers_activity, #这里只提取了Activity名称（默认为函数名）和参数，并没有真正执行函数代码，把这些信息打包成一个命令发送给Temporal Server。
                params,
                start_to_close_timeout=timedelta(seconds=60), #Change to 10 seconds and check the timeout effect.
                retry_policy=retry_policy  
            )                                                 #在main.py中start_workflow有execution_timeout和run_timeout，查询和这里的timeout用法区别
            self._stage = "completed"
            return result #返回类型为sum_numbers_activity的返回类型

        except Exception as e:
            self._stage = "failed"
            raise e
