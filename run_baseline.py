import os
import requests
from pathlib import Path
from dotenv import load_dotenv
from src import ChunkingStrategyComparator

load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

def openrouter_embed(text: str) -> list[float]:
    response = requests.post(
        "https://openrouter.ai/api/v1/embeddings",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": "openai/text-embedding-3-small",
            "input": text,
        }
    )
    return response.json()["data"][0]["embedding"]

files = [
    "data/shopee_chinh_sach_tra_hang_hoan_tien.md",
    "data/shopee_dong_kiem.md",
    "data/shopee_phuong_thuc_tra_hang.md",
]

comparator = ChunkingStrategyComparator()
for file in files:
    text = Path(file).read_text(encoding="utf-8")
    result = comparator.compare(text, chunk_size=200)
    print(f"\n=== {file} ===")
    for strategy, stats in result.items():
        print(strategy, "count =", stats["count"], "avg_length =", round(stats["avg_length"], 2))