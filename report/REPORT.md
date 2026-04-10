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

**Domain:** Shopee Help Center - các chính sách và hướng dẫn về trả hàng/hoàn tiền

**Tại sao nhóm chọn domain này?**
> Nhóm mình chọn domain này vì tài liệu khá rõ ràng, nhiều câu hỏi thường gặp và có cấu trúc gần giống nhau nên phù hợp để thử retrieval. Ngoài ra, nội dung của Shopee có nhiều trường hợp cụ thể như đồng kiểm, hủy đơn, hoàn tiền và phương thức trả hàng, nên dễ so sánh xem chunking và metadata có giúp ích không. Mình thấy đây là một domain thực tế, dễ đặt benchmark query và cũng dễ kiểm tra câu trả lời đúng hay sai.

### Data Inventory

| # | Tên tài liệu | Nguồn | Số ký tự | Metadata đã gán |
|---|--------------|-------|----------|-----------------|
| 1 | [SHOPEE ĐỒNG KIỂM] Tổng hợp các câu hỏi về chương trình | Shopee Help Center | 9,948 | `topic=do-kiem`, `type=faq`, `lang=vi` |
| 2 | [Hủy đơn] Thời gian nhận lại Voucher và tiền hoàn sau khi đơn hàng bị hủy | Shopee Help Center | 7,641 | `topic=huy-don`, `type=faq`, `lang=vi` |
| 3 | [Trả hàng/ Hoàn tiền] Các phương thức gửi hàng hoàn trả và phí hoàn trả | Shopee Help Center | 9,467 | `topic=phuong-thuc-tra-hang`, `type=guide`, `lang=vi` |
| 4 | [Trả hàng/Hoàn tiền] Những quy định chung về Trả hàng/Hoàn tiền của Shopee | Shopee Help Center | 9,014 | `topic=quy-dinh-tra-hang`, `type=policy`, `lang=vi` |
| 5 | CHÍNH SÁCH TRẢ HÀNG VÀ HOÀN TIỀN | Shopee Help Center | 27,287 | `topic=chinh-sach-tra-hang-hoan-tien`, `type=policy`, `lang=vi` |
| 6 | [Trả hàng/ Hoàn tiền] Thời gian nhận tiền hoàn và cách kiểm tra tiền hoàn | Shopee Help Center | 7,346 | `topic=thoi-gian-hoan-tien`, `type=guide`, `lang=vi` |

### Metadata Schema

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho retrieval? |
|----------------|------|---------------|-------------------------------|
| `topic` | string | `do-kiem`, `huy-don`, `thoi-gian-hoan-tien` | Giúp lọc đúng chủ đề khi query hỏi về một tình huống cụ thể. |
| `type` | string | `faq`, `guide`, `policy` | Giúp phân biệt tài liệu hỏi đáp, hướng dẫn, hay văn bản chính sách. |
| `lang` | string | `vi` | Giúp tránh lẫn tài liệu ngôn ngữ khác nếu sau này mở rộng dataset. |

---

## 3. Chunking Strategy — Cá nhân chọn, nhóm so sánh (15 điểm)

### Baseline Analysis

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Strategy | Chunk Count | Avg Length | Preserves Context? |
|-----------|----------|-------------|------------|-------------------|
| shopee_chinh_sach_tra_hang_hoan_tien.md | FixedSizeChunker (`fixed_size`) | 117 | 199.72 | Somewhat |
| shopee_chinh_sach_tra_hang_hoan_tien.md | SentenceChunker (`by_sentences`) | 83 | 251.84 | Yes |
| shopee_chinh_sach_tra_hang_hoan_tien.md | RecursiveChunker (`recursive`) | 157 | 118.03 | No |
| shopee_dong_kiem.md | FixedSizeChunker (`fixed_size`) | 45 | 199.62 | Somewhat |
| shopee_dong_kiem.md | SentenceChunker (`by_sentences`) | 14 | 577.29 | Yes |
| shopee_dong_kiem.md | RecursiveChunker (`recursive`) | 61 | 125.23 | No |
| shopee_phuong_thuc_tra_hang.md | FixedSizeChunker (`fixed_size`) | 42 | 199.69 | Somewhat |
| shopee_phuong_thuc_tra_hang.md | SentenceChunker (`by_sentences`) | 17 | 443.76 | Yes |
| shopee_phuong_thuc_tra_hang.md | RecursiveChunker (`recursive`) | 64 | 109.61 | No |


### Strategy Của Tôi

**Loại:** SemanticChunker

