#!/usr/bin/env python3
"""Startup script for HR Onboarding Agent.

Loads DEEPSEEK_API_KEY from /opt/data/.env, then starts uvicorn.
"""
import os
import sys
from pathlib import Path

# Load key from .env
env_path = Path("/opt/data/.env")
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line.startswith("DEEPSEEK_API_KEY="):
                key = line.split("=", 1)[1].strip()
                os.environ["DEEPSEEK_API_KEY"] = key
                break

if not os.environ.get("DEEPSEEK_API_KEY"):
    print("ERROR: DEEPSEEK_API_KEY not found")
    sys.exit(1)

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

import uvicorn
from app.main import app

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8700,
        log_level="info",
        reload=False,
    )
