/** Cẩm nang · bài nền tảng: luyện nói, từ vựng, phụ huynh, khung CEFR. */
import type { Article } from './articleTypes';

export const GENERAL_ARTICLES: Article[] = [
  {
    slug: 'luyen-noi-tieng-anh-mot-minh',
    category: 'giao-tiep',
    title: 'Cách luyện nói tiếng Anh một mình hiệu quả tại nhà',
    description: '7 cách luyện nói tiếng Anh một mình: shadowing, tự nói về một chủ đề, ghi âm và so sánh, sửa âm cuối, trọng âm — kèm lỗi phát âm người Việt hay mắc và lịch luyện mỗi ngày.',
    h1: 'Cách luyện nói tiếng Anh một mình hiệu quả tại nhà',
    lead: 'Không có bạn để nói cùng không phải lý do để dừng luyện nói. Phản xạ, phát âm và độ trôi chảy đều có thể luyện một mình mỗi ngày — miễn là bạn có phương pháp và có cách tự kiểm tra mình nói đúng hay sai.',
    published: '2026-10-27',
    updated: '2026-10-27',
    blocks: [
      {
        id: 'vi-sao',
        h2: 'Vì sao nhiều người học lâu vẫn ngại nói?',
        paras: [
          'Thường là do học theo hướng "hiểu" (đọc, làm bài tập) nhiều hơn hướng "dùng". Kỹ năng nói cần cơ miệng quen với âm tiếng Anh và não quen việc lấy từ ra nhanh — hai điều này chỉ đến từ việc nói thành tiếng thường xuyên, dù là nói một mình.',
        ],
      },
      {
        id: 'shadowing',
        h2: '1. Shadowing — nói đuổi theo người bản xứ',
        paras: [
          'Chọn một đoạn hội thoại hoặc podcast ngắn (30–60 giây) có phụ đề, ở trình độ bạn hiểu được khoảng 80%. Nghe một lần, sau đó vừa nghe vừa nói theo, cố bắt chước cả ngữ điệu, chỗ ngắt và nhấn giọng. Lặp lại đến khi nói trôi chảy cùng tốc độ.',
        ],
        tip: 'Đừng đổi bài quá nhanh. Nói theo một đoạn 5–7 lần đến khi thuần thục có ích hơn nghe qua mười đoạn khác nhau.',
      },
      {
        id: 'tu-noi',
        h2: '2. Tự nói 1 phút về một chủ đề',
        paras: [
          'Chọn một chủ đề quen thuộc (công việc, món ăn yêu thích, chuyến đi gần nhất), hẹn giờ 1 phút và nói liên tục, không dừng lại tra từ. Gặp từ không biết thì diễn đạt cách khác. Đây cũng chính là cách luyện IELTS Speaking Part 2.',
        ],
        bullets: [
          'Khung đơn giản: giới thiệu → 2–3 ý chính (mỗi ý có ví dụ) → kết thúc bằng cảm nghĩ.',
          'Sau khi nói, tra lại những từ bạn đã "bí" và nói lại lần hai.',
        ],
      },
      {
        id: 'ghi-am',
        h2: '3. Ghi âm và nghe lại',
        paras: [
          'Ghi âm giúp bạn nghe mình như người khác nghe: thiếu âm cuối, ngắt câu sai chỗ, "ừm… à…" quá nhiều. So sánh bản ghi với bản mẫu và ghi lại một lỗi cụ thể để sửa ở lần sau.',
        ],
      },
      {
        id: 'loi-phat-am',
        h2: '4. Sửa các lỗi phát âm người Việt hay mắc',
        table: {
          head: ['Lỗi', 'Ví dụ', 'Cách sửa'],
          rows: [
            ['Bỏ âm cuối', 'worked → "wor", likes → "lai"', 'Phát âm rõ /t/, /d/, /s/, /z/, /k/ ở cuối từ; luyện cặp từ like – likes – liked'],
            ['Âm /θ/ và /ð/', 'think → "tink", this → "dis"', 'Đặt đầu lưỡi giữa hai hàm răng rồi thổi hơi'],
            ['Nhầm /ʃ/ và /s/', 'she → "si", sea → "she"', 'Môi tròn và lưỡi lùi vào trong cho /ʃ/'],
            ['Âm dài – ngắn', 'ship / sheep, full / fool', 'Kéo dài rõ /iː/ và /uː/, âm ngắn thì gọn'],
            ['Trọng âm từ', 'phoTOgraph đọc thành PHOtograph', 'Học trọng âm cùng với từ mới, nghe và nói theo từ điển'],
          ],
        },
      },
      {
        id: 'noi-bang-tieng-anh',
        h2: '5. Nghĩ và tự nói bằng tiếng Anh trong ngày',
        paras: [
          'Mô tả việc mình đang làm ("I\'m making coffee. I need to answer three emails before lunch."), tự hỏi – tự đáp khi đi đường, đặt tên đồ vật xung quanh. Mục tiêu là giảm thói quen dịch từ tiếng Việt sang.',
        ],
      },
      {
        id: 'luyen-voi-ai',
        h2: '6. Luyện hội thoại với AI',
        paras: [
          'Trợ lý AI cho bạn một "người đối diện" không phán xét, có thể nói bất cứ lúc nào. Trong AI AGENT ENGLISH, phần Luyện nói có tình huống thực tế (gọi món, sân bay, khách sạn, phỏng vấn): bạn nghe mẫu, luyện từng câu có chấm phát âm theo từng từ, rồi nhập vai tự do với nhân vật AI và được gợi ý cách nói tự nhiên hơn.',
        ],
      },
      {
        id: 'lich-luyen',
        h2: '7. Lịch luyện nói 15 phút mỗi ngày',
        table: {
          head: ['Phút', 'Hoạt động'],
          rows: [
            ['0–5', 'Shadowing một đoạn ngắn'],
            ['5–10', 'Tự nói 1 phút về chủ đề trong ngày, ghi âm, nói lại lần hai'],
            ['10–15', 'Một tình huống nhập vai với AI hoặc luyện 5 câu có chấm phát âm'],
          ],
        },
        after: [
          'Khi đã quen, hãy tham gia nói cùng người khác: câu lạc bộ nói trong ứng dụng ghép 2–4 người theo chủ đề, có AI dẫn chuyện và sửa câu — bước chuyển tiếp tốt trước khi nói với người lạ.',
        ],
      },
    ],
    faqs: [
      { q: 'Luyện nói một mình có giúp nói với người thật tốt hơn không?', a: 'Có. Phát âm, phản xạ lấy từ và độ trôi chảy đều luyện được một mình. Khi nói với người thật, bạn có thêm kỹ năng nghe – đáp, nên hãy kết hợp dần với hội thoại nhóm.' },
      { q: 'Có cần học phiên âm IPA không?', a: 'Không bắt buộc, nhưng biết các âm khó như /θ/, /ð/, /ʃ/ và âm dài – ngắn giúp bạn tự sửa nhanh hơn khi tra từ điển.' },
    ],
    goal: 'tieng-anh-giao-tiep',
    related: ['hoc-tu-vung-nho-lau', 'cau-truc-de-thi-ielts', 'khung-cefr-la-gi'],
  },
  {
    slug: 'hoc-tu-vung-nho-lau',
    category: 'tu-vung',
    title: 'Cách học từ vựng tiếng Anh nhớ lâu: lặp lại ngắt quãng',
    description: 'Vì sao học từ vựng nhanh quên và cách nhớ lâu bằng lặp lại ngắt quãng, chủ động nhớ lại, học theo ngữ cảnh và cụm từ — kèm quy trình 5 bước mỗi ngày.',
    h1: 'Cách học từ vựng tiếng Anh nhớ lâu bằng lặp lại ngắt quãng',
    lead: 'Học 30 từ một buổi rồi một tuần sau chỉ nhớ vài từ là chuyện rất thường gặp. Vấn đề không phải trí nhớ kém, mà là cách ôn chưa đúng lúc. Lặp lại ngắt quãng giúp bạn ôn đúng thời điểm sắp quên — ít thời gian hơn mà nhớ lâu hơn.',
    published: '2026-10-27',
    updated: '2026-10-27',
    blocks: [
      {
        id: 'duong-cong-quen',
        h2: 'Vì sao học từ mới nhanh quên?',
        paras: [
          'Từ thí nghiệm của Hermann Ebbinghaus cuối thế kỷ 19, "đường cong quên" cho thấy thông tin mới giảm nhanh trong những ngày đầu nếu không được ôn lại. Mỗi lần ôn đúng lúc sắp quên, trí nhớ được củng cố và lần quên tiếp theo đến chậm hơn.',
        ],
      },
      {
        id: 'lap-lai-ngat-quang',
        h2: 'Lặp lại ngắt quãng (spaced repetition) là gì?',
        paras: [
          'Thay vì ôn tất cả từ mỗi ngày, bạn ôn mỗi từ vào các thời điểm giãn dần: ví dụ sau 1 ngày, 3 ngày, 1 tuần, 2–3 tuần… Từ bạn nhớ tốt sẽ được giãn xa hơn; từ hay quên được ôn lại sớm hơn. Nhờ vậy thời gian ôn tập trung vào đúng những từ khó.',
        ],
        table: {
          caption: 'Ví dụ lịch ôn một từ (mỗi lần nhớ đúng thì giãn khoảng cách)',
          head: ['Lần ôn', 'Sau khi học', 'Nếu quên'],
          rows: [
            ['1', '1 ngày', 'ôn lại ngay hôm sau'],
            ['2', '3 ngày', 'quay về khoảng ngắn'],
            ['3', '1 tuần', 'quay về khoảng ngắn'],
            ['4', '2–3 tuần', 'quay về khoảng ngắn'],
            ['5', '1–2 tháng', 'quay về khoảng ngắn'],
          ],
        },
      },
      {
        id: 'chu-dong-nho-lai',
        h2: 'Chủ động nhớ lại thay vì đọc lại',
        paras: [
          'Nhìn nghĩa tiếng Việt rồi tự nói ra từ tiếng Anh (hoặc ngược lại) hiệu quả hơn nhiều so với đọc lại danh sách. Việc cố gắng nhớ ra chính là lúc trí nhớ được củng cố — kể cả khi bạn nhớ sai rồi xem đáp án.',
        ],
      },
      {
        id: 'ngu-canh',
        h2: 'Học từ trong ngữ cảnh và theo cụm',
        bullets: [
          'Học cả câu ví dụ: "We need to meet the deadline." thay vì chỉ "deadline = hạn chót".',
          'Học cụm từ đi kèm (collocation): make a decision, take a break, heavy traffic.',
          'Học họ từ: decide – decision – decisive – decisively.',
          'Nói to và nghe phát âm khi học — từ nhớ được bằng cả tai và miệng sẽ dùng được khi nói.',
        ],
      },
      {
        id: 'bao-nhieu-tu',
        h2: 'Cần học bao nhiêu từ?',
        paras: [
          'Nhiều nghiên cứu về từ vựng cho thấy khoảng 2.000 họ từ thông dụng nhất chiếm phần rất lớn số từ ta gặp trong hội thoại và văn bản hằng ngày. Vì vậy, người mới nên ưu tiên nhóm từ thông dụng trước, sau đó mới mở rộng sang từ vựng học thuật (IELTS) hoặc công sở (TOEIC) theo mục tiêu.',
        ],
      },
      {
        id: 'quy-trinh',
        h2: 'Quy trình 5 bước mỗi ngày (15 phút)',
        numbered: [
          'Ôn các từ đến hạn trước (chủ động nhớ lại, nói to).',
          'Học 5–10 từ mới trong câu ví dụ, nghe phát âm.',
          'Tự đặt một câu của riêng mình với mỗi từ mới.',
          'Dùng lại 2–3 từ mới khi nói hoặc viết trong ngày.',
          'Đánh dấu từ hay quên để chúng được ôn sớm hơn.',
        ],
        after: [
          'AI AGENT ENGLISH tự làm phần lịch ôn: từ trong mỗi bài học và từ bạn lưu khi nghe podcast vào sổ từ vựng, rồi được nhắc ôn theo thuật toán lặp lại ngắt quãng. Trò chơi Blitz 60 giây giúp ôn nhanh khi bạn chỉ có một phút rảnh.',
        ],
      },
    ],
    faqs: [
      { q: 'Mỗi ngày nên học bao nhiêu từ mới?', a: 'Với đa số người học, 5–10 từ mới mỗi ngày kèm ôn tập đều đặn bền hơn là 30–50 từ một lúc rồi bỏ ôn.' },
      { q: 'Có nên ghi chép từ vựng ra sổ không?', a: 'Ghi chép giúp nhớ ban đầu, nhưng quan trọng hơn là ôn lại đúng lúc. Nếu dùng ứng dụng có lặp lại ngắt quãng, bạn không phải tự tính ngày ôn cho từng từ.' },
    ],
    goal: 'tieng-anh-giao-tiep',
    related: ['luyen-noi-tieng-anh-mot-minh', 'lo-trinh-tu-hoc-ielts', 'meo-toeic-part-5'],
  },
  {
    slug: 'day-con-hoc-tieng-anh-tai-nha',
    category: 'phu-huynh',
    title: 'Cho con học tiếng Anh tại nhà: hướng dẫn cho bố mẹ',
    description: 'Hướng dẫn bố mẹ cho con học tiếng Anh tại nhà theo từng độ tuổi: tạo thói quen 10–15 phút mỗi ngày, ưu tiên nghe – nói, khen nỗ lực, theo dõi tiến bộ — kể cả khi bố mẹ không giỏi tiếng Anh.',
    h1: 'Cho con học tiếng Anh tại nhà: hướng dẫn cho bố mẹ',
    lead: 'Bố mẹ không cần giỏi tiếng Anh để giúp con học tốt. Điều quan trọng nhất là thói quen đều đặn, môi trường khích lệ và biết con đang tiến bộ hay gặp khó ở đâu.',
    published: '2026-10-27',
    updated: '2026-10-27',
    blocks: [
      {
        id: 'nguyen-tac',
        h2: '5 nguyên tắc chung',
        numbered: [
          'Đều đặn hơn dài: 10–15 phút mỗi ngày tốt hơn 2 tiếng cuối tuần.',
          'Nghe – nói trước, đọc – viết sau, nhất là với trẻ nhỏ.',
          'Khen nỗ lực ("con nói to và rõ quá") thay vì chỉ khen kết quả.',
          'Không sửa lỗi liên tục khi con đang nói — ghi nhận rồi nói lại câu đúng một cách tự nhiên.',
          'Gắn tiếng Anh với điều con thích: bài hát, truyện, trò chơi, nhân vật yêu thích.',
        ],
      },
      {
        id: 'theo-do-tuoi',
        h2: 'Gợi ý theo độ tuổi',
        table: {
          head: ['Độ tuổi', 'Trọng tâm', 'Hoạt động gợi ý'],
          rows: [
            ['Mẫu giáo', 'Nghe, bắt chước âm, từ đơn giản', 'Bài hát, truyện tranh có tiếng, gọi tên đồ vật trong nhà'],
            ['Tiểu học', 'Từ vựng theo chủ đề, câu ngắn, phát âm', 'Bài học ngắn mỗi ngày, trò chơi ôn từ, nói câu đơn giản về bản thân'],
            ['THCS', 'Ngữ pháp, đọc hiểu, viết đoạn, nói có ý', 'Lộ trình theo trình độ, luyện nói theo tình huống, viết đoạn văn ngắn'],
          ],
        },
      },
      {
        id: 'thoi-quen',
        h2: 'Xây thói quen học mỗi ngày',
        bullets: [
          'Chọn một khung giờ cố định (ví dụ sau bữa tối) và một nơi ngồi học cố định.',
          'Dùng nhắc nhở và chuỗi ngày học để con thấy thành quả tích luỹ.',
          'Đặt mục tiêu tuần nhỏ, đạt được (ví dụ học 5 ngày/tuần) và ăn mừng khi hoàn thành.',
          'Giữ thời lượng màn hình hợp lý: học xong bài ngắn thì nghỉ.',
        ],
      },
      {
        id: 'bo-me-khong-gioi',
        h2: 'Bố mẹ không giỏi tiếng Anh thì kèm con thế nào?',
        paras: [
          'Vai trò của bố mẹ là người đồng hành, không phải giáo viên. Hãy hỏi con hôm nay học được từ gì, nhờ con "dạy lại" bố mẹ một câu — trẻ nhớ lâu hơn khi được giải thích cho người khác. Phần chuyên môn (giải thích ngữ pháp, sửa phát âm) có thể để giáo viên hoặc ứng dụng đảm nhận.',
        ],
      },
      {
        id: 'theo-doi',
        h2: 'Theo dõi tiến bộ của con',
        paras: [
          'Thay vì chỉ hỏi "hôm nay học chưa", hãy xem con học bao nhiêu buổi, độ chính xác ra sao, kỹ năng nào đang lên. Trong AI AGENT ENGLISH, phụ huynh có tài khoản riêng: nhập mã liên kết của con để nhận báo cáo tuần bằng tiếng Việt (số buổi học, phút học, kỹ năng cần hỗ trợ, gợi ý cho bố mẹ), cảnh báo khi con nghỉ học 2 ngày, và tải báo cáo PDF để in.',
          'Con học với giao diện vui nhộn có linh vật Bo, đá quý và trò chơi; bố mẹ luôn thấy giao diện gọn gàng, chuyên nghiệp.',
        ],
      },
      {
        id: 'khi-con-chan',
        h2: 'Khi con chán học',
        bullets: [
          'Giảm thời lượng, đổi sang hoạt động con thích hơn (trò chơi ôn từ, luyện nói nhập vai).',
          'Cho con chọn chủ đề bài học.',
          'Học cùng anh chị em hoặc bạn bè — thử thách nhỏ và bảng xếp hạng tuần tạo động lực.',
          'Nhìn lại mục tiêu: có thể bài đang quá khó, nên làm lại bài kiểm tra trình độ.',
        ],
      },
    ],
    faqs: [
      { q: 'Mấy tuổi nên cho con học tiếng Anh?', a: 'Trẻ có thể làm quen với âm thanh tiếng Anh từ sớm qua bài hát và truyện. Điều quan trọng hơn tuổi bắt đầu là học đều, vui và phù hợp lứa tuổi.' },
      { q: 'Mỗi ngày con nên học bao lâu?', a: 'Với trẻ tiểu học, khoảng 10–15 phút mỗi ngày là hợp lý; học sinh lớn hơn có thể 20–30 phút tuỳ mục tiêu.' },
      { q: 'Làm sao biết con có tiến bộ không?', a: 'Theo dõi đều đặn: số buổi học mỗi tuần, độ chính xác, kỹ năng nào tăng. Báo cáo tuần cho phụ huynh trong ứng dụng tổng hợp sẵn các thông tin này.' },
    ],
    goal: 'tieng-anh-cho-tre-em',
    related: ['hoc-tu-vung-nho-lau', 'luyen-noi-tieng-anh-mot-minh', 'khung-cefr-la-gi'],
  },
  {
    slug: 'khung-cefr-la-gi',
    category: 'nen-tang',
    title: 'Khung CEFR là gì? Các bậc A1–C2 và quy đổi IELTS, TOEIC',
    description: 'Khung tham chiếu CEFR gồm 6 bậc A1–C2: mỗi bậc làm được gì, tương ứng Khung năng lực ngoại ngữ 6 bậc của Việt Nam và bảng quy đổi tham khảo sang IELTS, TOEIC.',
    h1: 'Khung CEFR là gì? Các bậc A1–C2 và quy đổi IELTS, TOEIC',
    lead: 'CEFR là "thước đo chung" trình độ ngoại ngữ được dùng rộng rãi trên thế giới và là cơ sở của khung năng lực ngoại ngữ 6 bậc tại Việt Nam. Hiểu CEFR giúp bạn biết mình đang ở đâu và cần đạt gì cho mục tiêu học tập, công việc.',
    published: '2026-10-27',
    updated: '2026-10-27',
    blocks: [
      {
        id: 'cefr-la-gi',
        h2: 'CEFR là gì?',
        paras: [
          'CEFR (Common European Framework of Reference for Languages — Khung tham chiếu chung châu Âu về ngôn ngữ) do Hội đồng châu Âu xây dựng, mô tả năng lực ngôn ngữ theo 6 bậc từ A1 đến C2, bằng các mô tả "có thể làm được gì" (can-do) cho từng kỹ năng. Vì không gắn với một kỳ thi cụ thể, CEFR được dùng để so sánh nhiều chứng chỉ khác nhau.',
        ],
      },
      {
        id: 'sau-bac',
        h2: 'Sáu bậc CEFR làm được gì?',
        table: {
          head: ['Bậc', 'Tên gọi', 'Mô tả ngắn'],
          rows: [
            ['A1', 'Mới bắt đầu', 'Hiểu và dùng câu rất đơn giản về bản thân, nhu cầu cụ thể'],
            ['A2', 'Sơ cấp', 'Giao tiếp các tình huống quen thuộc: mua sắm, gia đình, công việc đơn giản'],
            ['B1', 'Trung cấp', 'Xử lý phần lớn tình huống khi đi du lịch, kể trải nghiệm, nêu lý do ngắn'],
            ['B2', 'Trung cao cấp', 'Hiểu ý chính văn bản phức tạp, giao tiếp trôi chảy với người bản xứ'],
            ['C1', 'Cao cấp', 'Dùng ngôn ngữ linh hoạt trong học thuật và công việc, diễn đạt rõ ràng, chặt chẽ'],
            ['C2', 'Thành thạo', 'Hiểu gần như mọi thứ nghe, đọc; diễn đạt chính xác cả sắc thái tinh tế'],
          ],
        },
      },
      {
        id: 'khung-viet-nam',
        h2: 'Khung năng lực ngoại ngữ 6 bậc dùng cho Việt Nam',
        paras: [
          'Việt Nam dùng Khung năng lực ngoại ngữ 6 bậc (ban hành kèm Thông tư 01/2014/TT-BGDĐT), xây dựng dựa trên CEFR: Bậc 1 tương ứng A1, Bậc 2 – A2, Bậc 3 – B1, Bậc 4 – B2, Bậc 5 – C1, Bậc 6 – C2. Nhiều trường đại học đặt chuẩn đầu ra ngoại ngữ ở Bậc 3 (B1) hoặc cao hơn tuỳ ngành.',
        ],
      },
      {
        id: 'quy-doi',
        h2: 'Quy đổi tham khảo sang IELTS và TOEIC',
        paras: [
          'Các bảng dưới chỉ mang tính tham khảo; khi nộp hồ sơ hãy xem yêu cầu cụ thể của trường hoặc đơn vị tuyển dụng.',
        ],
        table: {
          head: ['CEFR', 'IELTS (band, tham khảo)', 'TOEIC Listening + Reading (điểm tối thiểu theo ETS)'],
          rows: [
            ['A2', 'khoảng 3.0–3.5', '225 (Nghe 110 + Đọc 115)'],
            ['B1', 'khoảng 4.0–5.0', '550 (Nghe 275 + Đọc 275)'],
            ['B2', 'khoảng 5.5–6.5', '785 (Nghe 400 + Đọc 385)'],
            ['C1', 'khoảng 7.0–8.0', '945 (Nghe 490 + Đọc 455)'],
            ['C2', 'khoảng 8.5–9.0', '—'],
          ],
        },
      },
      {
        id: 'xac-dinh',
        h2: 'Làm sao biết mình đang ở bậc nào?',
        paras: [
          'Cách nhanh nhất là làm một bài kiểm tra trình độ có đủ kỹ năng. Bài kiểm tra đầu vào của AI AGENT ENGLISH mất khoảng 8–10 phút (từ vựng, ngữ pháp, đọc, nghe và một câu đọc to), xếp bạn vào bậc CEFR từ Pre-A1 trở lên, rồi tạo lộ trình học riêng theo bậc đó. Khi học, bài học tự điều chỉnh độ khó theo kết quả thực tế.',
        ],
        tip: 'Trình độ thường không đều giữa các kỹ năng: nhiều người đọc ở B1 nhưng nói mới ở A2. Hãy xem điểm từng kỹ năng để biết cần luyện gì trước.',
      },
    ],
    faqs: [
      { q: 'B1 tương đương IELTS bao nhiêu?', a: 'B1 thường được xem tương đương khoảng IELTS 4.0–5.0. Đây là mức tham chiếu chung, từng trường có thể quy định khác.' },
      { q: 'Bậc 3/6 là gì?', a: 'Là bậc 3 trong Khung năng lực ngoại ngữ 6 bậc dùng cho Việt Nam, tương ứng B1 của CEFR.' },
      { q: 'Từ A2 lên B1 mất bao lâu?', a: 'Tuỳ người học. Cambridge ước tính mỗi bậc CEFR cần khoảng 200 giờ học có hướng dẫn; học đều mỗi ngày sẽ nhanh hơn học dồn.' },
    ],
    goal: 'luyen-thi-ielts',
    related: ['cau-truc-de-thi-ielts', 'cau-truc-de-thi-toeic', 'lo-trinh-tu-hoc-ielts'],
  },
];
