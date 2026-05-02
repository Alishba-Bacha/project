"""
memory.py
Multi-strategy checkpoint saver for LangGraph.
"""

import logging
from pathlib import Path
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

memory = None

# Strategy 1: Try MemorySaver 
try:
    from langgraph.checkpoint.memory import MemorySaver
    memory = MemorySaver()
    logger.info("✅ Using MemorySaver (in-memory)")
    
except ImportError as e:
    logger.debug(f"MemorySaver import failed: {e}")
    
    # Strategy 2: Try to create a simple file-based checkpointer
    try:
        import json
        import os
        from datetime import datetime
        
        class FileCheckpointer:
            """Simple file-based checkpointer"""
            def __init__(self, base_path: Path):
                self.base_path = base_path
                self.base_path.mkdir(exist_ok=True, parents=True)
                logger.info(f"✅ Using FileCheckpointer at {base_path}")
            
            def _get_thread_path(self, thread_id):
                return self.base_path / f"{thread_id}.json"
            
            def get_next_version(self, current_version, channel_values):
                return (current_version or 0) + 1
            
            def get_tuple(self, config):
                checkpoint = self.get(config)
                if checkpoint:
                    return (config, checkpoint, {})
                return None
            
            def put(self, config, checkpoint, metadata=None):
                thread_id = config["configurable"]["thread_id"]
                file_path = self._get_thread_path(thread_id)
                
                # Add version and timestamp
                checkpoint['version'] = checkpoint.get('version', 1)
                checkpoint['timestamp'] = datetime.now().isoformat()
                
                with open(file_path, 'w') as f:
                    json.dump(checkpoint, f)
                
                return {"configurable": {"thread_id": thread_id}}
            
            def get(self, config):
                thread_id = config["configurable"]["thread_id"]
                file_path = self._get_thread_path(thread_id)
                
                if file_path.exists():
                    with open(file_path, 'r') as f:
                        return json.load(f)
                return None
            
            def list(self, config, limit=10):
                thread_id = config["configurable"]["thread_id"]
                checkpoint = self.get(config)
                if checkpoint:
                    return [(config, checkpoint, {})]
                return []
        
        # Create checkpoint directory
        checkpoint_dir = Path(__file__).parent / "checkpoints"
        memory = FileCheckpointer(checkpoint_dir)
        
    except Exception as e:
        logger.error(f"FileCheckpointer failed: {e}")
        
        # Strategy 3: Ultimate fallback - dummy memory
        class DummyMemory:
            def get_next_version(self, current_version, channel_values):
                return (current_version or 0) + 1
            
            def get_tuple(self, config):
                return None
            
            def put(self, config, checkpoint, metadata=None):
                logger.debug(f"Dummy memory put for thread: {config['configurable']['thread_id']}")
                return {"configurable": {"thread_id": config["configurable"]["thread_id"]}}
            
            def get(self, config):
                logger.debug(f"Dummy memory get for thread: {config['configurable']['thread_id']}")
                return None
            
            def list(self, config, limit=10):
                return []
        
        memory = DummyMemory()
        logger.warning("⚠️ Using dummy memory (no persistence)")

__all__ = ["memory"]