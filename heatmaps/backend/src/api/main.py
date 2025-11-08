import uvicorn
from dotenv import load_dotenv
from .config.settings import settings

load_dotenv()

if __name__ == "__main__":
    uvicorn.run(
        "routes:app",
        host="0.0.0.0",
        port=settings.port,
        reload=True
    )