import os
import json
from typing import List

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

PROXY_PORT = int(os.getenv("PROXY_PORT", "9999"))
PROXY_IP = os.getenv("PROXY_IP", "")
CRAWL4AI_ENDPOINT = os.getenv("CRAWL4AI_ENDPOINT", "http://localhost:11235/md")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CrawlRequest(BaseModel):
    urls: List[str]


@app.post("/crawl")
async def crawl(request: CrawlRequest, http_request: Request):
    client_ip = http_request.client.host if http_request.client else "unknown"
    print(f"Request to crawl {request.urls} from {client_ip}")

    ret = []

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            for url in request.urls:
                payload = {
                    "url": url,
                    "f": "fit",
                    "q": None,
                    "c": "0"
                }
                response = await client.post(CRAWL4AI_ENDPOINT, json=payload)

                if response.status_code != 200:
                    print(f"502 bad gateway for {url} :: {client_ip}")
                    raise HTTPException(status_code=502, detail="bad gateway")

                crawl_data = response.json()
                
                # Transform to Go proxy format expected by OpenWebUI
                metadata = {"source": url}
                ret.append({
                    "page_content": crawl_data.get("markdown", ""),
                    "metadata": metadata
                })

        print(f"200 :: {client_ip}")
        return ret

    except httpx.RequestError as e:
        print(f"502 bad gateway :: {client_ip} - {str(e)}")
        raise HTTPException(status_code=502, detail="bad gateway")
    except json.JSONDecodeError:
        print(f"502 bad gateway - invalid json from crawl api :: {client_ip}")
        raise HTTPException(status_code=502, detail="bad gateway - invalid json received from crawl api")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def root():
    return {
        "service": "OpenWebUI to Crawl4AI Proxy",
        "endpoints": ["/crawl", "/health"],
        "crawl4ai": CRAWL4AI_ENDPOINT,
        "proxy_port": PROXY_PORT
    }


if __name__ == "__main__":
    import uvicorn
    listen_address = f"{PROXY_IP}:{PROXY_PORT}" if PROXY_IP else f"0.0.0.0:{PROXY_PORT}"
    print(f"Listening on {listen_address}")
    uvicorn.run(app, host=PROXY_IP or "0.0.0.0", port=PROXY_PORT)
