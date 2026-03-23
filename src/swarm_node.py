import asyncio
import json
from dataclasses import dataclass
from typing import List, Set
import websockets

@dataclass
class SwarmNode:
    node_id: str
    peers: Set[str]
    ws_port: int
    is_alive: bool = True

    async def start(self):
        self.server = await websockets.serve(
            self.handle_connection,
            'localhost',
            self.ws_port
        )
        await self.discover_peers()
        await self.server.wait_closed()

    async def handle_connection(self, websocket, path):
        try:
            async for message in websocket:
                data = json.loads(message)
                if data['type'] == 'discovery':
                    await self.handle_discovery(websocket, data)
                elif data['type'] == 'task':
                    await self.handle_task(websocket, data)
        except websockets.exceptions.ConnectionClosed:
            pass

    async def handle_discovery(self, websocket, data):
        peer_id = data['node_id']
        if peer_id not in self.peers:
            self.peers.add(peer_id)
            # Broadcast new peer to all connected nodes
            await self.broadcast_peer(peer_id)
        
        # Send back our known peers
        await websocket.send(json.dumps({
            'type': 'peers',
            'peers': list(self.peers)
        }))

    async def handle_task(self, websocket, data):
        # Process incoming task
        result = await self.execute_task(data['payload'])
        await websocket.send(json.dumps({
            'type': 'result',
            'task_id': data['task_id'],
            'result': result
        }))

    async def discover_peers(self):
        # Try connecting to potential peers on nearby ports
        base_port = 8000
        for port in range(base_port, base_port + 10):
            if port != self.ws_port:
                try:
                    uri = f'ws://localhost:{port}'
                    async with websockets.connect(uri) as websocket:
                        await websocket.send(json.dumps({
                            'type': 'discovery',
                            'node_id': self.node_id
                        }))
                        response = await websocket.recv()
                        peers_data = json.loads(response)
                        self.peers.update(peers_data['peers'])
                except:
                    continue

    async def broadcast_peer(self, new_peer_id):
        # Notify all peers about new node
        for peer in self.peers:
            try:
                uri = f'ws://localhost:{self.get_port_for_peer(peer)}'
                async with websockets.connect(uri) as websocket:
                    await websocket.send(json.dumps({
                        'type': 'new_peer',
                        'node_id': new_peer_id
                    }))
            except:
                continue

    async def execute_task(self, payload):
        # Implement task execution logic here
        return {'status': 'completed', 'data': payload}

    def get_port_for_peer(self, peer_id):
        # Simple hash function to determine peer's port
        return 8000 + hash(peer_id) % 10

    async def shutdown(self):
        self.is_alive = False
        self.server.close()
        await self.server.wait_closed()
