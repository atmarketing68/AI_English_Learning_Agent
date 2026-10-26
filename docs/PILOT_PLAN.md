# AGEN Pilot Contract

## Mục tiêu

Kiểm chứng trong 4 tuần rằng AGEN giúp người Việt trình độ A1-B1 duy trì việc học
10-15 phút mỗi ngày và cải thiện speaking/writing qua feedback có thể hành động.

## Phân khúc ban đầu

- Người học 15-30 tuổi.
- Trình độ đầu vào PRE-A1 đến B1.
- Dùng trình duyệt trên laptop/desktop.
- Mục tiêu: giao tiếp hằng ngày hoặc tiếng Anh học tập/công việc cơ bản.

Trẻ dưới 15 tuổi, phụ huynh và chương trình giáo viên nằm ngoài phạm vi pilot này.
Không dùng kết quả pilot này để kết luận cho các nhóm đó.

## Giả thuyết cần kiểm chứng

> Nếu người học nhận được một nhiệm vụ cá nhân hóa ngắn mỗi ngày và feedback speaking/writing
> rõ ràng, ít nhất 35% người đã hoàn thành placement sẽ quay lại học trong ngày thứ 7.

## Chỉ số và ngưỡng thành công

| Nhóm | Chỉ số | Ngưỡng pilot |
|---|---|---:|
| Activation | Hoàn thành placement / đăng ký | >= 60% |
| First value | Hoàn thành lesson đầu tiên / placement | >= 70% |
| Retention | Người dùng quay lại ngày 7 / placement | >= 35% |
| Habit | Người dùng có >= 3 ngày học trong tuần | >= 40% |
| Learning | Điểm bài kiểm tra cuối tuần so với đầu tuần | tăng >= 10 điểm phần trăm |
| AI quality | Agent trace không bị flag | >= 95% |
| Reliability | Lesson generation thành công | >= 98% |
| Cost | Chi phí AI trên learner hoạt động mỗi tuần | ghi nhận, chưa đặt ngưỡng |

## Event cần ghi nhận

Các event này đã có trong `LearningEvent` hoặc `AgentTrace`; không tạo thêm tracking
framework trong pilot:

- `registration_completed`
- `placement_done`
- `lesson_started`
- `exercise_answered`
- `lesson_completed`
- `speaking_practice`
- `writing_submitted`
- `streak`
- Agent trace: latency, status, eval score, eval flags

Mỗi event nên có `learner_id`, `recorded_at`, `skill`, `score`, `duration_seconds` và
`extra_data` phù hợp. Không lưu API key, raw audio hoặc nội dung nhạy cảm không cần thiết.

## Không làm trong pilot

- Không mở rộng thêm persona hoặc level mới chỉ vì có yêu cầu riêng lẻ.
- Không quảng bá transcript matching là chấm phát âm phoneme-level.
- Không thu tiền thật khi billing vẫn là pilot/mock.
- Không cho learner tự cấu hình provider key.

## Quyết định sau 4 tuần

- Đạt activation, retention và learning: tiếp tục tối ưu retention/cost.
- Đạt engagement nhưng không đạt learning: sửa curriculum, rubric và feedback trước khi mở rộng.
- Đạt learning nhưng không đạt retention: rút ngắn session, cải thiện mission và onboarding.
- Không đạt cả hai: dừng mở rộng tính năng, phỏng vấn người học và xem lại phân khúc.