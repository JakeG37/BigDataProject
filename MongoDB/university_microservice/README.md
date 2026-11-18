# Supply-store sales and Redis statistics MCP lab

Atlas holds the existing **sample_supplies.sales** collection. Redis Cloud
holds the separate `active_users` demo statistic, an app-wide count.

```text
HTTP client -> Flask /sales (5001) -> Atlas sample_supplies.sales
HTTP client -> Flask /statistics/active_users (5002) -> Redis Cloud active_users
User question -> Ollama (11434) selects tools -> MCP client invokes tools
MCP server (5000) -> search_sales -> sales Flask API -> Atlas
                  -> get_statistics -> statistics Flask API -> Redis
```

## Configure

From the repository root in Command Prompt:

```cmd
cd MongoDB\university_microservice
```

If `.env` does not exist, copy `.env.example` to `.env`. Otherwise edit your
existing `.env`, preserving your real Atlas connection string. Use:

```dotenv
MONGODB_URI=mongodb+srv://YOUR_CLUSTER.mongodb.net/
MONGODB_USERNAME=your-atlas-database-user
MONGODB_PASSWORD='your-atlas-database-password'
MONGO_DB=sample_supplies
MONGO_COLLECTION=sales
FLASK_API_URL=http://127.0.0.1:5001
```

Your Atlas database user needs read access to sample_supplies, and Atlas Network
Access must allow your IP. Keep `.env` private. Scripts load it automatically.
Use one URI variable. The code also accepts `MONGO_URI` and gives it precedence
if both are set. With the separate `MONGODB_USERNAME` and `MONGODB_PASSWORD`
fields, remove the username and password from the URI. PyMongo receives them
directly, so the password field takes the original password without URL encoding.

If you need to create the virtual environment, run `py -3.11 -m venv venv`.
Install the project requirements into your existing environment:

```cmd
venv\Scripts\python.exe -m pip install -r requirements.txt
```

If your environment is called `.venv`, use that name in the commands below.

## Run Flask first

```cmd
venv\Scripts\python.exe app.py
```

Keep this terminal running. Open this URL in a browser:

http://127.0.0.1:5001/sales?location=Seattle&year=2015&limit=5

Or use another Command Prompt in the same directory:

```cmd
curl.exe --fail-with-body "http://127.0.0.1:5001/sales?location=Seattle&year=2015&limit=5"
```

Try Denver and 2017 for your other example. Location matches a whole location,
ignoring case. Optional `purchase_method`: `Phone`, `Online`, or `In store`
(encode the space as `%20` in a URL). Omit year, or leave it blank, for all years.
The limit defaults to 5 and must be between 1 and 100. `count` is the number
returned, not all matching sales. No matches returns an empty `sales` list.

The response contains the documents, including items and customer. ObjectIds
become strings, dates become UTC ISO strings, and Decimal128 prices become
strings to retain their exact decimal value. The year filter uses a UTC date
range on `saleDate`: January 1 of the selected year through just before January
1 of the next year. Invalid input returns HTTP 400; database failure returns 503.

## Connect to Redis Cloud and run the statistics API

In the Redis Cloud console, open your lab database and select **Connect**.
Use the current endpoint and database credentials in your existing `.env`.
The sample YAML's `user` field maps to `REDIS_USERNAME`.

```dotenv
REDIS_HOST=your-redis-cloud-host
REDIS_PORT=6379
REDIS_DB=0
REDIS_USERNAME=default
REDIS_PASSWORD='your-redis-cloud-database-password'
REDIS_TLS=true
```

Enter the hostname and port from the console as separate values. Keep TLS
enabled for deployment. If the console provides a CA certificate, download
it and set `REDIS_CA_FILE` to its local path. An existing non-TLS lab endpoint
requires setting `REDIS_TLS=false` explicitly.

From the project folder, check the connection and whether the read-only demo
key is present:

```cmd
venv\Scripts\python.exe -c "from redis_app import redis_client; print('Redis Cloud reachable:', redis_client.ping()); print('Active-user key present:', redis_client.get('active_users') is not None)"
```

The Flask endpoint reads an existing `active_users` key. If the key is missing
and you manage the lab database, you can initialize a fictitious count through
your Redis client with `SET active_users 42 NX`. `NX` preserves any existing
value.

Start the statistics API in its own Command Prompt from the project folder:

```cmd
venv\Scripts\python.exe redis_app.py
```

Leave that window open. In another window, verify the Redis REST response:

```cmd
curl.exe --fail-with-body "http://127.0.0.1:5002/statistics/active_users"
```

If the demo key contains 42, the response is `{"key":"active_users","value":42}`. An unset statistic
returns HTTP 404, and an unavailable Redis server returns HTTP 503.

## Test MCP

Keep both Flask APIs running. Start or restart the MCP server in a separate
Command Prompt from the project folder:

```cmd
venv\Scripts\python.exe mcp_server.py
```

In another window, test tool discovery and invocation:

```cmd
venv\Scripts\python.exe demo_mcp_client.py
```

The direct test connects to `http://127.0.0.1:5000/mcp`. It lists both tools and
calls `search_sales` with Seattle, 2015, and a limit of 5, then calls
`get_statistics` with `active_users`. Compare each result with its REST
response.

## Add Ollama (lecture pages 8 and 11)

Install the Ollama Windows application from https://ollama.com/download/windows
and open it. The Python package alone does not install the local model server.
If you installed it while terminals were open, open a new terminal so `ollama`
is on PATH. Download the model specified in the lecture:

```cmd
ollama pull qwen3:4b
```

If the app is not already serving, run `ollama serve` in a separate terminal
and leave it running. If it reports that the port is in use, the server may
already be running; check with `ollama list`.

Keep both Flask APIs and MCP running. From this project folder run:

```cmd
venv\Scripts\python.exe ollama_client.py "Find five sales from Seattle in 2015. Give their dates and purchase methods. Also report the demo app's active-user count."
```

Without an argument, the script asks for a question. It discovers tools over
MCP, translates their names/descriptions/input schemas into Ollama function
definitions, lets the model choose tool calls, executes those calls through MCP,
and sends the results back to Ollama for a final answer. The model has no direct
database connection. The trace prints discovered tools, chosen arguments, and
tool status. Verify that it calls both tools successfully and that the final
answer agrees with the direct MCP results.

Optional `.env` settings (defaults shown):

```dotenv
MCP_URL=http://127.0.0.1:5000/mcp
OLLAMA_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen3:4b
```

The client limits model rounds, tool calls, and request duration. The REST API
validates filters and caps records at 100. These limits help with the lecture's
runaway-request discussion; they are not server-wide rate limiting. A shared
deployment would also need authentication, rate limits, and concurrency limits.

## Relation to the full lecture lab

The project now uses `MCPServer` and `Client` from MCP SDK **2.x**, matching the
professor's template. Use port **5000** consistently for MCP; the slide 10
example uses 8000, while the template and this project use 5000. The sales
and statistics Flask APIs use 5001 and 5002, respectively.

Slide 13 asks for a procedure/code report, comparison of REST and MCP, a security
discussion, and a group presentation. Use actual results in the report; the
sample-record count does not represent total sales in a city or year.

References:

- [Atlas sample supplies schema](https://www.mongodb.com/docs/manual/sample-data/sample-supplies/)
- [MCP SDK client](https://py.sdk.modelcontextprotocol.io/client/)
- [Ollama tool calling](https://docs.ollama.com/capabilities/tool-calling)
- [Connect redis-py to Redis Cloud](https://redis.io/docs/latest/develop/clients/redis-py/connect/)
