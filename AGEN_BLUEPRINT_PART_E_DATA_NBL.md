# AGEN MASTER BLUEPRINT V1.0
## PHẦN E: DATA, RAG, ADAPTIVE LEARNING & NBL ARCHITECTURE

### 1. DATA MODEL CỐT LÕI (LEARNER DIGITAL TWIN)
Dữ liệu của học viên (Learner Profile) không chỉ là tên, tuổi, lớp mà là một bản sao kỹ thuật số (Digital Twin) học tập, bao gồm:
- **Identity:** Tuổi, Khối lớp, Sở thích (Preferences).
- **Language Profile:** Điểm số chi tiết 4 kỹ năng (Nghe, Nói, Đọc, Viết) + Từ vựng + Ngữ pháp.
- **Behavior:** Tần suất học, Thời lượng session, Tốc độ phản hồi (Response time), Engagement & Streak.
- **Learning Intelligence:** Điểm mạnh, Điểm yếu, Các mẫu lỗi lặp lại (Error patterns), Lỗ hổng kiến thức.

### 2. LEARNING EVENT (ĐƠN VỊ DỮ LIỆU CƠ SỞ)
Mọi tương tác của học viên đều sinh ra một `LearningEvent` lưu trữ trong DB.
**Ví dụ JSON của một Learning Event:**
```json
{
  "learner_id": "L001",
  "lesson_id": "A1-U01-L03",
  "skill": "speaking",
  "activity": "role_play",
  "difficulty": 2,
  "correct": false,
  "error_type": "grammar",
  "response_time": 8.4,
  "confidence": 0.62
}
```
Từ hàng triệu LearningEvent này, hệ thống sẽ phân tích để xây dựng Learning Intelligence (Tài sản "Golden Data" của hệ thống).

### 3. ADAPTIVE LEARNING ENGINE (ĐỘNG CƠ HỌC TẬP THÍCH ỨNG)
Sau mỗi câu trả lời của người học, hệ thống phân tích `LearningEvent` và ra quyết định ngay lập tức:
- **KEEP LEVEL:** Giữ nguyên độ khó nếu học viên trả lời ổn định.
- **INCREASE:** Tăng độ khó nếu học viên làm đúng liên tiếp nhanh và tự tin.
- **DECREASE:** Giảm độ khó nếu học viên làm sai liên tục.
- **REVIEW:** Bật chế độ ôn tập Spaced Repetition (Lặp lại ngắt quãng).
- **RETEACH:** Chuyển về Tutor Agent giảng lại lý thuyết (nếu sai cơ bản).
- **CHANGE ACTIVITY:** Đổi dạng bài tập để chống chán nản.

### 4. NEXT BEST LESSON ENGINE (TRÁI TIM THÔNG MINH)
AGEN không hỏi "Hôm nay bạn muốn học gì?", mà hệ thống tự động tính toán và đề xuất **"Next Mission"** mang lại giá trị học tập cao nhất.

**Công thức Scoring tham khảo:**
`NextLessonScore = SkillGap + ErrorFrequency + GoalRelevance + Prerequisite + ForgettingRisk + EngagementFit + DifficultyFit`

*Ví dụ:* Nếu học viên sai thì Quá khứ đơn (Past tense) nhiều lần trong các bài Speaking trước, NBL Engine sẽ điều hướng buổi học tiếp theo thành "Past Tense Adventure".

### 5. RAG KNOWLEDGE BASE
Đây là cơ sở dữ liệu tri thức tĩnh (Static Knowledge) làm đầu vào cho LLM, giúp LLM không bị hallucinate. Bao gồm:
- Curriculum (Chương trình) & Lesson Blueprints.
- Vocabulary / Grammar databases.
- Rubrics (Tiêu chí chấm điểm).
- CEFR Descriptors & Teaching Methodology (Sư phạm).
- Common mistakes (Các lỗi người Việt hay mắc phải).
