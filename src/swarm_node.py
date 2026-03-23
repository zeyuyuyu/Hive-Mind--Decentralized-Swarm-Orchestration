import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Dict, Set

@dataclass
class NodeInfo:
    node_id: str
    ip: str
    port: int
    last_seen: float
    capabilities: Set[str]

class SwarmNode:
    def __init__(self, node_id: str, port: int):
        self.node_id = node_id
        self.port = port
        self.peers: Dict[str, NodeInfo] = {}
        self.capabilities = set(['compute', 'storage'])
        self.logger = logging.getLogger('SwarmNode')

    async def start(self):
        self.server = await asyncio.start_server(
            self.handle_connection, '0.0.0.0', self.port)
        self.discovery_task = asyncio.create_task(self.periodic_discovery())
        self.cleanup_task = asyncio.create_task(self.periodic_cleanup())
        self.logger.info(f'Node {self.node_id} listening on port {self.port}')

    async def stop(self):
        self.discovery_task.cancel()
        self.cleanup_task.cancel()
        self.server.close()
        await self.server.wait_closed()

    async def handle_connection(self, reader, writer):
        try:
            data = await reader.read(1024)
            message = json.loads(data.decode())
            
            if message['type'] == 'discovery':
                await self.handle_discovery(message, writer)
            elif message['type'] == 'task':
                await self.handle_task(message, writer)

            writer.close()
            await writer.wait_closed()

        except Exception as e:
            self.logger.error(f'Error handling connection: {e}')

    async def handle_discovery(self, message, writer):
        peer_info = NodeInfo(
            node_id=message['node_id'],
            ip=message['ip'],
            port=message['port'],
            last_seen=asyncio.get_event_loop().time(),
            capabilities=set(message['capabilities'])
        )
        self.peers[peer_info.node_id] = peer_info

        # Reply with our info
        response = {
            'type': 'discovery_reply',
            'node_id': self.node_id,
            'capabilities': list(self.capabilities)
        }
        writer.write(json.dumps(response).encode())
        await writer.drain()

    async def periodic_discovery(self):
        while True:
            try:
                # Broadcast discovery to known peers
                for peer in self.peers.values():
                    try:
                        reader, writer = await asyncio.open_connection(
                            peer.ip, peer.port)
                        
                        message = {
                            'type': 'discovery',
                            'node_id': self.node_id,
                            'ip': '0.0.0.0',  # Replace with actual IP
                            'port': self.port,
                            'capabilities': list(self.capabilities)
                        }
                        
                        writer.write(json.dumps(message).encode())
                        await writer.drain()
                        
                        data = await reader.read(1024)
                        response = json.loads(data.decode())
                        
                        if response['type'] == 'discovery_reply':
                            peer.last_seen = asyncio.get_event_loop().time()
                            peer.capabilities = set(response['capabilities'])
                        
                        writer.close()
                        await writer.wait_closed()
                        
                    except Exception as e:
                        self.logger.warning(f'Failed to contact peer {peer.node_id}: {e}')
                        
            except Exception as e:
                self.logger.error(f'Error in discovery: {e}')
                
            await asyncio.sleep(60)  # Run discovery every minute

    async def periodic_cleanup(self):
        while True:
            try:
                current_time = asyncio.get_event_loop().time()
                expired_peers = [
                    node_id for node_id, peer in self.peers.items()
                    if current_time - peer.last_seen > 180  # 3 minutes timeout
                ]
                
                for node_id in expired_peers:
                    del self.peers[node_id]
                    self.logger.info(f'Removed inactive peer {node_id}')
                    
            except Exception as e:
                self.logger.error(f'Error in cleanup: {e}')
                
            await asyncio.sleep(60)

    async def handle_task(self, message, writer):
        # Task handling implementation
        pass
