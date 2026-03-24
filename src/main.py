import asyncio
from typing import List
from .swarm_node import SwarmNode

class TaskScheduler:
    def __init__(self, swarm_nodes: List[SwarmNode]):
        self.swarm_nodes = swarm_nodes
        self.task_queue = asyncio.Queue()

    async def schedule_task(self, task):
        await self.task_queue.put(task)
        await self.dispatch_tasks()

    async def dispatch_tasks(self):
        while not self.task_queue.empty():
            task = await self.task_queue.get()
            least_loaded_node = min(self.swarm_nodes, key=lambda node: node.load_factor)
            await least_loaded_node.execute_task(task)
            self.task_queue.task_done()

class HiveMind:
    def __init__(self, swarm_nodes: List[SwarmNode]):
        self.task_scheduler = TaskScheduler(swarm_nodes)

    async def submit_task(self, task):
        await self.task_scheduler.schedule_task(task)
