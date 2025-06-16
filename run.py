#!/usr/bin/env python3
"""
Entry point script for running the Marzban Node Agent directly.

This script allows running the agent without using Docker,
useful for development and testing.
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from node_agent.main import main

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