**Mô tả cách hoạt động:**
> `SemanticChunker` hoạt động bằng cách nhóm các đoạn văn liền kề lại dựa trên độ tương đồng ngữ nghĩa. Đầu tiên hàm `_build_blocks()` sẽ tách text thành các block nhỏ theo `\n\n`, rồi xử lý riêng các phần có cấu trúc như heading hay bullet list, còn đoạn nào quá dài thì pack lại theo câu. Tiếp theo chunker duyệt qua từng block, embed nó lên rồi tính cosine similarity với embedding của chunk đang giữ. Nếu similarity còn cao hơn ngưỡng 0.72 và text chưa vượt 500 ký tự thì block đó được gộp vào chunk hiện tại và embedding được cập nhật lại. Còn nếu không thì chunk đó bị đóng lại và block mới sẽ bắt đầu một chunk mới.

**Tại sao tôi chọn strategy này cho domain nhóm?**
> Tài liệu Shopee của nhóm mình toàn là FAQ với chính sách, mỗi mục thường chỉ nói về một vấn đề như hoàn tiền, đồng kiểm hay trả hàng thôi. Mình thấy `SemanticChunker` hợp hơn vì nó nhóm câu theo nghĩa thực sự chứ không chỉ đếm ký tự hay tìm dấu xuống dòng, nên chunk ra thường gọn và đúng chủ đề hơn. So với `RecursiveChunker` ra tới 157 chunk mà avg length chỉ có 118 chars — cảm giác quá vụn, retrieval dễ lấy nhầm mảnh không đủ ngữ cảnh — thì `SemanticChunker` chỉ ra 78 chunk với avg 246 chars, mình thấy cân hơn và dễ dùng hơn cho bài này.

**Code snippet:**
```python
from src import SemanticChunker

chunker = SemanticChunker(
    similarity_threshold=0.72,
    max_chunk_size=500,
)
chunks = chunker.chunk(text)
print("chunk count:", len(chunks))
```

### So Sánh: Strategy của tôi vs Baseline

| Tài liệu | Strategy | Chunk Count | Avg Length | Retrieval Quality? |
|-----------|----------|-------------|------------|--------------------|
| shopee_chinh_sach_tra_hang_hoan_tien.md | SentenceChunker (best baseline) | 83 | 251.84 | Good |
| shopee_chinh_sach_tra_hang_hoan_tien.md | **SemanticChunker (của tôi)** | **78** | **246.76** | **Better** |
| shopee_dong_kiem.md | SentenceChunker (best baseline) | 14 | 577.29 | Somewhat |
| shopee_dong_kiem.md | **SemanticChunker (của tôi)** | **40** | **194.80** | **Better** |
| shopee_phuong_thuc_tra_hang.md | SentenceChunker (best baseline) | 17 | 443.76 | Somewhat |
| shopee_phuong_thuc_tra_hang.md | **SemanticChunker (của tôi)** | **27** | **244.59** | **Better** |

> `SentenceChunker` trên `shopee_dong_kiem.md` và `shopee_phuong_thuc_tra_hang.md` sinh ra chunk rất dài (577 và 443 chars avg) vì tài liệu có nhiều câu liên tiếp về cùng một chủ đề — chunker không biết khi nào nên cắt. `SemanticChunker` xử lý tốt hơn vì nó phát hiện được khi nào ngữ nghĩa bắt đầu chuyển sang chủ đề khác và cắt đúng chỗ đó, tạo ra chunk cân bằng hơn về độ dài và tập trung hơn về nội dung.

### So Sánh Với Thành Viên Khác

| Thành viên | Strategy | Điểm | Ưu điểm | Nhược điểm |
|---|---|---|---|---|
| Hoàng Vĩnh Giang | Custom Recursive Strategy | 8 | Chunking dựa theo cấu trúc của tài liệu, đảm bảo tính toàn vẹn của thông tin đoạn văn | Với những đoạn dài chunk có thể vượt quá lượng ký tự cho phép của mô hình embedding |
| Nhữ Gia Bách | SemanticChunker | 8/10 | Chunk đúng chủ đề, score distribution rõ | Thiếu thông tin số liệu cụ thể khi chunk tách rời context |
| Trần Quang Quí | DocumentStructureChunker | 9/10 (5/5 relevant, avg score 0.628) | Chunk bám sát cấu trúc Q&A, context coherent, không bị cắt giữa điều khoản | Multi-aspect query (Q3) score thấp 0.59 vì định nghĩa và hướng dẫn nằm ở 2 chunk khác nhau |
| Đoàn Nam Sơn | Parent-Child Chunking | 9/10 (5/5 relevant, avg score 0.66) | Chunk hoạt động rất tốt, cắt đúng theo pattern Q&A, không bị cắt giữa điều khoản, rất phù hợp với tài liệu có cấu trúc rõ ràng | Với tài liệu không có cấu trúc rõ ràng thì có thể không hiệu quả |
| Vũ Đức Duy | Agentic Chunking (LLM gpt-4o-mini) | 9/10 (5/5 relevant, avg score 0.669) | Gom ngữ nghĩa cực sâu, tối ưu số lượng (chỉ tốn 54 chunks thay vì 209 chunks), không bị gãy đoạn văn. Điểm average score cao nhất. | Phải gọi API LLM tốn kém kinh phí, index siêu chậm, dễ dính lỗi parse JSON nếu document quá dài. |


