"""Desktop executable entry point for the bundled AGEN backend."""
import os

import uvicorn
from main import app


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=int(os.environ.get("AGEN_BACKEND_PORT", "8000")),
        log_level="info",
    )
