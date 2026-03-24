import os
import time
import psutil
import requests

class SwarmNode:
    def __init__(self, node_id, swarm_manager_url):
        self.node_id = node_id
        self.swarm_manager_url = swarm_manager_url
        self.min_cpu_utilization = 20
        self.max_cpu_utilization = 80
        self.min_memory_utilization = 20
        self.max_memory_utilization = 80

    def monitor_resources(self):
        cpu_utilization = psutil.cpu_percent(interval=1)
        memory_utilization = psutil.virtual_memory().percent

        if cpu_utilization < self.min_cpu_utilization or cpu_utilization > self.max_cpu_utilization or \
           memory_utilization < self.min_memory_utilization or memory_utilization > self.max_memory_utilization:
            self.scale_swarm()

    def scale_swarm(self):
        current_nodes = self._get_current_nodes()
        if cpu_utilization < self.min_cpu_utilization or memory_utilization < self.min_memory_utilization:
            self._add_node()
        elif cpu_utilization > self.max_cpu_utilization or memory_utilization > self.max_memory_utilization:
            self._remove_node(current_nodes)

    def _get_current_nodes(self):
        response = requests.get(f'{self.swarm_manager_url}/nodes')
        return response.json()

    def _add_node(self):
        response = requests.post(f'{self.swarm_manager_url}/nodes')
        if response.status_code == 200:
            print(f'Added new node to the swarm.')
        else:
            print(f'Failed to add new node to the swarm.')

    def _remove_node(self, current_nodes):
        if len(current_nodes) > 1:
            node_to_remove = current_nodes[-1]
            response = requests.delete(f'{self.swarm_manager_url}/nodes/{node_to_remove["ID"]}')
            if response.status_code == 200:
                print(f'Removed node {node_to_remove["ID"]} from the swarm.')
            else:
                print(f'Failed to remove node {node_to_remove["ID"]} from the swarm.')
        else:
            print(f'Cannot remove the last node from the swarm.')
