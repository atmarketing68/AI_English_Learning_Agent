# AGEN MASTER BLUEPRINT V1.0
## PHẦN F: MVP BACKLOG, USER STORIES & SPRINT PLAN

### 1. MỤC TIÊU CỦA MVP (PHASE 1)
**Thời gian dự kiến:** 3–4 tháng.
**Mục tiêu chính:** Chứng minh AGEN có thể giúp một learner học tiếng Anh hiệu quả hơn thông qua lộ trình cá nhân hóa và AI Tutor cơ bản, vượt trội hơn so với một chatbot thông thường. 
*Chưa tập trung vào các tính năng nâng cao như Family Mode, Teacher LMS, hay hệ thống payment phức tạp.*

### 2. EPIC & BACKLOG (TÍNH NĂNG CHÍNH)
1. **Epic 1: User & Learner Management**
   - Đăng ký/Đăng nhập qua Email/Google/Apple.
   - Luồng Onboarding & Tạo Learner Profile (Thu thập tên, tuổi, sở thích, mục tiêu).
2. **Epic 2: Placement & Diagnosis**
   - Bài test đầu vào (Gamified Placement Test).
   - Đánh giá level (Pre-A1 đến B2) và sinh Personalized Roadmap.
3. **Epic 3: Daily Learning Flow (Luồng học tập hàng ngày)**
   - Learner Dashboard hiển thị "Today's Mission".
   - Luồng 1 Lesson chuẩn (Warm-up, Học từ vựng, Luyện câu, Review).
4. **Epic 4: AI Tutor & 4-Skill Practice (Cơ bản)**
   - AI Tutor giải thích ngữ pháp/từ vựng.
   - Speaking cơ bản: Audio Capture, Chuyển Text (STT), chấm điểm Fluency/Pronunciation đơn giản.
   - Writing cơ bản: Nộp text, AI review lỗi, giải thích lỗi, cho phép viết lại.
5. **Epic 5: Basic Gamification & Progress**
   - Lưu trữ lịch sử (Learning History).
   - Tích điểm XP, hiển thị Streak 7 ngày.
   - Bảng hiển thị kỹ năng hiện tại (Radar chart cho 4 kỹ năng).

### 3. USER STORIES (MẪU)
- *Là một Học sinh (P2), tôi muốn làm một bài test đầu vào giống như chơi game để hệ thống biết tôi đang ở trình độ nào mà không bị áp lực.*
- *Là một Học sinh (P1), tôi muốn được nghe AI nói mẫu và ghi âm lại giọng của tôi để tôi biết mình phát âm đúng hay sai.*
- *Là một Học sinh (P3), tôi muốn khi tôi viết sai ngữ pháp, AI không chỉ gạch bỏ mà phải giải thích tại sao sai và gợi ý tôi viết lại câu tốt hơn.*

### 4. SPRINT PLAN KHUYẾN NGHỊ (GIAI ĐOẠN MVP)
Dự án được chia thành các Sprint (mỗi Sprint 2 tuần):
- **Sprint 1-2 (Foundation):** Setup hạ tầng Backend (Node.js/Python, PostgreSQL), API Gateway, User Auth, định nghĩa DB Schema cho Learner Profile và LearningEvent.
- **Sprint 3-4 (Curriculum & Placement):** Xây dựng hệ thống lưu trữ Curriculum (Knowledge Base) và phát triển thuật toán Placement Test.
- **Sprint 5-6 (AI Integration & Daily Flow):** Tích hợp LLM (Agent Orchestrator cơ bản), STT/TTS; xây dựng Frontend Daily Lesson Flow.
- **Sprint 7 (4-Skill Practice):** Hoàn thiện luồng học Nghe - Nói - Đọc - Viết. Kết nối AI Tutor và Coach Agent.
- **Sprint 8 (Gamification & QA):** Tích hợp XP, Streak. Kiểm thử toàn hệ thống (UAT), fix bugs và đo lường độ chính xác (AI Evaluation Framework).