**Strategy nào tốt nhất cho domain này? Tại sao?**
> Parent-Child Chunking của Đoàn Nam Sơn phù hợp nhất với domain chính sách/FAQ của Shopee vì tài liệu có cấu trúc Q&A rõ ràng, giúp chunk bám sát từng điều khoản mà không bị cắt giữa chừng. DocumentStructureChunker cũng là lựa chọn tốt, nhưng điểm yếu ở multi-aspect query cho thấy Parent-Child xử lý context tốt hơn trong trường hợp này.


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
| 1 | Tôi muốn hoàn tiền đơn hàng. | Làm sao để trả hàng và lấy lại tiền? | high | 0.6165 | ✅ |
| 2 | Đồng kiểm là kiểm tra hàng khi nhận. | Tôi có thể mở seal sản phẩm khi đồng kiểm không? | high | 0.4599 | ✅ |
| 3 | Shopee hoàn tiền trong 24 giờ. | Thời gian xử lý hoàn tiền mất bao lâu? | high | 0.3548 | ❌ |
| 4 | Hôm nay trời đẹp quá. | Tôi muốn trả hàng về cho người bán. | low | 0.3286 | ✅ |
| 5 | Phí vận chuyển được hoàn lại. | Voucher mã giảm giá có được hoàn không? | high | 0.4399 | ✅ |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn nghĩa?**
> Pair 3 bất ngờ nhất — mình nghĩ "Shopee hoàn tiền trong 24 giờ" và "Thời gian xử lý hoàn tiền mất bao lâu?" sẽ có similarity cao vì cùng hỏi về thời gian hoàn tiền, nhưng score chỉ 0.3548. Có thể vì một câu là khẳng định cụ thể còn câu kia là câu hỏi mở, khiến embedding biểu diễn chúng theo hướng khác nhau. Điều này cho thấy embeddings không chỉ nhìn vào từ khóa mà còn nhạy cảm với cấu trúc câu và intent.

---

## 6. Results — Cá nhân (10 điểm)

### Benchmark Queries & Gold Answers (nhóm thống nhất)

| # | Query | Gold Answer |
|---|-------|-------------|
| 1 | Tôi có bao nhiêu ngày để gửi yêu cầu trả hàng hoàn tiền? | 15 ngày kể từ lúc đơn hàng được cập nhật trạng thái Giao hàng thành công. |
| 2 | Tiền hoàn về ví ShopeePay mất bao lâu? | 24 giờ (với điều kiện Ví ShopeePay vẫn hoạt động bình thường). |
| 3 | Đồng kiểm là gì và tôi được làm gì khi đồng kiểm? | Kiểm tra ngoại quan và số lượng sản phẩm khi nhận hàng. Không được mở tem, dùng thử. |
| 4 | Nếu trả hàng theo hình thức tự sắp xếp, tôi có được hoàn phí vận chuyển không? | Có, Shopee hoàn lại trong 3-5 ngày làm việc (hoặc Shopee Xu với đơn ngoài Mall). |
| 5 | Mã giảm giá có được hoàn lại khi tôi trả hàng toàn bộ đơn không? | Có, mã giảm giá được hoàn nếu khiếu nại toàn bộ sản phẩm và được chấp nhận hoàn tiền. |


### Kết Quả Của Tôi

| # | Query | Top-1 Retrieved Chunk (tóm tắt) | Score | Relevant? | Agent Answer (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Tôi có bao nhiêu ngày để gửi yêu cầu trả hàng hoàn tiền? | Người mua có thể gửi yêu cầu trong vòng 15 ngày kể từ khi đơn được giao thành công | 0.6784 | Yes | 15 ngày kể từ khi đơn hàng giao thành công |
| 2 | Tiền hoàn về ví ShopeePay mất bao lâu? | Tiền hoàn được chuyển vào Ví ShopeePay, SPayLater, thẻ ngân hàng tùy trường hợp | 0.6303 | Partially | Đề cập các hình thức hoàn tiền nhưng không nói rõ thời gian |
| 3 | Đồng kiểm là gì và tôi được làm gì khi đồng kiểm? | Hướng dẫn cách thực hiện đồng kiểm | 0.6934 | Yes | Mô tả quy trình đồng kiểm |
| 4 | Nếu trả hàng theo hình thức tự sắp xếp, tôi có được hoàn phí vận chuyển không? | Tự sắp xếp phải thanh toán phí trước, được hoàn lại sau khi yêu cầu được chấp nhận | 0.6711 | Yes | Có hoàn phí vận chuyển sau khi yêu cầu được duyệt |
| 5 | Mã giảm giá có được hoàn lại khi tôi trả hàng toàn bộ đơn không? | Voucher có thể được/không được hoàn tùy quy định Shopee | 0.7258 | Yes | Có, nếu khiếu nại toàn bộ đơn và được chấp nhận |

