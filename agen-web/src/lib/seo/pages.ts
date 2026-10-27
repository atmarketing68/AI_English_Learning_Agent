/**
 * SEO · Nội dung các trang công khai theo mục tiêu học (server-rendered, có trong sitemap).
 * Chỉ mô tả tính năng đang có trong app — không ghi số liệu người dùng, đánh giá hay giá cụ thể
 * (những phần đó chủ dự án quyết định trên landing).
 */
export type SeoIcon = 'ielts' | 'toeic' | 'kids' | 'talk' | 'class';

export interface SeoPage {
  slug: string;
  icon: SeoIcon;
  cardTitle: string;
  cardDesc: string;
  title: string;            // <title> (template adds "· AI AGENT ENGLISH")
  description: string;      // meta description, ~150–160 ký tự
  h1: string;
  lead: string;
  eyebrow: string;
  highlights: { title: string; desc: string }[];
  sections: { h2: string; body: string[]; bullets?: string[] }[];
  steps: { title: string; desc: string }[];
  faqs: { q: string; a: string }[];
  cta: { title: string; desc: string; label: string; href: string };
  related: string[];
}

export const SEO_PAGES: SeoPage[] = [
  {
    slug: 'luyen-thi-ielts',
    icon: 'ielts',
    cardTitle: 'Luyện thi IELTS',
    cardDesc: 'Thi thử 4 kỹ năng, chấm band Writing/Speaking, kế hoạch ôn theo ngày thi.',
    title: 'Luyện thi IELTS online với AI – thi thử & chấm band',
    description: 'Luyện thi IELTS online với AI: thi thử Listening, Reading, Speaking có giám khảo AI, chấm Writing theo 4 tiêu chí band và kế hoạch ôn theo ngày thi. Học thử miễn phí.',
    eyebrow: 'IELTS · Listening · Reading · Writing · Speaking',
    h1: 'Luyện thi IELTS online với AI',
    lead: 'Làm đề thi thử đúng định dạng, nhận band ước tính ngay sau khi nộp, được AI chấm Writing và Speaking theo bốn tiêu chí chính thức — rồi ôn đúng phần còn yếu theo kế hoạch tính ngược từ ngày thi của bạn.',
    highlights: [
      { title: 'Thi thử Listening & Reading', desc: 'Mini test đúng dạng đề thật: điền form, trắc nghiệm, True/False/Not Given, hoàn thành câu. Có đồng hồ, phần nghe phát một lần.' },
      { title: 'Speaking với giám khảo AI', desc: 'Part 1, Part 2 (cue card: 1 phút chuẩn bị, nói đến 2 phút) và Part 3. Trả lời bằng micro, nhận band theo 4 tiêu chí.' },
      { title: 'Chấm Writing Task 1 & Task 2', desc: 'Band theo Task Response, Coherence & Cohesion, Lexical Resource, Grammatical Range & Accuracy, kèm lỗi và câu sửa.' },
      { title: 'Kế hoạch ôn theo ngày thi', desc: 'Nhập band mục tiêu và ngày thi, app chia lộ trình theo tuần, ưu tiên kỹ năng đang thấp nhất.' },
    ],
    sections: [
      {
        h2: 'Thi thử IELTS Listening và Reading có band ước tính',
        body: [
          'Mỗi đề là một bài thi rút gọn giữ nguyên dạng câu hỏi của IELTS: Section 1 điền thông tin, Section 2–3 trắc nghiệm với hội thoại và bài nói học thuật; phần Reading có bài đọc học thuật với câu hỏi True/False/Not Given, hoàn thành câu và trắc nghiệm.',
          'Nộp bài là có ngay số câu đúng, band ước tính theo bảng quy đổi và lời giải tiếng Việt cho từng câu, chỉ rõ đáp án nằm ở đâu trong bài nghe hoặc bài đọc. Kho đề được bổ sung dần, mỗi đề mới đều được người duyệt kiểm tra đáp án trước khi phát hành.',
        ],
        bullets: ['Giọng đọc tự nhiên, phát một lần như thi thật', 'Lời giải từng câu bằng tiếng Việt', 'Lịch sử điểm để thấy mình tiến bộ qua từng đề'],
      },
      {
        h2: 'Luyện IELTS Speaking với giám khảo AI',
        body: [
          'Giám khảo AI đọc câu hỏi, đếm giờ chuẩn bị và giờ nói giống phòng thi. Bạn trả lời bằng micro; khi nộp, AI đánh giá theo Fluency & Coherence, Lexical Resource, Grammatical Range & Accuracy và Pronunciation, nhận xét từng phần và đưa ra câu nói tự nhiên hơn để bạn nghe lại.',
          'Ngoài đề thi thử, phần Luyện nói có các tình huống nhập vai và chấm phát âm theo từng từ, giúp bạn luyện phản xạ trước khi vào Part 2 và Part 3.',
        ],
      },
      {
        h2: 'Chấm IELTS Writing theo 4 tiêu chí',
        body: [
          'Viết Task 1 (mô tả biểu đồ) hoặc Task 2 (nghị luận) ngay trong app. AI trả về band từng tiêu chí, band tổng làm tròn theo quy tắc IELTS, danh sách lỗi ngữ pháp kèm giải thích tiếng Việt, bài viết đã sửa và gợi ý để lên nửa band tiếp theo.',
          'Nếu bạn học trong lớp có giáo viên dùng AI AGENT ENGLISH, giáo viên có thể chấm lại theo rubric 4 tiêu chí và theo dõi biểu đồ tiến bộ band của bạn qua từng bài.',
        ],
      },
      {
        h2: 'Lộ trình IELTS và kế hoạch ôn thi cá nhân',
        body: [
          'Lộ trình mục tiêu IELTS gồm các chặng từ vựng học thuật, ngữ pháp band 6+ và luyện Reading/Listening theo dạng đề. Kế hoạch ôn thi lấy điểm hiện tại từ các bài thi thử và bài viết, so với band mục tiêu và số tuần còn lại, rồi đặt chỉ tiêu mỗi tuần: bao nhiêu bài học, đề thi thử, bài viết và lượt luyện nói.',
          'Khi gặp điểm ngữ pháp chưa chắc, bạn hỏi trợ lý Bo bằng tiếng Việt và nhận giải thích kèm ví dụ nghe được.',
        ],
      },
    ],
    steps: [
      { title: 'Kiểm tra trình độ', desc: 'Bài kiểm tra đầu vào khoảng 8–10 phút xếp trình độ theo CEFR.' },
      { title: 'Chọn mục tiêu IELTS', desc: 'Nhập band mong muốn và ngày thi để có kế hoạch theo tuần.' },
      { title: 'Thi thử và sửa lỗi', desc: 'Làm đề, đọc lời giải, luyện lại đúng phần còn yếu.' },
    ],
    faqs: [
      { q: 'Band ước tính trên app có giống điểm thi thật không?', a: 'Band là ước tính để theo dõi tiến bộ, dựa trên bảng quy đổi chính thức cho Listening/Reading và tiêu chí chấm công khai cho Writing/Speaking. Điểm thi thật có thể chênh lệch; hãy dùng band trên app để biết mình đang tiến hay lùi và phần nào cần luyện thêm.' },
      { q: 'Luyện IELTS Speaking với AI cần thiết bị gì?', a: 'Chỉ cần điện thoại hoặc máy tính có micro và trình duyệt Chrome, Edge hoặc Safari. Bạn cho phép trang dùng micro khi được hỏi là có thể bắt đầu.' },
      { q: 'Tài khoản miễn phí thi thử được bao nhiêu đề?', a: 'Tài khoản miễn phí làm được một đề thi thử Listening/Reading và một lượt thi thử Speaking mỗi ngày. Gói Premium thi không giới hạn.' },
      { q: 'App có chấm IELTS Writing Task 1 không?', a: 'Có. Bạn chọn dạng IELTS Task 1 hoặc Task 2 khi luyện viết; AI chấm band theo 4 tiêu chí, chỉ lỗi và gợi ý cách viết tốt hơn.' },
    ],
    cta: { title: 'Bắt đầu luyện IELTS hôm nay', desc: 'Kiểm tra trình độ miễn phí, nhận kế hoạch ôn thi theo band mục tiêu.', label: 'Học thử miễn phí', href: '/register' },
    related: ['luyen-thi-toeic', 'tieng-anh-giao-tiep', 'lop-hoc-va-doanh-nghiep'],
  },
  {
    slug: 'luyen-thi-toeic',
    icon: 'toeic',
    cardTitle: 'Luyện thi TOEIC',
    cardDesc: 'Đề Listening & Reading theo Part, Speaking & Writing có chấm điểm.',
    title: 'Luyện thi TOEIC online với AI – đủ 4 kỹ năng',
    description: 'Luyện thi TOEIC online: đề thi thử Listening Part 2–4, Reading Part 5–7, TOEIC Speaking và Writing được AI chấm điểm, từ vựng công sở và lộ trình theo mục tiêu.',
    eyebrow: 'TOEIC · Listening & Reading · Speaking & Writing',
    h1: 'Luyện thi TOEIC online với AI',
    lead: 'Luyện đúng từng Part của đề TOEIC với bối cảnh công sở, xem điểm ước tính ngay khi nộp bài và để AI chấm phần Speaking, Writing — học ngắn mỗi ngày, hợp với người đi làm.',
    highlights: [
      { title: 'Listening Part 2–4', desc: 'Hỏi – đáp, hội thoại và bài nói ngắn với giọng đọc tự nhiên, phát một lần như thi thật.' },
      { title: 'Reading Part 5–7', desc: 'Điền câu, điền đoạn văn và đọc hiểu email, thông báo — lời giải tiếng Việt từng câu.' },
      { title: 'TOEIC Speaking', desc: 'Đọc to đoạn văn có chấm phát âm, trả lời câu hỏi và nêu ý kiến; điểm ước tính thang 0–200.' },
      { title: 'TOEIC Writing', desc: 'Viết email và bài luận ý kiến, nhận điểm ước tính thang 0–200 và danh sách lỗi cần sửa.' },
    ],
    sections: [
      {
        h2: 'Đề thi thử TOEIC Listening & Reading theo từng Part',
        body: [
          'Đề Listening gồm Part 2 (chọn câu đáp phù hợp), Part 3 (hội thoại) và Part 4 (bài nói ngắn như thông báo, tin nhắn thoại). Đề Reading gồm Part 5 (điền câu: thì, giới từ, loại từ, liên từ), Part 6 (điền đoạn văn) và Part 7 (đọc hiểu một hoặc hai văn bản liên quan).',
          'Sau khi nộp, bạn thấy số câu đúng từng phần, điểm ước tính theo thang của từng kỹ năng và giải thích vì sao đáp án đúng — giúp nhận ra bẫy thường gặp như từ đồng âm ở Part 2 hay loại từ ở Part 5.',
        ],
      },
      {
        h2: 'TOEIC Speaking và Writing có chấm điểm',
        body: [
          'Phần thi nói mô phỏng Q1–2 đọc to (chấm độ chính xác phát âm theo từng từ), Q5–7 trả lời câu hỏi nhanh và Q11 nêu ý kiến có lý do. AI đánh giá phát âm, ngữ điệu, ngữ pháp, từ vựng, mạch lạc và nội dung, rồi quy ra điểm ước tính.',
          'Phần viết có dạng email phản hồi và bài luận nêu ý kiến. AI chấm theo mức độ hoàn thành yêu cầu, bố cục, từ vựng và ngữ pháp, kèm bài đã sửa để bạn học cách diễn đạt trong môi trường công việc.',
        ],
      },
      {
        h2: 'Từ vựng công sở và lộ trình TOEIC',
        body: [
          'Lộ trình mục tiêu TOEIC đi qua từ vựng công sở, ngữ pháp Part 5 & 6 và luyện Reading/Listening Part 3–7. Từ mới được đưa vào ôn tập ngắt quãng để nhớ lâu; mỗi ngày bạn chỉ cần 10–15 phút.',
        ],
        bullets: ['Ôn tập ngắt quãng tự nhắc đúng lúc sắp quên', 'Bài học tạo theo đúng trình độ của bạn', 'Nhắc học hằng ngày qua thông báo hoặc email'],
      },
    ],
    steps: [
      { title: 'Kiểm tra trình độ', desc: 'Biết mình đang ở đâu trước khi chọn mục tiêu điểm.' },
      { title: 'Học theo lộ trình TOEIC', desc: 'Từ vựng, ngữ pháp và luyện đề theo Part.' },
      { title: 'Thi thử định kỳ', desc: 'Xem điểm ước tính tăng dần và tập trung vào Part yếu.' },
    ],
    faqs: [
      { q: 'Điểm TOEIC ước tính được tính thế nào?', a: 'Listening và Reading quy đổi từ tỉ lệ câu đúng của đề thi thử; Speaking và Writing dựa trên tiêu chí chấm công khai của bài thi. Đây là ước tính để theo dõi tiến bộ, không thay thế điểm thi chính thức.' },
      { q: 'Người đi làm bận có theo được không?', a: 'Được. Bạn chọn 5, 10, 15 hoặc 30 phút mỗi ngày; bài học được chia nhỏ, có thể học trên điện thoại trong giờ nghỉ.' },
      { q: 'Có luyện phỏng vấn tiếng Anh không?', a: 'Có lộ trình mục tiêu phỏng vấn xin việc, gồm phần nền tảng và kể chuyện theo cấu trúc STAR, cùng tình huống nhập vai phỏng vấn trong phần Luyện nói.' },
    ],
    cta: { title: 'Luyện TOEIC mỗi ngày 15 phút', desc: 'Làm bài kiểm tra trình độ miễn phí và bắt đầu lộ trình TOEIC.', label: 'Bắt đầu miễn phí', href: '/register' },
    related: ['luyen-thi-ielts', 'tieng-anh-giao-tiep', 'lop-hoc-va-doanh-nghiep'],
  },
  {
    slug: 'tieng-anh-cho-tre-em',
    icon: 'kids',
    cardTitle: 'Tiếng Anh cho trẻ em',
    cardDesc: 'Giao diện vui nhộn cùng Bo, báo cáo tuần cho phụ huynh.',
    title: 'Tiếng Anh cho trẻ em với AI – học vui, bố mẹ theo dõi',
    description: 'Ứng dụng tiếng Anh cho trẻ em: bài học ngắn theo trình độ, luyện nói với AI, linh vật Bo, trò chơi ôn từ 60 giây và báo cáo tuần, cảnh báo nghỉ học cho phụ huynh.',
    eyebrow: 'Học sinh tiểu học & THCS · Phụ huynh',
    h1: 'Tiếng Anh cho trẻ em: học vui mỗi ngày cùng AI',
    lead: 'Con học bài ngắn vừa sức với giao diện vui nhộn và bạn đồng hành Bo; bố mẹ nhận báo cáo tuần dễ hiểu, biết con tiến bộ gì và cần hỗ trợ ở đâu — không cần giỏi tiếng Anh vẫn kèm được con.',
    highlights: [
      { title: 'Giao diện riêng cho bé', desc: 'Màu sắc tươi, linh vật Bo động viên và nói tiếng Việt, đá quý, cửa hàng trang phục cho nhân vật.' },
      { title: 'Luyện nói không ngại', desc: 'Con nói vào micro, AI sửa câu nhẹ nhàng và chấm phát âm theo từng từ.' },
      { title: 'Ôn từ bằng trò chơi', desc: 'Blitz 60 giây, chuỗi ngày học, nhiệm vụ hằng ngày và giải đấu tuần giữ thói quen.' },
      { title: 'Phụ huynh nắm rõ', desc: 'Báo cáo tuần, cảnh báo khi con nghỉ học 2 ngày, báo cáo PDF để in.' },
    ],
    sections: [
      {
        h2: 'Bài học ngắn, đúng trình độ của con',
        body: [
          'Sau bài kiểm tra đầu vào, mỗi bài học được tạo riêng theo trình độ CEFR của con (từ Pre-A1) với đủ nghe, nói, đọc, viết. Bài dài vài phút nên con không bị quá tải; độ khó tự điều chỉnh theo kết quả thật.',
          'Từ đã học được đưa vào ôn tập ngắt quãng — app nhắc ôn đúng lúc con sắp quên, nên từ vựng được nhớ lâu thay vì học trước quên sau.',
        ],
      },
      {
        h2: 'Động lực học mỗi ngày',
        body: [
          'Con nhận XP, đá quý và giữ chuỗi ngày học; hoàn thành nhiệm vụ ngày và mục tiêu tuần để được thưởng. Trò chơi Blitz 60 giây ôn từ vựng nhanh, giải đấu tuần cho con thi đua vui với các bạn cùng nhóm.',
          'Bo — linh vật của app — khen khi con làm tốt, gợi ý khi con sai và đọc lời nhắn bằng tiếng Việt cho các bé chưa đọc tốt.',
        ],
      },
      {
        h2: 'Dành cho phụ huynh: biết con học thế nào',
        body: [
          'Phụ huynh tạo tài khoản riêng, nhập mã liên kết của con để xem báo cáo hằng tuần: số buổi học, phút học, độ chính xác, kỹ năng nào đang lên, kỹ năng nào cần luyện thêm và gợi ý việc bố mẹ nên làm.',
          'App gửi cảnh báo khi con nghỉ học 2 ngày hoặc chuỗi ngày học sắp mất, qua email, thông báo đẩy hoặc Zalo. Gói gia đình cho phép một lần thanh toán dùng Premium cho tối đa 4 con.',
        ],
        bullets: ['Báo cáo tuần dễ hiểu, có thể in PDF', 'Cảnh báo nghỉ học và chuỗi ngày sắp mất', 'Người lớn luôn thấy giao diện chuyên nghiệp, gọn gàng'],
      },
    ],
    steps: [
      { title: 'Tạo tài khoản cho con', desc: 'Hoặc cho con học thử ngay, không cần đăng ký.' },
      { title: 'Làm bài kiểm tra đầu vào', desc: 'App xếp trình độ và tạo lộ trình vừa sức.' },
      { title: 'Liên kết tài khoản phụ huynh', desc: 'Nhập mã của con để nhận báo cáo tuần.' },
    ],
    faqs: [
      { q: 'Con nên học bao nhiêu phút mỗi ngày?', a: 'Với trẻ nhỏ, 10–15 phút mỗi ngày đều đặn hiệu quả hơn học dồn. Phụ huynh có thể chọn 5, 10, 15 hoặc 30 phút khi tạo lộ trình.' },
      { q: 'Phụ huynh không giỏi tiếng Anh có kèm con được không?', a: 'Được. Báo cáo, lời khuyên và giải thích ngữ pháp đều bằng tiếng Việt; bố mẹ chỉ cần xem báo cáo tuần và nhắc con học đều.' },
      { q: 'Làm sao liên kết tài khoản phụ huynh với con?', a: 'Trong app của con có mã liên kết. Phụ huynh đăng ký tài khoản phụ huynh, chọn Liên kết với con và nhập mã đó.' },
      { q: 'Gói gia đình dùng cho mấy con?', a: 'Gói gia đình do phụ huynh thanh toán, dùng Premium cho tối đa 4 con đã liên kết.' },
    ],
    cta: { title: 'Cho con học thử ngay hôm nay', desc: 'Không cần thẻ, không cần cài đặt — mở trình duyệt là học.', label: 'Học thử miễn phí', href: '/register' },
    related: ['tieng-anh-giao-tiep', 'luyen-thi-ielts', 'lop-hoc-va-doanh-nghiep'],
  },
  {
    slug: 'tieng-anh-giao-tiep',
    icon: 'talk',
    cardTitle: 'Tiếng Anh giao tiếp',
    cardDesc: 'Nhập vai tình huống thật, chấm phát âm, câu lạc bộ nói.',
    title: 'Học tiếng Anh giao tiếp với AI – nhập vai, chấm phát âm',
    description: 'Học tiếng Anh giao tiếp với AI: nhập vai gọi món, sân bay, khách sạn, phỏng vấn; chấm phát âm từng từ, podcast có phụ đề và câu lạc bộ nói nhóm có AI dẫn dắt.',
    eyebrow: 'Giao tiếp hằng ngày · Du lịch · Công việc',
    h1: 'Học tiếng Anh giao tiếp với AI',
    lead: 'Nói chuyện với AI trong những tình huống bạn sẽ gặp thật — gọi món, làm thủ tục sân bay, nhận phòng khách sạn, phỏng vấn — được sửa câu ngay và chấm phát âm từng từ, để lần sau nói tự tin hơn.',
    highlights: [
      { title: 'Nhập vai cùng nhân vật AI', desc: 'Mỗi tình huống có nhân vật, mục tiêu hội thoại và gợi ý câu khi bạn bí.' },
      { title: 'Chấm phát âm từng từ', desc: 'Biết từ nào nói chưa rõ, nghe mẫu và nói lại ngay.' },
      { title: 'Nghe podcast có phụ đề', desc: 'Bấm vào từ trong phụ đề để tra nghĩa, trả lời câu hỏi hiểu bài.' },
      { title: 'Câu lạc bộ nói nhóm', desc: 'Phòng 2–4 người luyện nói theo chủ đề, AI dẫn chuyện và sửa câu.' },
    ],
    sections: [
      {
        h2: 'Luyện nói theo tình huống thật',
        body: [
          'Phần Luyện nói có ba bước: nghe mẫu hội thoại, luyện từng câu có chấm phát âm, rồi nhập vai tự do với nhân vật AI. Khi bạn nói chưa tự nhiên, AI gợi ý cách nói lịch sự và phổ biến hơn — ví dụ thay “I want a coffee” bằng “I’d like a coffee, please”.',
          'Mọi câu mẫu đều nghe được bằng giọng đọc tự nhiên; bạn có thể nghe lại, nói theo (shadowing) và so sánh.',
        ],
        bullets: ['Gọi món, đặt bàn nhà hàng', 'Sân bay, khách sạn, hỏi đường khi du lịch', 'Phỏng vấn xin việc, thuyết trình công việc'],
      },
      {
        h2: 'Nghe nhiều để nói tự nhiên',
        body: [
          'Thư viện podcast theo trình độ có phụ đề song song; chạm vào từ bất kỳ để xem nghĩa và lưu vào sổ từ vựng. Sau mỗi tập có vài câu hỏi để kiểm tra bạn hiểu đến đâu.',
        ],
      },
      {
        h2: 'Câu lạc bộ nói: luyện cùng người thật',
        body: [
          'Tham gia phòng nói 2–4 người theo chủ đề; AI đóng vai người dẫn, đặt câu hỏi, sửa câu và giữ cuộc trò chuyện đi đúng hướng. Phòng có thể mở ngay hoặc hẹn giờ, và app nhắc bạn trước 15 phút.',
          'Nếu cần hỏi nhanh về ngữ pháp hay cách dùng từ, trợ lý Bo trả lời bằng tiếng Việt kèm ví dụ.',
        ],
      },
    ],
    steps: [
      { title: 'Chọn thời gian mỗi ngày', desc: '5–30 phút, học trên điện thoại hoặc máy tính.' },
      { title: 'Nhập vai tình huống', desc: 'Nói với AI, nhận sửa câu và điểm phát âm.' },
      { title: 'Ôn và nói lại', desc: 'Từ và câu đã học được nhắc ôn đúng lúc.' },
    ],
    faqs: [
      { q: 'Mất gốc có học giao tiếp được không?', a: 'Được. Bài kiểm tra đầu vào xếp bạn từ trình độ thấp nhất (Pre-A1); bài học và tình huống nhập vai được chọn vừa sức, có giải thích tiếng Việt.' },
      { q: 'AI chấm phát âm như thế nào?', a: 'AI so sánh câu bạn nói với câu mẫu để chỉ ra từ nào nói chưa rõ hoặc bị thiếu, kèm điểm cho cả câu. Bạn nghe lại mẫu và nói lại ngay để cải thiện.' },
      { q: 'Có cần cài ứng dụng không?', a: 'Không bắt buộc. AI AGENT ENGLISH chạy trên trình duyệt điện thoại và máy tính; bạn có thể thêm vào màn hình chính để mở nhanh như ứng dụng.' },
    ],
    cta: { title: 'Nói tiếng Anh tự tin hơn sau mỗi ngày', desc: 'Học thử ngay một tình huống nhập vai với AI.', label: 'Học thử miễn phí', href: '/register' },
    related: ['tieng-anh-cho-tre-em', 'luyen-thi-toeic', 'luyen-thi-ielts'],
  },
  {
    slug: 'lop-hoc-va-doanh-nghiep',
    icon: 'class',
    cardTitle: 'Cho lớp học & doanh nghiệp',
    cardDesc: 'Giao bài, kiểm tra định kỳ, chấm rubric, báo cáo nhóm.',
    title: 'Tiếng Anh cho lớp học & doanh nghiệp – giao bài, báo cáo',
    description: 'Công cụ dạy tiếng Anh với AI cho giáo viên và doanh nghiệp: tạo lớp bằng mã, giao bài theo tuần, bài kiểm tra định kỳ, chấm rubric IELTS, báo cáo CSV/PDF và gói theo ghế.',
    eyebrow: 'Giáo viên · Trung tâm · Phòng nhân sự',
    h1: 'Tiếng Anh cho lớp học và doanh nghiệp',
    lead: 'Tạo lớp trong một phút, học viên vào bằng mã; giao bài và bài kiểm tra định kỳ, AI tạo bài đúng trình độ từng người, còn bạn xem điểm, chấm lại và xuất báo cáo cho cả nhóm.',
    highlights: [
      { title: 'Lớp học bằng mã', desc: 'Tạo lớp hoặc nhóm doanh nghiệp, gửi mã cho học viên, xem XP, chuỗi ngày và kỹ năng của từng người.' },
      { title: 'Giao bài & kiểm tra định kỳ', desc: 'Giao bài tuần theo kỹ năng và chủ đề; giao đề thi thử cho cả lớp với hạn nộp, có bảng điểm.' },
      { title: 'Chấm lại theo rubric', desc: 'Xem bài viết của học viên, chấm lại theo 4 tiêu chí IELTS, theo dõi biểu đồ tiến bộ band.' },
      { title: 'Báo cáo & chứng nhận', desc: 'Xuất CSV, in báo cáo PDF, cấp chứng nhận hoàn thành có mã xác thực.' },
    ],
    sections: [
      {
        h2: 'Giao bài theo tuần, AI cá nhân hoá cho từng học viên',
        body: [
          'Bạn chọn kỹ năng (từ vựng, ngữ pháp, đọc, nghe) và chủ đề; mỗi học viên nhận bài học được tạo đúng trình độ của mình. Học xong là bài tập được tính hoàn thành, bạn thấy ngay ai đã làm và điểm bao nhiêu.',
        ],
      },
      {
        h2: 'Bài kiểm tra định kỳ cho cả lớp',
        body: [
          'Giao một đề thi thử Listening, Reading hoặc Speaking (IELTS/TOEIC) cho cả lớp trong khoảng ngày bạn chọn. Học viên nhận thông báo, làm bài trong app; lần làm đầu tiên trong hạn được tính điểm. Bạn xem bảng điểm từng người, điểm trung bình, cao nhất, thấp nhất; người chưa làm được nhắc vào ngày hết hạn.',
        ],
        bullets: ['Điểm tự chấm ngay khi nộp', 'Kết quả vào báo cáo CSV của lớp', 'Không tốn lượt thi miễn phí của học viên'],
      },
      {
        h2: 'Theo dõi từng học viên và nhận xét',
        body: [
          'Trang của mỗi học viên gồm bài học đã làm, bài viết, bài thi thử, bài thi nói và bài kiểm tra lớp. Bạn gửi nhận xét gắn với từng bài, chấm lại bài viết theo rubric IELTS và xem biểu đồ band qua thời gian. Lớp còn có lịch câu lạc bộ nói hằng tuần, phòng tự mở và nhắc cả lớp trước giờ học.',
        ],
      },
      {
        h2: 'Gói theo ghế cho doanh nghiệp',
        body: [
          'Gói nhóm tính theo số ghế: các thành viên được phủ Premium để học không giới hạn. Doanh nghiệp điền thông tin xuất hoá đơn VAT khi thanh toán.',
        ],
      },
    ],
    steps: [
      { title: 'Tạo tài khoản giáo viên / doanh nghiệp', desc: 'Chọn vai trò "Giáo viên / Công ty" khi đăng ký.' },
      { title: 'Tạo lớp và gửi mã', desc: 'Học viên nhập mã trong mục Lớp học.' },
      { title: 'Giao bài, kiểm tra, xem báo cáo', desc: 'Theo dõi tiến bộ của cả lớp ở một nơi.' },
    ],
    faqs: [
      { q: 'Học viên có cần tài khoản riêng không?', a: 'Có. Mỗi học viên tạo tài khoản (hoặc dùng tài khoản sẵn có) rồi nhập mã lớp để tham gia; một học viên có thể ở nhiều lớp.' },
      { q: 'Bài kiểm tra lớp chấm điểm thế nào?', a: 'Đề Listening/Reading chấm tự động theo đáp án và quy đổi band/điểm ước tính; đề Speaking được AI chấm theo tiêu chí của kỳ thi. Lần làm đầu tiên trong thời hạn là điểm được tính.' },
      { q: 'Có xuất báo cáo cho cả nhóm không?', a: 'Có. Bạn tải báo cáo CSV mở được bằng Excel (XP, chuỗi ngày, bài tập, điểm bài kiểm tra) hoặc in báo cáo PDF của nhóm.' },
    ],
    cta: { title: 'Mở lớp học tiếng Anh với AI', desc: 'Tạo tài khoản giáo viên miễn phí và thử giao bài đầu tiên.', label: 'Tạo tài khoản', href: '/register' },
    related: ['luyen-thi-ielts', 'luyen-thi-toeic', 'tieng-anh-cho-tre-em'],
  },
];

export const SEO_PAGE_BY_SLUG: Record<string, SeoPage> = Object.fromEntries(SEO_PAGES.map(p => [p.slug, p]));
