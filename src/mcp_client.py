"""
mcp_client.py
Client for interacting with the HallucinationTools MCP server.
"""

import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from contextlib import AsyncExitStack
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MCPClient:
    """MCP Client for Hallucination Tools"""
    
    def __init__(self):
        self.session = None
        self.exit_stack = AsyncExitStack()
        self.server_script = str(Path(__file__).parent / "mcp_server.py")
    
    async def connect(self):
        """Connect to the MCP server"""
        logger.info(f"Connecting to server: {self.server_script}")
        
        server_params = StdioServerParameters(
            command="python",
            args=["-u", self.server_script]
        )
        
        stdio_transport = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(self.stdio, self.write)
        )
        
        await self.session.initialize()
        
        # List available tools
        tools = await self.session.list_tools()
        tool_names = [tool.name for tool in tools.tools]
        logger.info(f"Connected to server. Available tools: {tool_names}")
        
        return self.session
    
    async def call_tool(self, tool_name: str, arguments: dict):
        """Call a specific tool on the server"""
        logger.info(f"Calling tool: {tool_name} with args: {arguments}")
        
        result = await self.session.call_tool(tool_name, arguments)
        
        # Parse the result
        if hasattr(result, 'content') and result.content:
            for content in result.content:
                if content.type == 'text':
                    try:
                        # Try to parse as JSON
                        parsed = json.loads(content.text)
                        # Pretty print for display
                        print(f"Result: {json.dumps(parsed, indent=2)}")
                        return parsed
                    except json.JSONDecodeError:
                        print(f"Result: {content.text}")
                        return content.text
        
        return result
    
    async def search_evidence(self, query: str, num_results: int = 3):
        """Convenience method to search for evidence"""
        return await self.call_tool("search_evidence", {
            "query": query,
            "num_results": num_results
        })
    
    async def verify_claim(self, claim: str):
        """Convenience method to verify a claim"""
        return await self.call_tool("verify_claim", {
            "claim": claim
        })
    
    async def fetch_paper(self, paper_title=None, arxiv_id=None, doi=None):
        """Fetch paper metadata"""
        args = {}
        if paper_title:
            args["paper_title"] = paper_title
        if arxiv_id:
            args["arxiv_id"] = arxiv_id
        if doi:
            args["doi"] = doi
        return await self.call_tool("fetch_paper", args)
    
    async def verify_citation(self, citation_text, expected_source=None):
        """Verify citation accuracy"""
        args = {"citation_text": citation_text}
        if expected_source:
            args["expected_source"] = expected_source
        return await self.call_tool("verify_citation", args)
    
    async def close(self):
        """Close the connection"""
        await self.exit_stack.aclose()
        logger.info("Disconnected from server")


async def main():
    """Example usage of the MCP client"""
    client = MCPClient()
    
    try:
        # Connect to server
        await client.connect()
        
        # Example 1: Search for evidence
        print("\n" + "="*60)
        print("🔍 TEST 1: Search for evidence")
        print("="*60)
        
        await client.search_evidence(
            query="Fine-tuning LLMs reduces hallucinations",
            num_results=2
        )
        
        # Example 2: Verify a claim
        print("\n" + "="*60)
        print("✅ TEST 2: Verify a claim")
        print("="*60)
        
        await client.verify_claim(
            claim="Fine-tuning LLMs reduces hallucinations in medical papers"
        )
        
        # Example 3: Fetch paper (if you want to test)
        # print("\n" + "="*60)
        # print("📄 TEST 3: Fetch paper")
        # print("="*60)
        # await client.fetch_paper(arxiv_id="2301.12345")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())