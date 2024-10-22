# Ducky

Fatduck agents

### New Agent

1. Create folder logic in `agent`
2. Add db logic in [/db/db_utils.py](/db/db_utils.py)
3. Add api endpoint in [main.py](main.py)
4. Add sdk logic in [/db/sdk.py](/db/sdk.py)
5. Add new service in railway

### Drizzle Studio

`./entrypoint studio`

### Runpod:

Better Ollama CUDA12
4 x A40s
`ssh root@XX.XX.XX.XXX -p 22XXX -i ~/.ssh/align_runpod`

Install ollama: `(curl -fsSL https://ollama.com/install.sh | sh && OLLAMA_HOST=0.0.0.0 ollama serve > ollama.log 2>&1) &`
KeepAlive: `ollama run llama3.1:70b --keepalive 1000m`

DONT FORGET OLLAMA_HOST=0.0.0.0 in above command
