# G2 · Chấm phát âm đến từng âm — bảng so sánh để chủ dự án quyết định

> Hạng mục 9 của G2. Chưa làm phần "đến từng âm" vì cần chọn dịch vụ trả phí (hoặc tự chạy mô hình).
> Hiện tại app đã chấm **đến từng từ** (đúng / nghe nhầm / thiếu) và gợi ý **âm khó với người Việt**
> (/θ/, âm cuối, /r/, /ʃ/…) — miễn phí, chạy ngay, dựa trên transcript của Web Speech API.

## Hiện trạng (đã có trong app)

| | |
|---|---|
| Cách làm | Trình duyệt (Chrome/Edge) nhận giọng nói → gửi **văn bản** lên server → so khớp với câu mẫu |
| Kết quả | Điểm tổng, từng từ (đúng / nghe nhầm thành gì / thiếu), mẹo âm khó cho người Việt |
| Chi phí | 0 đ |
| Hạn chế | Không "nghe" được âm thật: phát âm sai nhưng máy vẫn đoán ra đúng từ thì vẫn được tính đúng; không chấm ngữ điệu, trọng âm |
| Trình duyệt | Chrome, Edge, Safari iOS 14.5+ (Firefox không hỗ trợ) |

## Các lựa chọn để chấm đến từng âm (phoneme)

Giả định quy mô để ước tính: mỗi lượt nói ~5 giây; học viên tích cực nói 20 lượt/ngày.

| Phương án | Chấm được gì | Giá (tham khảo, cần xác nhận lại trên trang giá) | 50 học viên/ngày | 500 học viên/ngày | Việc cần làm |
|---|---|---|---|---|---|
| **Azure AI Speech – Pronunciation Assessment** | Điểm từng âm, từng từ, độ chính xác, trôi chảy, trọn vẹn, ngữ điệu (prosody) | Tính theo giờ audio của Speech-to-Text: ~1 USD/giờ; **miễn phí 5 giờ/tháng** (gói F0) | ~1,4 giờ/ngày ≈ **~40 USD/tháng** (tháng đầu gần như miễn phí) | ~14 giờ/ngày ≈ **~420 USD/tháng** | Ghi âm trên web (MediaRecorder) → upload → gọi SDK; ~2–3 ngày làm |
| **SpeechAce API** | Điểm từng âm/từ, trôi chảy, có cả bài IELTS/TOEFL | Theo gói (tính theo số lượt chấm); thường thương lượng, tầm **vài trăm USD/tháng** cho vài chục nghìn lượt | ~30.000 lượt/tháng | ~300.000 lượt/tháng | Giống Azure; cần liên hệ sales lấy giá |
| **ELSA API / Speechmatics** | Tương tự | Chỉ bán cho doanh nghiệp, giá theo hợp đồng | — | — | Liên hệ sales |
| **Tự chạy mô hình mở** (wav2vec2 phoneme / Kaldi GOP / Whisper + so khớp phoneme) | Điểm từng âm (độ chính xác thấp hơn dịch vụ thương mại; cần tinh chỉnh cho giọng Việt) | Thuê GPU nhỏ (T4): **~0,35–0,55 USD/giờ** → ~250–400 USD/tháng nếu chạy 24/7; hoặc serverless GPU trả theo giây | Giá cố định không theo số học viên | Giá cố định | 2–3 tuần: dựng pipeline, đánh giá chất lượng, vận hành; Render free không chạy được |
| **Giữ như hiện tại** (chấm theo từ) | Từng từ + mẹo âm khó | 0 đ | 0 đ | 0 đ | Đã xong |

Quy đổi: 50 học viên × 20 lượt × 5 giây = 5.000 giây ≈ 1,4 giờ audio/ngày. Azure 1 USD/giờ → ~42 USD/tháng.

## Đề xuất

1. **Pilot (hiện tại, vài chục học viên):** giữ chấm theo từ (0 đ). Đủ để học viên biết từ nào chưa rõ.
2. **Khi muốn "đến từng âm":** chọn **Azure Pronunciation Assessment** — rẻ nhất khi quy mô nhỏ, có gói miễn phí
   5 giờ/tháng để thử, tài liệu tốt, chấm cả ngữ điệu. Chi phí tăng tuyến tính theo số học viên (≈ 0,8 USD/học viên
   tích cực/tháng), nên chỉ bật cho gói Premium là hợp lý.
3. Tự chạy mô hình chỉ đáng khi vượt ~500 học viên tích cực/ngày.

## Khi chủ dự án chọn Azure, cần

- Tạo tài nguyên *Speech* trên Azure (vùng `southeastasia`), lấy `AZURE_SPEECH_KEY`, `AZURE_SPEECH_REGION` → dán vào Render.
- Mình sẽ: ghi âm trên web (MediaRecorder, 16 kHz), thêm endpoint `/speaking/pronunciation-audio`, giữ nguyên giao diện
  chấm từng từ hiện tại và thêm lớp "từng âm" bên dưới; tự động tắt (quay về chấm theo từ) khi chưa có khoá.
