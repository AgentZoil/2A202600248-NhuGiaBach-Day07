import os
import requests
from dotenv import load_dotenv
from src.chunking import compute_similarity

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

pairs = [
    ("Tôi muốn hoàn tiền đơn hàng.", "Làm sao để trả hàng và lấy lại tiền?"),
    ("Đồng kiểm là kiểm tra hàng khi nhận.", "Tôi có thể mở seal sản phẩm khi đồng kiểm không?"),
    ("Shopee hoàn tiền trong 24 giờ.", "Thời gian xử lý hoàn tiền mất bao lâu?"),
    ("Hôm nay trời đẹp quá.", "Tôi muốn trả hàng về cho người bán."),
    ("Phí vận chuyển được hoàn lại.", "Voucher mã giảm giá có được hoàn không?"),
]

print("Starting...")
for i, (a, b) in enumerate(pairs, 1):
    print(f"Running pair {i}...")
    score = compute_similarity(openrouter_embed(a), openrouter_embed(b))
    print(f"Pair {i}: {score:.4f}")

print("Done.")