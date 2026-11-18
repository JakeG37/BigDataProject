"""Expose the Atlas sales and Redis statistics Flask APIs through MCP."""
import os
import sys
from pathlib import Path
from typing import Literal, Optional

import requests
from dotenv import load_dotenv
from mcp.server import MCPServer

load_dotenv(Path(__file__).with_name('.env'))
API_URL = os.getenv('FLASK_API_URL', 'http://127.0.0.1:5001').rstrip('/')
REDIS_API_URL = os.getenv('REDIS_API_URL', 'http://127.0.0.1:5002').rstrip('/')
mcp = MCPServer('Supply Store Sales')


@mcp.tool()
def search_sales(location: str, year: Optional[int] = None,
                 purchase_method: str = '', limit: int = 5) -> dict:
    """Search supply-store sales by location and optional UTC calendar year.

    Optional purchase_method: Online, Phone, or In store. Limit: 1 to 100.
    Dates are UTC ISO strings; item prices are decimal strings.
    This tool only reads data; it cannot insert, update, or delete records.
    """
    params = {'location': location, 'limit': limit}
    if year is not None:
        params['year'] = year
    if purchase_method:
        params['purchase_method'] = purchase_method

    try:
        response = requests.get(
            f'{API_URL}/sales', params=params, timeout=10
        )
    except requests.RequestException as exc:
        raise RuntimeError('Cannot reach the Flask sales API') from exc

    if response.status_code != 200:
        raise RuntimeError(f'Sales API returned HTTP {response.status_code}')
    return response.json()


@mcp.tool()
def get_statistics(key: Literal['active_users']) -> dict:
    """Get the demo application's active-user count from Redis.

    Use key 'active_users' for questions about how many users are active in the
    app. The value is a separate demo statistic with no store or year filter.
    """
    try:
        response = requests.get(f'{REDIS_API_URL}/statistics/{key}', timeout=5)
    except requests.RequestException as exc:
        raise RuntimeError('Cannot reach the Flask statistics API') from exc

    if response.status_code != 200:
        error = response.json().get('error', 'Statistics lookup failed')
        raise RuntimeError(f'Statistics API returned HTTP {response.status_code}: {error}')
    return response.json()


if __name__ == '__main__':
    if '--stdio' in sys.argv:
        mcp.run(transport='stdio')
    else:
        mcp.run(transport='streamable-http', host='127.0.0.1', port=5000)
