from pathlib import Path
import requests
from src.agent import KnowledgeBaseAgent
from src.store import EmbeddingStore
from src.models import Document
from src import SemanticChunker
from dotenv import load_dotenv
import os

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
    data = response.json()
    return data["data"][0]["embedding"]

files = [
    "data/shopee_chinh_sach_tra_hang_hoan_tien.md",
    "data/shopee_dong_kiem.md",
    "data/shopee_phuong_thuc_tra_hang.md",
]

queries = [
    "Tôi có bao nhiêu ngày để gửi yêu cầu trả hàng hoàn tiền?",
    "Tiền hoàn về ví ShopeePay mất bao lâu?",
    "Đồng kiểm là gì và tôi được làm gì khi đồng kiểm?",
    "Nếu trả hàng theo hình thức tự sắp xếp, tôi có được hoàn phí vận chuyển không?",
    "Mã giảm giá có được hoàn lại khi tôi trả hàng toàn bộ đơn không?",
]

chunker = SemanticChunker(similarity_threshold=0.72, max_chunk_size=500)
store = EmbeddingStore(collection_name="shopee_bench", embedding_fn=openrouter_embed)

for file in files:
    text = Path(file).read_text(encoding="utf-8")
    chunks = chunker.chunk(text)
    docs = [
        Document(
            id=f"{Path(file).stem}_{i}",
            content=chunk,
            metadata={"source": file},
        )
        for i, chunk in enumerate(chunks)
    ]
    store.add_documents(docs)
    print(f"Added {len(docs)} chunks from {file}")

def demo_llm(prompt):
    return "[demo]"

agent = KnowledgeBaseAgent(store=store, llm_fn=demo_llm)

for i, query in enumerate(queries, 1):
    print(f"\n{'='*60}")
    print(f"Query {i}: {query}")
    results = store.search(query, top_k=3)
    for j, r in enumerate(results, 1):
        print(f"  Top-{j} score={r['score']:.4f}: {r['content'][:200]}")