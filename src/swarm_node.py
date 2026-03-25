import asyncio
import json
from typing import Dict, Set
from dataclasses import dataclass
import logging

@dataclass
class NodeInfo:
    node_id: str
    address: str
    port: int
    capabilities: Set[str]
    last_seen: float

class SwarmNode:
    def __init__(self, node_id: str, port: int):
        self.node_id = node_id
        self.port = port
        self.peers: Dict[str, NodeInfo] = {}
        self.capabilities = set(['compute', 'storage'])
        self.logger = logging.getLogger('SwarmNode')
        
    async def start(self):
        """Start the swarm node and begin peer discovery"""
        self.server = await asyncio.start_server(
            self._handle_connection, '0.0.0.0', self.port)
        self.logger.info(f'Node {self.node_id} listening on port {self.port}')
        asyncio.create_task(self._periodic_heartbeat())
        asyncio.create_task(self._cleanup_stale_peers())

    async def _handle_connection(self, reader, writer):
        """Handle incoming peer connections"""
        data = await reader.read(1024)
        msg = json.loads(data.decode())
        
        if msg['type'] == 'discovery':
            # Register new peer
            peer_info = NodeInfo(
                node_id=msg['node_id'],
                address=writer.get_extra_info('peername')[0],
                port=msg['port'],
                capabilities=set(msg['capabilities']),
                last_seen=asyncio.get_event_loop().time()
            )
            self.peers[msg['node_id']] = peer_info
            
            # Send response with our info
            response = {
                'type': 'discovery_response',
                'node_id': self.node_id,
                'port': self.port,
                'capabilities': list(self.capabilities)
            }
            writer.write(json.dumps(response).encode())
            await writer.drain()
            
        elif msg['type'] == 'heartbeat':
            if msg['node_id'] in self.peers:
                self.peers[msg['node_id']].last_seen = \\
                    asyncio.get_event_loop().time()
                
        writer.close()
        await writer.wait_closed()

    async def _periodic_heartbeat(self):
        """Periodically send heartbeat to all known peers"""
        while True:
            for peer in self.peers.values():
                try:
                    reader, writer = await asyncio.open_connection(
                        peer.address, peer.port)
                    
                    msg = {
                        'type': 'heartbeat',
                        'node_id': self.node_id
                    }
                    writer.write(json.dumps(msg).encode())
                    await writer.drain()
                    writer.close()
                    await writer.wait_closed()
                    
                except Exception as e:
                    self.logger.warning(
                        f'Failed to send heartbeat to {peer.node_id}: {e}')
                    
            await asyncio.sleep(5)

    async def _cleanup_stale_peers(self):
        """Remove peers that haven't been seen recently"""
        while True:
            current_time = asyncio.get_event_loop().time()
            stale_peers = [
                node_id for node_id, info in self.peers.items()
                if current_time - info.last_seen > 15
            ]
            
            for node_id in stale_peers:
                self.logger.info(f'Removing stale peer {node_id}')
                del self.peers[node_id]
                
            await asyncio.sleep(5)

    async def broadcast_to_peers(self, message: dict):
        """Send a message to all connected peers"""
        for peer in self.peers.values():
            try:
                reader, writer = await asyncio.open_connection(
                    peer.address, peer.port)
                writer.write(json.dumps(message).encode())
                await writer.drain()
                writer.close()
                await writer.wait_closed()
            except Exception as e:
                self.logger.error(
                    f'Failed to broadcast to {peer.node_id}: {e}')

    def get_peers_with_capability(self, capability: str) -> Set[str]:
        """Find all peers that have a specific capability"""
        return {node_id for node_id, info in self.peers.items() 
                if capability in info.capabilities}
