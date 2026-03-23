import random
import time

class SwarmNode:
    def __init__(self, node_id, capacity):
        self.node_id = node_id
        self.capacity = capacity
        self.current_load = 0
        self.last_balance_time = time.time()
        self.balance_interval = 5  # Seconds between load balancing checks

    def add_load(self, load):
        self.current_load += load
        if self.current_load > self.capacity:
            self.current_load = self.capacity

    def remove_load(self, load):
        self.current_load -= load
        if self.current_load < 0:
            self.current_load = 0

    def balance_load(self, other_nodes):
        if time.time() - self.last_balance_time < self.balance_interval:
            return

        self.last_balance_time = time.time()

        # Find the node with the lowest current load
        min_load_node = min(other_nodes, key=lambda node: node.current_load)

        # Calculate the average load across all nodes
        total_load = sum(node.current_load for node in other_nodes)
        average_load = total_load / (len(other_nodes) + 1)  # Include this node

        # If this node's load is above the average, try to offload some work
        if self.current_load > average_load:
            load_to_offload = self.current_load - average_load
            min_load_node.add_load(load_to_offload)
            self.remove_load(load_to_offload)
            print(f'Node {self.node_id} offloaded {load_to_offload} to node {min_load_node.node_id}')
