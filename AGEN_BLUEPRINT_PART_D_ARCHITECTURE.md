# AGEN MASTER BLUEPRINT V1.0
## PHẦN D: SOFTWARE & SOLUTION ARCHITECTURE

### 1. KIẾN TRÚC TỔNG THỂ 7 TẦNG (7-LAYER ARCHITECTURE)
Hệ thống được thiết kế linh hoạt, đảm bảo khả năng mở rộng từ MVP lên Platform:
1. **User Ecosystem:** Student, Parent, Teacher, Admin.
2. **Access Layer:** Web (Next.js/React), Mobile (Flutter), Voice, LMS.
3. **Experience Layer:** Cung cấp trải nghiệm AI Tutor, Learning Path, Gamification & Dashboards.
4. **AGEN AI Brain:** Các Engine xử lý lõi (Adaptive Learning, NBL, Assessment, AI Teaching).
5. **Data & Intelligence:** Quản lý Learner Profile, Knowledge Base, Memory & Analytics.
6. **Integration Layer:** Tích hợp LLMs, Speech-to-Text (STT), Text-to-Speech (TTS), Payment, Notification.
7. **Infrastructure:** Hệ thống hạ tầng Cloud, Vector DB, CDN, CI/CD.

### 2. VOICE-FIRST ARCHITECTURE (KIẾN TRÚC ƯU TIÊN GIỌNG NÓI)
Kiến trúc luồng âm thanh là điểm khác biệt của AGEN, phân tách rõ ràng giữa "Hiểu ý" và "Đánh giá phát âm":
- **Luồng xử lý:** MIC -> Audio Capture -> Speech-to-Text (STT) -> Language Understanding (LLM) -> TTS -> Learner.
- Song song đó: Audio Capture -> Pronunciation Analysis / Fluency Analysis -> Coach Feedback.

### 3. TECHNICAL STACK (CÔNG NGHỆ KHUYẾN NGHỊ)
- **Frontend / Client:**
  - Web: Next.js / React
  - Mobile: Flutter (cho phép build đa nền tảng iOS/Android với hiệu năng cao).
- **Backend / API:**
  - Microservices/Modular Monolith (Giai đoạn đầu): Node.js hoặc Python (FastAPI/Django) để dễ dàng tích hợp AI.
  - Database cốt lõi: PostgreSQL.
  - Caching & Realtime: Redis.
  - Lưu trữ file (Audio/Images): Object Storage (AWS S3, Cloudflare R2).
- **AI & Data Layer:**
  - LLM: Tích hợp GPT-4, Claude hoặc Gemini (có thể fallback lẫn nhau).
  - Voice AI: Whisper (STT) và ElevenLabs / Azure TTS (TTS).
  - Vector DB (cho RAG): Pinecone, Qdrant hoặc pgvector.
- **Infrastructure:**
  - Cloud Platform: AWS hoặc Google Cloud.
  - Triển khai: Docker, Kubernetes (khi scale), CI/CD qua GitHub Actions/GitLab CI.

### 4. LOGIC TƯƠNG TÁC BACKEND API (API GATEWAY)
- API Gateway sẽ phân luồng tới các Service chuyên biệt:
  - Auth Service
  - Learner Service
  - Curriculum Service & Lesson Service
  - Assessment & Learning Service
  - Gamification & Parent Service
- AI Orchestration Layer sẽ nằm phía sau Backend, giao tiếp với các LLM và AI Models thông qua gRPC hoặc REST.
