from pathlib import Path
from src import SemanticChunker

text = Path("data/shopee_chinh_sach_tra_hang_hoan_tien.md").read_text(encoding="utf-8")
chunker = SemanticChunker(similarity_threshold=0.72, max_chunk_size=500)
chunks = chunker.chunk(text)
print("chunk count:", len(chunks))
for i, chunk in enumerate(chunks[:8], 1):
    print(f"\n--- chunk {i} ({len(chunk)} chars) ---")
    print(chunk[:600])
