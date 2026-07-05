import asyncio
import uvicorn
from main import app

if __name__ == "__main__":
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)
    asyncio.run(server.serve())