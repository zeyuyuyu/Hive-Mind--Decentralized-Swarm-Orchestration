import os
import asyncio
from hive_mind.swarm import Swarm
from hive_mind.agent import Agent
from hive_mind.governance import GovernanceProtocol

# Core logic for Hive-Mind
async def main():
    # Initialize the swarm
    swarm = Swarm()

    # Register agents to the swarm
    agent1 = Agent("agent1")
    agent2 = Agent("agent2")
    agent3 = Agent("agent3")
    swarm.register_agent(agent1)
    swarm.register_agent(agent2)
    swarm.register_agent(agent3)

    # Start the decentralized governance protocol
    governance = GovernanceProtocol(swarm)
    await governance.start()

    # Perform swarm-based orchestration
    await swarm.orchestrate()

if __name__ == "__main__":
    asyncio.run(main())