#!/usr/bin/env python3
import uvicorn
import os
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    # Configure uvicorn with appropriate timeouts for long-running requests
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        timeout_keep_alive=600,
        timeout_graceful_shutdown=30,
        access_log=True,
        log_level="info"
    )
