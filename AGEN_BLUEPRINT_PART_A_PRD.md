# AGEN MASTER BLUEPRINT V1.0
## PHẦN A: PRODUCT REQUIREMENT SPECIFICATION (PRD)

### 1. TẦM NHÌN SẢN PHẨM (VISION)
**AGEN** được định vị là:
*"AI Personal English Learning Agent – người thầy, người bạn và huấn luyện viên tiếng Anh đồng hành lâu dài."*

AGEN không chỉ là một ứng dụng hỏi đáp AI. Nó là một trợ lý cá nhân hóa giúp người học Việt Nam phát triển toàn diện 4 kỹ năng (Listening – Speaking – Reading – Writing) từ nền tảng đến nâng cao thông qua sự kết hợp của:
- AI Tutor & AI Coaches
- Adaptive Learning (Học tập thích ứng)
- Gamification (Game hóa)
- Learning Analytics (Phân tích dữ liệu học tập)

Mục tiêu cốt lõi: **"Learn → Play → Practice → Speak → Create → Improve"**

### 2. ĐỐI TƯỢNG NGƯỜI DÙNG MỤC TIÊU (PERSONAS)
AGEN hướng tới 5 nhóm đối tượng (Personas) chính yếu:

1. **P1 – Tiểu học (6–10 tuổi):**
   - Hành vi: Thời gian học ngắn, dễ mất tập trung.
   - Nhu cầu/Trải nghiệm: Nhiều hình ảnh, storytelling, game, giao diện Voice-first.
2. **P2 – THCS (11–14 tuổi):**
   - Hành vi: Cần củng cố kiến thức nền và phát triển kỹ năng thực hành.
   - Nhu cầu/Trải nghiệm: Ngữ pháp + Từ vựng, giao tiếp thực tế, kỹ năng đọc hiểu, và các challenge/nhiệm vụ.
3. **P3 – THPT (15–17 tuổi):**
   - Hành vi: Có mục tiêu học tập rõ ràng (điểm số, thi cử).
   - Nhu cầu/Trải nghiệm: Academic English, kỹ năng viết (writing), giao tiếp nâng cao, luyện thi (exam preparation).
4. **P4 – Adult (Sinh viên / Người đi làm):**
   - Hành vi: Quỹ thời gian hẹp, học để ứng dụng ngay.
   - Nhu cầu/Trải nghiệm: Tiếng Anh giao tiếp ứng dụng, Workplace English.
5. **P5 – Parent (Phụ huynh):**
   - Hành vi: Muốn quản lý, theo dõi tiến độ của con mà không muốn gây áp lực.
   - Nhu cầu/Trải nghiệm: Parent Dashboard (theo dõi thời gian học, tiến bộ, mục tiêu, báo cáo và khuyến nghị từ AI).

### 3. CÁC TÍNH NĂNG CỐT LÕI (CORE FEATURES) CHO GIAI ĐOẠN MVP
Trong giai đoạn MVP (Minimum Viable Product), chúng ta tập trung vào các tính năng sau để chứng minh triết lý giáo dục của AGEN:

1. **Account & Quản lý User:**
   - Đăng nhập/Đăng ký an toàn.
   - Hỗ trợ tạo Learner Profile chi tiết.
2. **Hệ thống Placement Test:**
   - Đánh giá đầu vào 4 kỹ năng và Từ vựng, Ngữ pháp.
   - Trả ra kết quả chuẩn đoán chi tiết (Skill Diagnosis) & Gợi ý lộ trình (Personalized Roadmap).
3. **Daily Lesson & Curriculum cơ bản:**
   - Học theo lộ trình Lesson (Warm-up, Học mới, Thực hành).
4. **AI Tutor & Thực hành 4 kỹ năng cơ bản:**
   - Tính năng nhận diện và luyện Speaking (Pronunciation, Role Play cơ bản).
   - Tính năng viết và AI chấm/phản hồi lỗi Writing.
5. **Adaptive Learning & Progress Tracking:**
   - Tracking kết quả đúng/sai qua từng Activity (Learning Events).
   - Basic Gamification: Streak 7 ngày, tính điểm XP/Star.

### 4. YÊU CẦU TRẢI NGHIỆM NGƯỜI DÙNG (UX/UI REQUIREMENTS)
- **Giao diện tối giản, tập trung vào nhiệm vụ:**
  Trang chủ học viên (Learner Homepage) không biến thành LMS phức tạp mà tập trung vào "Today's Mission" và tiến độ Streak.
  *Ví dụ UX Trang chủ:*
  ```
  👋 Hi [Name]!
  🔥 7 Day Streak
  🎯 TODAY'S MISSION: "Talk about My Family"
  [ START BUTTON ]
  ---
  🎧 Listen | 🗣 Speak | 📖 Read | ✍ Write
  🏆 Progress
  ```
- **Tương tác khích lệ:** AI sửa lỗi bằng cách công nhận nỗ lực -> Chỉ lỗi -> Giải thích -> Đề nghị thử lại. Tuyệt đối không dùng phong cách Shaming/Negative.
- **Child Safety:** Đảm bảo Age-aware content, không thu thập dữ liệu nhạy cảm, không bắt buộc mật khẩu rườm rà với trẻ nhỏ.

### 5. PRODUCT & LEARNING KPIs
- **Learning KPIs:** Độ cải thiện (improvement) Vocabulary, Grammar, 4 Skills; tỷ lệ Lesson completion.
- **Engagement KPIs:** Daily/Weekly Active Users (DAU/WAU), Streak duy trì, Session frequency.
- **AI KPIs:** Response quality, Hallucination rate, Feedback accuracy.
