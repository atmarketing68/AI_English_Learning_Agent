# AGEN MASTER BLUEPRINT V1.0
## PHẦN C: AI MULTI-AGENT ARCHITECTURE

### 1. TỔNG QUAN HỆ THỐNG MULTI-AGENT
AGEN không sử dụng một model AI (LLM) nguyên khối duy nhất để xử lý mọi yêu cầu. Thay vào đó, kiến trúc **Multi-Agent Orchestration** được áp dụng để đảm bảo tính chuyên môn hóa, độ chính xác và khả năng kiểm soát.

**Sơ đồ luồng xử lý:**
`Learner Input -> AGEN ORCHESTRATOR -> Specific Agent(s) -> Learner Output`

### 2. AGEN ORCHESTRATOR (Bộ Điều Phối Trung Tâm)
- **Nhiệm vụ:** Tiếp nhận mọi tương tác của người học, phân tích ý định (Intent Recognition) và điều phối công việc cho các Agent con phù hợp.
- **Hoạt động:** Khi người học nói "I went to school today", Orchestrator sẽ gửi Audio/Text tới *Speaking Coach* để phân tích phát âm, và *Tutor Agent* để phản hồi giao tiếp.

### 3. CÁC ĐẶC VỤ (AGENTS) CHUYÊN BIỆT
1. **Tutor Agent (Gia sư):**
   - Nhiệm vụ: Dạy kiến thức mới, giải thích ngữ pháp, từ vựng theo quy tắc "Công nhận nỗ lực -> Chỉ lỗi -> Giải thích -> Lấy ví dụ -> Yêu cầu thử lại".
2. **Coach Agent (Huấn luyện viên Kỹ năng):**
   - **Speaking Coach:** Đánh giá Pronunciation, Fluency, Grammar, Vocabulary từ Audio của học sinh (sau khi qua Speech-to-Text).
   - **Writing Coach:** Chấm điểm bài viết dựa trên Rubric (Content, Grammar, Vocabulary, Coherence, Spelling) và đưa ra gợi ý sửa lỗi thay vì chỉ chấm đúng/sai.
3. **Assessment Agent (Đánh giá):**
   - Tạo bài test, quiz, và Placement test. Chấm điểm để phân tích kỹ năng (Reading, Listening...).
4. **Curriculum Agent (Quản lý chương trình học):**
   - Đảm bảo các Agent khác không dạy "lung tung" ngoài phạm vi Curriculum đã được Knowledge Base (RAG) thiết lập.
5. **Analytics Agent (Phân tích học tập):**
   - Phân tích điểm mạnh, điểm yếu, các lỗi lặp lại (Repeated Errors) để cập nhật vào Learner Profile và tạo tiền đề cho Next Best Lesson Engine.
6. **Engagement Agent (Quản lý động lực):**
   - Điều khiển hệ thống Gamification: thưởng XP, cấp Badge, tính Streak, quản lý Missions và Challenges.
7. **Parent Agent (Trợ lý Phụ huynh):**
   - Tổng hợp dữ liệu từ Analytics Agent để sinh báo cáo tự động (Report) cho Parent Dashboard, với ngôn ngữ dễ hiểu, tích cực.

### 4. KẾT NỐI VỚI RAG (Retrieval-Augmented Generation)
Mọi Agent đều không được tự tạo kiến thức (hallucinate) mà phải truy vấn thông qua RAG vào **AGEN Knowledge Base** (chứa Khung chương trình, Từ vựng, Ngữ pháp, Tiêu chuẩn CEFR, Hướng dẫn sư phạm).
