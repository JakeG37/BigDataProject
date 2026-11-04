# Atlas supply-store sales assignment

The project now reads your existing **sample_supplies.sales** collection.
The folder keeps its original name so your existing virtual environment works.
No seed script or data insertion is needed.

```text
HTTP client -> Flask /sales (5001) -> Atlas sample_supplies.sales
User question -> Python Ollama/MCP client -> Ollama (11434) selects tools
Python client -> MCP search_sales (5000) -> same Flask API -> Atlas
```

## Configure

From the repository root in PowerShell:

```powershell
cd MongoDB\university_microservice
```

If `.env` does not exist, copy `.env.example` to `.env`. Otherwise edit your
existing `.env`, preserving your real Atlas connection string. Use:

```dotenv
MONGO_URI=mongodb+srv://YOUR_USER:YOUR_PASSWORD@YOUR_CLUSTER.mongodb.net/
MONGO_DB=sample_supplies
MONGO_COLLECTION=sales
FLASK_API_URL=http://127.0.0.1:5001
```

Your Atlas database user needs read access to sample_supplies, and Atlas Network
Access must allow your IP. Keep `.env` private. Scripts load it automatically.
`MONGODB_URI` is also accepted as an alternative to `MONGO_URI`. If your file
contains `MONGODB_USERNAME` and `MONGODB_PASSWORD`, those are passed separately
to PyMongo. A missing URI now produces a configuration error instead of silently
connecting to localhost.

If you have not installed the virtual environment:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

If the environment already exists, still run the pip install command above:
the lecture version now uses **MCP SDK 2.x** and the Ollama Python package.
Restart any old MCP server after upgrading.

## Run Flask first

```powershell
.\.venv\Scripts\python.exe app.py
```

Keep this terminal running. Open this URL in a browser:

http://127.0.0.1:5001/sales?location=Seattle&year=2015&limit=5

Or use a second PowerShell terminal in the same directory:

```powershell
Invoke-RestMethod 'http://127.0.0.1:5001/sales?location=Seattle&year=2015&limit=5' | ConvertTo-Json -Depth 15
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

## Test MCP

Keep Flask running. Start the MCP server in a second terminal in this folder:

```powershell
.\.venv\Scripts\python.exe mcp_server.py
```

In a third terminal in the same folder, test discovery and invocation without AI:

```powershell
.\.venv\Scripts\python.exe demo_mcp_client.py
```

This connects to the running HTTP MCP server, lists tool names and schemas,
and calls `search_sales` with Seattle, year 2015, limit 5. It is the equivalent
of the lecture's `mcptest.py`. It does not use an AI model.

Connect a Streamable HTTP MCP host to `http://127.0.0.1:5000/mcp`. This address
speaks MCP; it is not a browser REST endpoint. Ask the connected assistant:
"Find five sales from Seattle in 2015." Tool arguments:

```json
{"location": "Seattle", "year": 2015, "limit": 5}
```

## Add Ollama (lecture pages 8 and 11)

Install the Ollama Windows application from https://ollama.com/download/windows
and open it. The Python package alone does not install the local model server.
If you installed it while terminals were open, open a new terminal so `ollama`
is on PATH. Download the model specified in the lecture:

```powershell
ollama pull qwen3:4b
```

If the app is not already serving, run `ollama serve` in a separate terminal
and leave it running. If it reports that the port is in use, the server may
already be running; check with `ollama list`.

Keep Flask and MCP running. From this project folder run:

```powershell
.\.venv\Scripts\python.exe ollama_client.py "Find three sales from Seattle in 2015. Show sale dates and purchase methods."
```

Without an argument, the script asks for a question. It discovers tools over
MCP, translates their names/descriptions/input schemas into Ollama function
definitions, lets the model choose tool calls, executes those calls through MCP,
and sends the results back to Ollama for a final answer. The model has no direct
database connection. The trace prints discovered tools, chosen arguments, and
tool status so you can compare against the deterministic demo.

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
example uses 8000, while the template and this project use 5000. Flask is 5001.

The current implementation covers the MongoDB sales path plus the Ollama
integration. Slide 11 also describes a two-database demonstration, and slide 12
has a prompt that calls both database tools. That portion would require adding
the Redis service/tool (typically port 5002); it is not implemented here.
Slide 13 asks for a procedure/code report, comparison of REST and MCP, a security
discussion, and a group presentation. Use actual results in the report; the
sample-record count does not represent total sales in a city or year.

References:

- [Atlas sample supplies schema](https://www.mongodb.com/docs/manual/sample-data/sample-supplies/)
- [MCP SDK client](https://py.sdk.modelcontextprotocol.io/client/)
- [Ollama tool calling](https://docs.ollama.com/capabilities/tool-calling)
