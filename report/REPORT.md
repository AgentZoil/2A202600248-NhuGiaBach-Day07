# Báo Cáo Lab 7: Embedding & Vector Store

**Họ tên:** [Tên sinh viên]
**Nhóm:** [Tên nhóm]
**Ngày:** [Ngày nộp]

---

## 1. Warm-up (5 điểm)

### Cosine Similarity (Ex 1.1)

**High cosine similarity nghĩa là gì?**
> High cosine similarity nghĩa là hai vector đang có hướng khá giống nhau, nên nội dung mà chúng biểu diễn cũng thường gần nghĩa với nhau. Nói đơn giản thì điểm càng cao thì hai câu càng dễ nói về cùng một ý hoặc cùng một chủ đề.

**Ví dụ HIGH similarity:**
- Sentence A: "Tôi thích học machine learning."
- Sentence B: "Mình rất hứng thú với việc học về học máy."
- Tại sao tương đồng: Hai câu gần như cùng nói về sở thích học machine learning, chỉ khác cách diễn đạt.

**Ví dụ LOW similarity:**
- Sentence A: "Hôm nay trời mưa rất to."
- Sentence B: "Tôi đang nấu bữa tối trong bếp."
- Tại sao khác: Hai câu không cùng ngữ cảnh và không có ý nghĩa liên quan rõ ràng.

**Tại sao cosine similarity được ưu tiên hơn Euclidean distance cho text embeddings?**
> Với text embeddings thì mình thường quan tâm đến hướng của vector hơn là độ dài của nó. Cosine similarity đo mức độ giống nhau về hướng nên ổn hơn Euclidean distance, vì khoảng cách Euclidean có thể bị ảnh hưởng bởi magnitude của vector.

### Chunking Math (Ex 1.2)

**Document 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> Trình bày phép tính:  
> Step size = 500 - 50 = 450.  
> Số chunks = ceil((10000 - 500) / 450) + 1 = ceil(9500 / 450) + 1 = 22.
>
> Đáp án: 22 chunks.

**Nếu overlap tăng lên 100, chunk count thay đổi thế nào? Tại sao muốn overlap nhiều hơn?**
> Nếu overlap tăng lên 100 thì step size còn 400, nên số chunks sẽ tăng lên thành 25 chunks. Mình muốn overlap nhiều hơn để giữ được ngữ cảnh giữa các chunk tốt hơn, nhất là khi một ý bị cắt qua ranh giới chunk.

---

## 2. Document Selection — Nhóm (10 điểm)

### Domain & Lý Do Chọn

**Domain:** [ví dụ: Customer support FAQ, Vietnamese law, cooking recipes, ...]

**Tại sao nhóm chọn domain này?**
> *Viết 2-3 câu:*

### Data Inventory

| # | Tên tài liệu | Nguồn | Số ký tự | Metadata đã gán |
|---|--------------|-------|----------|-----------------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |
| 5 | | | | |

### Metadata Schema

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho retrieval? |
|----------------|------|---------------|-------------------------------|
| | | | |
| | | | |

---

## 3. Chunking Strategy — Cá nhân chọn, nhóm so sánh (15 điểm)

### Baseline Analysis

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Strategy | Chunk Count | Avg Length | Preserves Context? |
|-----------|----------|-------------|------------|-------------------|
| | FixedSizeChunker (`fixed_size`) | | | |
| | SentenceChunker (`by_sentences`) | | | |
| | RecursiveChunker (`recursive`) | | | |

### Strategy Của Tôi

**Loại:** [FixedSizeChunker / SentenceChunker / RecursiveChunker / custom strategy]

**Mô tả cách hoạt động:**
> *Viết 3-4 câu: strategy chunk thế nào? Dựa trên dấu hiệu gì?*

**Tại sao tôi chọn strategy này cho domain nhóm?**
> *Viết 2-3 câu: domain có pattern gì mà strategy khai thác?*

**Code snippet (nếu custom):**
```python
# Paste implementation here
```

### So Sánh: Strategy của tôi vs Baseline

| Tài liệu | Strategy | Chunk Count | Avg Length | Retrieval Quality? |
|-----------|----------|-------------|------------|--------------------|
| | best baseline | | | |
| | **của tôi** | | | |

### So Sánh Với Thành Viên Khác

