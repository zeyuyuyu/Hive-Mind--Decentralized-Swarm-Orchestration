import asyncio
import json
from dataclasses import dataclass
from typing import Dict, List, Set
import socket
import time

@dataclass
class SwarmNode:
    node_id: str
    ip: str 
    port: int
    last_seen: float
    capabilities: List[str]

class SwarmMesh:
    def __init__(self, port: int = 5555):
        self.port = port
        self.nodes: Dict[str, SwarmNode] = {}
        self.my_id = socket.gethostname()
        self.my_capabilities = ['compute', 'storage']
        
    async def start(self):
        """Start the mesh network node"""
        self.broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.broadcast_socket.bind(('', self.port))
        
        await asyncio.gather(
            self.broadcast_heartbeat(),
            self.listen_for_nodes()
        )
    
    async def broadcast_heartbeat(self):
        """Periodically broadcast node presence"""
        while True:
            msg = {
                'type': 'heartbeat',
                'node_id': self.my_id,
                'capabilities': self.my_capabilities,
                'timestamp': time.time()
            }
            self.broadcast_socket.sendto(
                json.dumps(msg).encode(),
                ('<broadcast>', self.port)
            )
            await asyncio.sleep(5)
    
    async def listen_for_nodes(self):
        """Listen for other nodes' heartbeats"""
        while True:
            data, addr = self.broadcast_socket.recvfrom(1024)
            msg = json.loads(data.decode())
            
            if msg['type'] == 'heartbeat':
                node = SwarmNode(
                    node_id=msg['node_id'],
                    ip=addr[0],
                    port=addr[1], 
                    last_seen=msg['timestamp'],
                    capabilities=msg['capabilities']
                )
                self.nodes[node.node_id] = node
                
            # Cleanup stale nodes
            self._cleanup_nodes()
    
    def _cleanup_nodes(self, max_age: float = 15.0):
        """Remove nodes that haven't been seen recently"""
        now = time.time()
        stale = []
        for node_id, node in self.nodes.items():
            if now - node.last_seen > max_age:
                stale.append(node_id)
        for node_id in stale:
            del self.nodes[node_id]
    
    def get_nodes_with_capability(self, capability: str) -> List[SwarmNode]:
        """Find nodes that have a specific capability"""
        return [
            node for node in self.nodes.values()
            if capability in node.capabilities
        ]

if __name__ == '__main__':
    mesh = SwarmMesh()
    asyncio.run(mesh.start())