"""Discover and invoke MCP tools without an AI model (the slides' mcptest)."""
import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from mcp import Client

load_dotenv(Path(__file__).with_name('.env'))
MCP_URL = os.getenv('MCP_URL', 'http://127.0.0.1:5000/mcp')


async def main():
    async with Client(MCP_URL) as client:
        tools = await client.list_tools()
        print('Available MCP tools:')
        for tool in tools.tools:
            print('-', tool.name, tool.input_schema)
        calls = (
            ('search_sales', {'location': 'Seattle', 'year': 2015, 'limit': 5}),
            ('get_statistics', {'location': 'Seattle', 'year': 2015}),
        )
        failed_tools = []
        for name, arguments in calls:
            print(f'\n{name} results:')
            result = await client.call_tool(name, arguments)
            for item in result.content:
                if item.type == 'text':
                    print(item.text)
            if result.is_error:
                failed_tools.append(name)
        if failed_tools:
            raise RuntimeError(f'MCP calls failed: {", ".join(failed_tools)}')


if __name__ == '__main__':
    asyncio.run(main())
