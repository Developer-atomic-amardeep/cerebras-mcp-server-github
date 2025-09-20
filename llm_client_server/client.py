import asyncio
import json
import os
from contextlib import AsyncExitStack
from typing import Optional, Any, Dict, List
from cerebras.cloud.sdk import Cerebras
from dotenv import load_dotenv
from mcp.client.sse import sse_client
from mcp import ClientSession

load_dotenv()

class MCPCerebrasClient:

    """Client for interacting with MCP servers using Cerebras API."""

    def __init__(self, model: str = "llama-4-scout-17b-16e-instruct"):
        """Initialize the MCP Cerebras client."""

        self.session: Optional[ClientSession] = None
        self.stack = AsyncExitStack()
        self.client = Cerebras(api_key=os.getenv("CEREBRAS_API_KEY"))
        self.model = model
        self.stdio: Optional[Any] = None
        self.write: Optional[Any] = None

    async def connect_to_server(self, server_url: str = "http://localhost:8050/sse"):
        """Connect to the MCP server via SSE."""

        sse_transport = await self.stack.enter_async_context(
            sse_client(server_url)
        )

        self.stdio, self.write = sse_transport
        self.session = await self.stack.enter_async_context(
            ClientSession(self.stdio, self.write)
        )

        await self.session.initialize()

        tools_result = await self.session.list_tools()

        print("Available tools:")
        for tool in tools_result.tools:
            print(f"- {tool.name}: {tool.description}")

    async def get_mcp_tools(self) -> List[Dict[str, Any]]:
        """Get available tools from MCP server in Cerebras format."""

        tool_result = await self.session.list_tools()

        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "strict": True,
                    "description": tool.description,
                    "parameters": tool.inputSchema,
                },
            }
            for tool in tool_result.tools
        ]

    async def process_query(self, query: str) -> str:
        """Process a query using Cerebras API and available tools."""

        tools = await self.get_mcp_tools()

        messages = [
            {"role": "system", "content": "You are a helpful assistant with access to tools. Use the available tools when needed to answer questions."},
            {"role": "user", "content": query},
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            parallel_tool_calls=False,
        )

        choice = response.choices[0].message

        if choice.tool_calls:
            for tool_call in choice.tool_calls:
                print(f"Model executing function '{tool_call.function.name}' with arguments {tool_call.function.arguments}")

                result = await self.session.call_tool(
                    tool_call.function.name, 
                    arguments=json.loads(tool_call.function.arguments)
                )

                messages.append({
                    "role": "tool",
                    "content": json.dumps(result.content[0].text),
                    "tool_call_id": tool_call.id
                })

            final_response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
            )

            return final_response.choices[0].message.content
    
        return choice.content

    async def cleanup(self):
        """Cleanup the resources."""
        await self.stack.aclose()

async def main():
    client = MCPCerebrasClient()
    try:
        await client.connect_to_server()

        query = "What is the company policy on remote work?"
        response = await client.process_query(query)
        print(f"Response: {response}")
    finally:
        await client.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
