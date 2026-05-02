# simple_search.py
import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / "src"))

from mcp_client import MCPClient

async def main():
    if len(sys.argv) < 2:
        print("Usage: python simple_search.py 'your query'")
        return
    
    query = " ".join(sys.argv[1:])
    client = MCPClient()
    
    try:
        print(f"🔍 Searching: {query}")
        await client.connect()
        
        result = await client.search_evidence(query, 3)
        if result.get("status") == "success":
            print("\n📚 Results:")
            print(result.get("evidence", "No evidence"))
        else:
            print(f"❌ Error: {result.get('message', 'Unknown error')}")
            
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())