**Bao nhiêu queries trả về chunk relevant trong top-3?** 5 / 5


---

## 7. What I Learned (5 điểm — Demo)

**Điều hay nhất tôi học được từ thành viên khác trong nhóm:**
Mình học được cách dùng Parent-Child Chunking từ Đoàn Nam Sơn. Đó là ý tưởng giữ chunk parent để làm context cho chunk child khi retrieve rất hay, giải quyết đúng điểm yếu mà SemanticChunker của mình gặp phải ở Query 2. Trước đó mình chỉ nghĩ đến việc tối ưu cách cắt chunk chứ chưa nghĩ đến việc giữ thêm context phía trên.

**Điều hay nhất tôi học được từ nhóm khác (qua demo):**
Điều mình ấn tượng nhất từ demo của nhóm khác là họ nắm rõ từng quyết định kỹ thuật của mình khi bị hỏi về edge case hay lý do chọn parameter, họ giải thích được ngay chứ không lúng túng. Điều này nhắc mình rằng hiểu sâu vấn đề quan trọng hơn làm được kết quả đẹp, vì cuối cùng vẫn phải defend được những gì mình build.

**Nếu làm lại, tôi sẽ thay đổi gì trong data strategy?**
> Nếu làm lại mình sẽ dùng real embedding model ngay từ đầu thay vì `_mock_embed`, vì kết quả retrieval với mock gần như random và không phản ánh chất lượng chunking thật sự. Ngoài ra mình sẽ thêm metadata chi tiết hơn như `subtopic` để có thể filter trước khi search, giảm noise trong kết quả. Mình cũng sẽ tách tài liệu lớn như `shopee_chinh_sach_tra_hang_hoan_tien.md` (27,287 chars) thành nhiều file nhỏ theo từng chủ đề để chunk ra coherent hơn.

---

### Failure Analysis

**Query thất bại:** Query 2 — *"Tiền hoàn về ví ShopeePay mất bao lâu?"*

**Kết quả thực tế:**
- Top-1 (score=0.6303): Đề cập các hình thức hoàn tiền (ShopeePay, SPayLater, thẻ ngân hàng) nhưng **không có thông tin về thời gian cụ thể**
- Gold answer yêu cầu: *"24 giờ"* — thông tin này không xuất hiện trong chunk nào được retrieve

**Tại sao thất bại?**

Có 3 nguyên nhân chính:

1. **Chunk coherence thấp:** Thông tin về thời gian hoàn tiền (24 giờ) và thông tin về hình thức hoàn tiền (ShopeePay, thẻ ngân hàng) nằm ở hai đoạn khác nhau trong tài liệu. `SemanticChunker` đã tách chúng ra vì similarity giữa hai đoạn không đủ cao — dẫn đến chunk retrieve được chỉ có một nửa thông tin.

2. **Metadata thiếu granularity:** Không có `subtopic=thoi-gian-hoan-tien` để filter trước, nên store phải search toàn bộ 145 chunks thay vì chỉ tìm trong nhóm tài liệu liên quan đến thời gian hoàn tiền.

3. **Query mơ hồ về intent:** Query hỏi "mất bao lâu" nhưng embedding lại match với chunk nói về "hình thức hoàn tiền" vì cả hai đều chứa từ "ShopeePay". Đây là vấn đề về precision — chunk retrieved có topic đúng nhưng không đủ grounding để trả lời câu hỏi thật sự.

**Đề xuất cải thiện:**

- Thêm `subtopic` vào metadata schema (ví dụ `subtopic=thoi-gian`, `subtopic=hinh-thuc`) để dùng `search_with_filter` thay vì search toàn bộ
- Tăng `max_chunk_size` lên 800-1000 để các thông tin liên quan không bị tách ra
- Dùng hybrid search — kết hợp keyword match ("24 giờ", "thời gian") với semantic search để tăng recall cho các query hỏi về số liệu cụ thể

---

## Tự Đánh Giá

| Tiêu chí | Loại | Điểm tự đánh giá |
|----------|------|-------------------|
| Warm-up | Cá nhân | 4.5 / 5 |
| Document selection | Nhóm | 9 / 10 |
| Chunking strategy | Nhóm | 13 / 15 |
| My approach | Cá nhân | 9 / 10 |
| Similarity predictions | Cá nhân | 4 / 5 |
| Results | Cá nhân | 8 / 10 |
| Core implementation (tests) | Cá nhân | 28 / 30 |
| Demo | Nhóm | 4 / 5 |
| **Tổng** | | **79.5 / 100** |