| Thành viên | Strategy | Retrieval Score (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Tôi | | | | |
| [Tên] | | | | |
| [Tên] | | | | |

**Strategy nào tốt nhất cho domain này? Tại sao?**
> *Viết 2-3 câu:*

---

## 4. My Approach — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi implement các phần chính trong package `src`.

### Chunking Functions

**`SentenceChunker.chunk`** — approach:
> Mình dùng regex `(?<=[.!?])(?:\s+|\n+)` để tách câu dựa trên dấu kết thúc câu rồi split theo khoảng trắng hoặc xuống dòng phía sau. Sau đó mình `strip()` từng câu để bỏ khoảng trắng thừa, và nếu text rỗng thì trả về `[]` luôn. Với case text không tách được câu rõ ràng thì mình vẫn giữ nguyên phần text đó để không bị mất nội dung.

**`RecursiveChunker.chunk` / `_split`** — approach:
> Mình cho chunker thử từng separator theo thứ tự ưu tiên, từ đoạn lớn như `\n\n` rồi đến `\n`, `. `, space, và cuối cùng là cắt thẳng theo `chunk_size`. Nếu một đoạn vẫn còn quá dài thì nó sẽ gọi đệ quy xuống separator tiếp theo để chia nhỏ hơn. Base case là khi text đã ngắn hơn `chunk_size` hoặc không còn separator nào để thử nữa thì mình cắt theo độ dài cố định.

### EmbeddingStore

**`add_documents` + `search`** — approach:
> Mình lưu document dưới dạng record gồm `id`, `content`, `metadata` và vector embedding của content. Khi search thì mình embed query trước, rồi tính dot product với embedding của từng chunk và sắp xếp theo score giảm dần. Cách này đơn giản nhưng đủ ổn cho bài lab và chạy tốt với mock embedding.

**`search_with_filter` + `delete_document`** — approach:
> Mình filter metadata trước rồi mới search trên tập con đó, để query không bị lẫn với tài liệu ngoài nhóm điều kiện. `delete_document` thì mình xoá tất cả record có `metadata["doc_id"]` trùng với `doc_id` cần xoá, nên một document có nhiều chunk vẫn được dọn sạch hết.

### KnowledgeBaseAgent

**`answer`** — approach:
> Mình lấy top-k chunk từ store rồi ghép thành phần `Context` theo từng chunk để model dễ đọc. Prompt có phần hướng dẫn rõ là chỉ trả lời dựa trên context, nếu không thấy thông tin thì nói không biết. Sau đó mình gọi thẳng `llm_fn(prompt)` và trả về kết quả cuối cùng.

### Test Results

```
============================== 42 passed in 0.11s ==============================
```

**Số tests pass:** 42 / 42

---

## 5. Similarity Predictions — Cá nhân (5 điểm)

| Pair | Sentence A | Sentence B | Dự đoán | Actual Score | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | | | high / low | | |
| 2 | | | high / low | | |
| 3 | | | high / low | | |
| 4 | | | high / low | | |
| 5 | | | high / low | | |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn nghĩa?**
> *Viết 2-3 câu:*

---

## 6. Results — Cá nhân (10 điểm)

Chạy 5 benchmark queries của nhóm trên implementation cá nhân của bạn trong package `src`. **5 queries phải trùng với các thành viên cùng nhóm.**

### Benchmark Queries & Gold Answers (nhóm thống nhất)

| # | Query | Gold Answer |
|---|-------|-------------|
| 1 | | |
| 2 | | |
| 3 | | |
| 4 | | |
| 5 | | |

### Kết Quả Của Tôi

| # | Query | Top-1 Retrieved Chunk (tóm tắt) | Score | Relevant? | Agent Answer (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |

**Bao nhiêu queries trả về chunk relevant trong top-3?** __ / 5

---

## 7. What I Learned (5 điểm — Demo)

**Điều hay nhất tôi học được từ thành viên khác trong nhóm:**
> *Viết 2-3 câu:*

**Điều hay nhất tôi học được từ nhóm khác (qua demo):**
> *Viết 2-3 câu:*

**Nếu làm lại, tôi sẽ thay đổi gì trong data strategy?**
> *Viết 2-3 câu:*

---

## Tự Đánh Giá

| Tiêu chí | Loại | Điểm tự đánh giá |
|----------|------|-------------------|
| Warm-up | Cá nhân | / 5 |
| Document selection | Nhóm | / 10 |
| Chunking strategy | Nhóm | / 15 |
| My approach | Cá nhân | / 10 |
| Similarity predictions | Cá nhân | / 5 |
| Results | Cá nhân | / 10 |
| Core implementation (tests) | Cá nhân | / 30 |
| Demo | Nhóm | / 5 |
| **Tổng** | | **/ 100** |
