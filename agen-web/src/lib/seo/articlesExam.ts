/**
 * Cẩm nang · bài về kỳ thi (IELTS, TOEIC). Số liệu định dạng đề theo mô tả công khai của đơn vị tổ chức thi;
 * bảng quy đổi điểm ghi rõ là tham khảo. Không ghi lệ phí (thay đổi theo thời điểm, địa điểm).
 */
import type { Article } from './articleTypes';

export const EXAM_ARTICLES: Article[] = [
  {
    slug: 'cau-truc-de-thi-ielts',
    category: 'ielts',
    title: 'Cấu trúc đề thi IELTS và cách tính band điểm',
    description: 'Cấu trúc đề thi IELTS 4 kỹ năng: số câu, thời gian, dạng bài từng phần; cách tính band Overall, tiêu chí chấm Writing/Speaking và bảng quy đổi điểm tham khảo.',
    h1: 'Cấu trúc đề thi IELTS và cách tính band điểm',
    lead: 'Trước khi ôn, hãy nắm thật chắc đề thi gồm những gì: mỗi kỹ năng bao nhiêu câu, làm trong bao lâu, chấm theo tiêu chí nào và band Overall được làm tròn ra sao. Bài này tóm tắt đầy đủ để bạn lên kế hoạch ôn đúng chỗ.',
    published: '2026-10-27',
    updated: '2026-10-27',
    blocks: [
      {
        id: 'tong-quan',
        h2: 'IELTS gồm những phần nào?',
        paras: [
          'IELTS (International English Language Testing System) đánh giá đủ bốn kỹ năng Nghe, Đọc, Viết, Nói. Có hai hình thức: Academic (dành cho du học, nghề nghiệp yêu cầu học thuật) và General Training (định cư, làm việc, học nghề). Phần Nghe và Nói giống nhau ở cả hai hình thức; phần Đọc và Viết khác nhau về loại văn bản và đề bài.',
          'Nghe, Đọc, Viết thi liền nhau trong một buổi; phần Nói thi riêng với giám khảo, có thể cùng ngày hoặc cách vài ngày tuỳ địa điểm. Bạn có thể chọn thi trên giấy hoặc trên máy tính; nội dung và cách chấm như nhau.',
        ],
        table: {
          caption: 'Tóm tắt cấu trúc đề IELTS',
          head: ['Kỹ năng', 'Thời gian', 'Số câu / nhiệm vụ', 'Nội dung chính'],
          rows: [
            ['Listening', 'khoảng 30 phút (+10 phút chép đáp án nếu thi giấy, 2 phút kiểm tra nếu thi máy)', '40 câu, 4 phần', 'Hội thoại đời sống, độc thoại, thảo luận học thuật, bài giảng'],
            ['Reading', '60 phút', '40 câu, 3 bài đọc', 'Academic: bài từ sách, tạp chí, báo; General: văn bản đời sống và công việc'],
            ['Writing', '60 phút', '2 bài', 'Task 1 ≥ 150 từ, Task 2 ≥ 250 từ (bài luận)'],
            ['Speaking', '11–14 phút', '3 phần', 'Phỏng vấn, nói 1–2 phút theo cue card, thảo luận'],
          ],
        },
      },
      {
        id: 'listening',
        h2: 'IELTS Listening: 4 phần, 40 câu',
        paras: [
          'Bài nghe được phát một lần. Độ khó tăng dần: Part 1 là hội thoại hằng ngày (đặt phòng, đăng ký dịch vụ), Part 2 là độc thoại về chủ đề đời sống (giới thiệu một địa điểm, thông báo), Part 3 là thảo luận học thuật giữa hai đến bốn người, Part 4 là một bài giảng học thuật.',
        ],
        bullets: [
          'Dạng câu hỏi thường gặp: điền form, ghi chú, bảng; trắc nghiệm; nối thông tin; điền nhãn bản đồ, sơ đồ; hoàn thành câu; trả lời ngắn.',
          'Chú ý giới hạn từ trong đề (ví dụ "NO MORE THAN TWO WORDS AND/OR A NUMBER"): viết thừa từ là sai dù đúng ý.',
          'Chính tả phải đúng; số, ngày tháng phải viết theo đúng cách đã nghe.',
        ],
        tip: 'Dùng thời gian trước mỗi phần để đọc câu hỏi và gạch chân từ khoá, đoán loại từ cần điền (danh từ, số, tên riêng). Đáp án thường xuất hiện theo đúng thứ tự câu hỏi.',
      },
      {
        id: 'reading',
        h2: 'IELTS Reading: 3 bài đọc, 40 câu trong 60 phút',
        paras: [
          'Không có thời gian chép đáp án riêng, nên bạn cần quản lý giờ: trung bình khoảng 20 phút cho mỗi bài đọc. Bài Academic dài, có văn phong học thuật; bài General Training gồm thông báo, quảng cáo, tài liệu công việc rồi mới tới một bài dài hơn.',
        ],
        bullets: [
          'True / False / Not Given (hoặc Yes / No / Not Given với quan điểm tác giả): "Not Given" khi bài không nói tới, đừng suy luận thêm.',
          'Matching headings: chọn tiêu đề cho từng đoạn — đọc câu chủ đề đầu đoạn và ý tổng kết cuối đoạn.',
          'Sentence / summary completion: chép đúng từ trong bài, đúng giới hạn số từ.',
          'Multiple choice, matching information, matching features.',
        ],
        tip: 'Đọc lướt (skimming) toàn bài 2–3 phút để nắm ý từng đoạn, rồi mới đọc dò (scanning) theo từ khoá của câu hỏi. Để ý từ đồng nghĩa: đề hiếm khi lặp nguyên văn câu trong bài.',
      },
      {
        id: 'writing',
        h2: 'IELTS Writing: Task 1 và Task 2',
        paras: [
          'Task 1 Academic yêu cầu mô tả biểu đồ, bảng, bản đồ hoặc quy trình trong ít nhất 150 từ; Task 1 General Training là viết thư (trang trọng hoặc thân mật). Task 2 ở cả hai hình thức là bài luận ít nhất 250 từ: nêu quan điểm, thảo luận hai mặt, nguyên nhân – giải pháp, lợi – hại.',
          'Task 2 chiếm trọng số gấp đôi Task 1, nên nên dành khoảng 40 phút cho Task 2 và 20 phút cho Task 1. Viết thiếu số từ tối thiểu sẽ bị trừ điểm ở tiêu chí đáp ứng đề.',
        ],
        table: {
          caption: 'Bốn tiêu chí chấm Writing (mỗi tiêu chí 25%)',
          head: ['Tiêu chí', 'Giám khảo xem gì'],
          rows: [
            ['Task Achievement (Task 1) / Task Response (Task 2)', 'Trả lời đúng và đủ yêu cầu đề, có tổng quan (Task 1), quan điểm rõ và phát triển ý (Task 2)'],
            ['Coherence and Cohesion', 'Bố cục đoạn hợp lý, ý nối tiếp mạch lạc, dùng từ nối tự nhiên, không lạm dụng'],
            ['Lexical Resource', 'Vốn từ đa dạng, dùng đúng ngữ cảnh, kết hợp từ tự nhiên, ít lỗi chính tả'],
            ['Grammatical Range and Accuracy', 'Dùng được nhiều cấu trúc câu, câu phức chính xác, ít lỗi ngữ pháp'],
          ],
        },
      },
      {
        id: 'speaking',
        h2: 'IELTS Speaking: 3 phần trong 11–14 phút',
        numbered: [
          'Part 1 (4–5 phút): giới thiệu và trả lời các câu hỏi quen thuộc về bản thân, công việc, sở thích, quê hương.',
          'Part 2 (3–4 phút): nhận cue card, có 1 phút chuẩn bị (được ghi chú), nói liên tục 1–2 phút về chủ đề, sau đó có thể được hỏi thêm một hai câu.',
          'Part 3 (4–5 phút): thảo luận sâu hơn, trừu tượng hơn, liên quan chủ đề Part 2.',
        ],
        after: [
          'Bốn tiêu chí chấm Speaking: Fluency and Coherence (trôi chảy, mạch lạc), Lexical Resource (từ vựng), Grammatical Range and Accuracy (ngữ pháp), Pronunciation (phát âm). Trả lời quá ngắn ở Part 1 hoặc không nói đủ thời gian ở Part 2 đều làm giảm điểm trôi chảy.',
        ],
      },
      {
        id: 'cach-tinh-band',
        h2: 'Cách tính band Overall',
        paras: [
          'Mỗi kỹ năng được chấm theo thang 0–9, có thể lẻ 0,5. Band Overall là trung bình cộng bốn kỹ năng, làm tròn tới nửa band gần nhất theo quy tắc: phần lẻ .25 làm tròn lên .5, phần lẻ .75 làm tròn lên band nguyên tiếp theo, các phần lẻ nhỏ hơn thì làm tròn xuống.',
        ],
        table: {
          caption: 'Ví dụ làm tròn band Overall',
          head: ['Listening', 'Reading', 'Writing', 'Speaking', 'Trung bình', 'Overall'],
          rows: [
            ['6.5', '6.5', '5.0', '7.0', '6.25', '6.5'],
            ['7.0', '6.5', '6.0', '6.0', '6.375', '6.5'],
            ['6.0', '6.5', '6.5', '7.0', '6.5', '6.5'],
            ['7.0', '7.0', '6.5', '7.5', '7.0', '7.0'],
            ['6.0', '6.0', '5.5', '6.0', '5.875', '6.0'],
          ],
        },
      },
      {
        id: 'quy-doi-diem',
        h2: 'Bảng quy đổi số câu đúng sang band (tham khảo)',
        paras: [
          'Listening và Reading chấm theo số câu đúng trên 40 rồi quy ra band. Bảng dưới là mức quy đổi tham khảo được dùng phổ biến; ngưỡng thật có thể chênh nhẹ giữa các đề để giữ độ khó tương đương.',
        ],
        table: {
          head: ['Band', 'Listening (số câu đúng)', 'Academic Reading (số câu đúng)'],
          rows: [
            ['9.0', '39–40', '39–40'],
            ['8.0', '35–36', '35–36'],
            ['7.0', '30–31', '30–32'],
            ['6.5', '26–29', '27–29'],
            ['6.0', '23–25', '23–26'],
            ['5.5', '18–22', '19–22'],
            ['5.0', '16–17', '15–18'],
          ],
        },
        tip: 'Muốn đạt 6.5 Overall, mục tiêu thường gặp là Listening/Reading khoảng 27–30 câu đúng và Writing/Speaking ổn định ở 6.0 trở lên.',
      },
      {
        id: 'luyen-tap',
        h2: 'Luyện theo đúng cấu trúc đề với AI AGENT ENGLISH',
        paras: [
          'Trong ứng dụng, phần Thi thử có các mini test IELTS Listening và Reading giữ nguyên dạng câu hỏi ở trên, chấm ngay và quy ra band ước tính; phần thi thử Speaking có giám khảo AI hỏi đủ Part 1–3, chấm theo bốn tiêu chí. Khi luyện viết, chọn IELTS Task 2 (bài luận) hoặc Task 1 dạng thư (General Training) để được chấm band từng tiêu chí và xem bài đã sửa.',
          'Band trên ứng dụng là ước tính để theo dõi tiến bộ; hãy dùng nó để biết kỹ năng nào đang kéo điểm Overall xuống và ôn đúng chỗ đó.',
        ],
      },
    ],
    faqs: [
      { q: 'Nên thi IELTS trên giấy hay trên máy tính?', a: 'Nội dung và cách chấm như nhau. Thi máy thường có kết quả nhanh hơn và phù hợp người gõ phím nhanh; thi giấy hợp với người quen viết tay và muốn ghi chú trực tiếp lên đề. Hãy luyện đúng hình thức bạn sẽ thi.' },
      { q: 'Viết thiếu số từ tối thiểu có bị trừ điểm không?', a: 'Có. Task 1 dưới 150 từ hoặc Task 2 dưới 250 từ sẽ bị ảnh hưởng ở tiêu chí đáp ứng đề. Nên viết dư một chút (khoảng 170–190 từ cho Task 1, 260–300 từ cho Task 2) thay vì viết rất dài.' },
      { q: 'Band 6.5 tương đương trình độ nào?', a: 'Band 5.5–6.5 thường được xem là tương đương bậc B2 của khung CEFR; 7.0 trở lên tiến dần tới C1. Đây là mức tham chiếu chung, không thay cho yêu cầu cụ thể của từng trường.' },
    ],
    goal: 'luyen-thi-ielts',
    related: ['lo-trinh-tu-hoc-ielts', 'khung-cefr-la-gi', 'luyen-noi-tieng-anh-mot-minh'],
  },
  {
    slug: 'lo-trinh-tu-hoc-ielts',
    category: 'ielts',
    title: 'Lộ trình tự học IELTS từ mất gốc đến 6.5',
    description: 'Lộ trình tự học IELTS theo từng giai đoạn: củng cố nền tảng A2, làm quen định dạng đề ở B1, luyện chiến thuật để lên 6.5 — kèm lịch học mỗi ngày và lỗi thường gặp.',
    h1: 'Lộ trình tự học IELTS từ mất gốc đến 6.5',
    lead: 'Tự học IELTS hiệu quả không phải là làm thật nhiều đề, mà là đi đúng thứ tự: nền tảng trước, định dạng đề sau, chiến thuật cuối cùng. Dưới đây là lộ trình theo trình độ CEFR, kèm lịch học mẫu bạn có thể áp dụng ngay.',
    published: '2026-10-27',
    updated: '2026-10-27',
    blocks: [
      {
        id: 'xac-dinh-trinh-do',
        h2: 'Bước 0: biết mình đang ở đâu',
        paras: [
          'Hãy làm một bài kiểm tra trình độ trước khi lên kế hoạch. Nếu bạn chưa đọc hiểu được đoạn văn đơn giản hoặc chưa nghe được hội thoại chậm, hãy bắt đầu từ giai đoạn nền tảng — luyện đề quá sớm chỉ làm bạn nản vì điểm thấp và không biết sửa từ đâu.',
          'Về thời gian, Cambridge ước tính mỗi bậc CEFR cần khoảng 200 giờ học có hướng dẫn. Con số thực tế khác nhau ở mỗi người, nhưng nó cho bạn hình dung: đi từ A2 lên B2 là một hành trình nhiều tháng, cần học đều mỗi ngày thay vì học dồn.',
        ],
      },
      {
        id: 'giai-doan-1',
        h2: 'Giai đoạn 1 — Nền tảng (A1–A2, chưa cần làm đề)',
        bullets: [
          'Ngữ pháp cốt lõi: các thì hiện tại, quá khứ, tương lai; câu hỏi; so sánh; mệnh đề quan hệ cơ bản.',
          'Từ vựng: khoảng 1.500–2.000 từ thông dụng nhất, học theo chủ đề và ôn tập ngắt quãng.',
          'Nghe: hội thoại chậm có phụ đề, nghe lại và nói theo (shadowing).',
          'Phát âm: âm cuối, trọng âm từ — nền tảng cho Speaking và cả Listening.',
        ],
        tip: 'Mục tiêu giai đoạn này là hiểu được bài nghe, bài đọc đơn giản mà không phải tra từ từng câu, và nói được 3–4 câu liền mạch về bản thân.',
      },
      {
        id: 'giai-doan-2',
        h2: 'Giai đoạn 2 — Làm quen định dạng đề (B1, khoảng band 4.0–5.0)',
        bullets: [
          'Học từng dạng câu hỏi Listening và Reading: điền form, True/False/Not Given, matching headings… Làm theo từng dạng trước khi làm cả đề.',
          'Writing: học cấu trúc bài Task 1 (mở bài – tổng quan – thân bài) và Task 2 (mở bài nêu quan điểm – 2 đoạn thân bài – kết luận).',
          'Speaking: luyện trả lời Part 1 thành 2–3 câu có lý do; tập nói đủ 1 phút cho Part 2.',
          'Từ vựng học thuật theo chủ đề hay gặp: giáo dục, môi trường, công nghệ, sức khoẻ, đô thị.',
        ],
      },
      {
        id: 'giai-doan-3',
        h2: 'Giai đoạn 3 — Chiến thuật và luyện đề (B2, band 5.5–6.5)',
        bullets: [
          'Làm đề có giới hạn thời gian, chữa kỹ từng câu sai: sai vì không nghe được, vì bẫy từ đồng nghĩa hay vì hết giờ?',
          'Writing: luyện phát triển ý (giải thích + ví dụ), đa dạng cấu trúc câu, nhờ chấm theo 4 tiêu chí để biết tiêu chí nào thấp nhất.',
          'Speaking: luyện Part 2 với đồng hồ, dùng đủ các gợi ý trên cue card; Part 3 trả lời theo khung "quan điểm – lý do – ví dụ".',
          'Thi thử toàn bộ định kỳ (ví dụ 2 tuần/lần) để quen áp lực thời gian.',
        ],
      },
      {
        id: 'lich-hoc',
        h2: 'Lịch học mẫu 60 phút mỗi ngày',
        table: {
          head: ['Thời lượng', 'Hoạt động', 'Ghi chú'],
          rows: [
            ['10 phút', 'Ôn từ vựng đến hạn', 'Ôn tập ngắt quãng, nói to từ và câu ví dụ'],
            ['20 phút', 'Kỹ năng chính của ngày', 'Luân phiên: thứ 2–4–6 Listening/Reading, thứ 3–5 Writing'],
            ['15 phút', 'Speaking', 'Trả lời 3 câu Part 1 hoặc 1 cue card Part 2, ghi âm và nghe lại'],
            ['15 phút', 'Chữa lỗi', 'Ghi lỗi sai vào sổ, xem lại lỗi tuần trước'],
          ],
        },
        after: [
          'Cuối tuần: một bài thi thử một kỹ năng, xem lại các lỗi lặp lại để quyết định tuần sau ưu tiên gì. Nếu chỉ có 30 phút mỗi ngày, giữ phần ôn từ và một kỹ năng chính, luân phiên các kỹ năng còn lại.',
        ],
      },
      {
        id: 'loi-thuong-gap',
        h2: 'Những lỗi khiến tự học IELTS chậm tiến bộ',
        bullets: [
          'Luyện đề liên tục nhưng không chữa lỗi — điểm sẽ đứng yên.',
          'Học thuộc bài mẫu Writing/Speaking rồi ghép vào: giám khảo dễ nhận ra và điểm từ vựng, trôi chảy không cao.',
          'Bỏ qua phát âm vì nghĩ "chỉ cần nói được": phát âm ảnh hưởng trực tiếp tới điểm Speaking và khả năng nghe.',
          'Không có người chấm Writing: tự đọc lại khó thấy lỗi mạch lạc và lỗi dùng từ.',
        ],
      },
      {
        id: 'hoc-voi-ai',
        h2: 'Tự học IELTS cùng AI AGENT ENGLISH',
        paras: [
          'Ứng dụng làm bài kiểm tra đầu vào để xếp bạn vào đúng giai đoạn, tạo bài học theo trình độ, nhắc ôn từ vựng đúng lúc và có lộ trình mục tiêu IELTS. Khi nhập band mục tiêu và ngày thi, kế hoạch ôn thi tự chia chỉ tiêu theo tuần, ưu tiên kỹ năng đang thấp nhất. Bài viết được chấm band theo 4 tiêu chí và thi thử Speaking có giám khảo AI — hai phần người tự học thường thiếu người chấm.',
        ],
      },
    ],
    faqs: [
      { q: 'Tự học IELTS mất bao lâu để đạt 6.5?', a: 'Tuỳ điểm xuất phát và thời gian học mỗi ngày. Theo ước tính của Cambridge, mỗi bậc CEFR cần khoảng 200 giờ học có hướng dẫn; từ B1 lên B2 (khoảng band 6.0–6.5) thường cần nhiều tháng học đều đặn.' },
      { q: 'Có nên học từ vựng IELTS theo danh sách dài không?', a: 'Nên học theo chủ đề và trong câu ví dụ, kết hợp ôn tập ngắt quãng. Học danh sách dài không có ngữ cảnh dễ quên và khó dùng khi viết, nói.' },
      { q: 'Mất gốc có nên luyện đề ngay không?', a: 'Chưa nên. Hãy củng cố ngữ pháp, từ vựng cơ bản và nghe chậm trước; khi đọc hiểu được đoạn văn đơn giản mới chuyển sang làm quen dạng đề.' },
    ],
    goal: 'luyen-thi-ielts',
    related: ['cau-truc-de-thi-ielts', 'hoc-tu-vung-nho-lau', 'khung-cefr-la-gi'],
  },
  {
    slug: 'cau-truc-de-thi-toeic',
    category: 'toeic',
    title: 'Cấu trúc đề thi TOEIC 4 kỹ năng và mẹo từng Part',
    description: 'Cấu trúc đề TOEIC Listening & Reading 7 Part (200 câu, 120 phút, thang 10–990) và TOEIC Speaking & Writing, kèm mẹo làm bài cho từng Part.',
    h1: 'Cấu trúc đề thi TOEIC và mẹo làm bài từng Part',
    lead: 'TOEIC đo tiếng Anh trong môi trường công việc. Phần lớn người đi làm thi TOEIC Listening & Reading; nhiều doanh nghiệp và trường còn yêu cầu thêm Speaking & Writing. Nắm rõ từng Part giúp bạn phân bổ thời gian và ôn đúng trọng tâm.',
    published: '2026-10-27',
    updated: '2026-10-27',
    blocks: [
      {
        id: 'listening-reading',
        h2: 'TOEIC Listening & Reading: 200 câu trong khoảng 2 giờ',
        paras: [
          'Bài thi gồm 100 câu Nghe (khoảng 45 phút) và 100 câu Đọc (75 phút), tất cả là trắc nghiệm. Mỗi phần chấm thang 5–495, tổng điểm 10–990.',
        ],
        table: {
          caption: 'Cấu trúc TOEIC Listening & Reading',
          head: ['Part', 'Dạng bài', 'Số câu'],
          rows: [
            ['1', 'Mô tả tranh: chọn câu mô tả đúng bức ảnh', '6'],
            ['2', 'Hỏi – đáp: chọn câu đáp phù hợp (3 lựa chọn)', '25'],
            ['3', 'Hội thoại ngắn, mỗi bài 3 câu hỏi (có bài kèm biểu đồ)', '39'],
            ['4', 'Bài nói ngắn: thông báo, tin nhắn thoại, giới thiệu — mỗi bài 3 câu', '30'],
            ['5', 'Hoàn thành câu: ngữ pháp và từ vựng', '30'],
            ['6', 'Hoàn thành đoạn văn: điền từ/câu vào email, thông báo', '16'],
            ['7', 'Đọc hiểu: đoạn đơn và nhóm 2–3 văn bản liên quan', '54'],
          ],
        },
      },
      {
        id: 'meo-nghe',
        h2: 'Mẹo phần Nghe (Part 1–4)',
        bullets: [
          'Part 1: loại ngay đáp án nhắc tới vật/hành động không có trong ảnh; cẩn thận các từ phát âm giống nhau.',
          'Part 2: câu hỏi Wh- thường không trả lời bằng Yes/No; đáp án đúng đôi khi là câu hỏi lại hoặc câu gián tiếp ("Let me check the schedule.").',
          'Part 3–4: đọc trước 3 câu hỏi khi đoạn giới thiệu đang phát; đáp án thường đi theo thứ tự câu hỏi.',
          'Để ý câu chứa thông tin về người nói (ai, ở đâu, làm nghề gì) và hành động tiếp theo ("What will the man probably do next?").',
        ],
      },
      {
        id: 'meo-doc',
        h2: 'Mẹo phần Đọc (Part 5–7)',
        bullets: [
          'Part 5: xác định loại câu hỏi trước (từ loại, thì, giới từ, liên từ, từ vựng); câu từ loại thường làm nhanh không cần dịch cả câu.',
          'Part 6: đọc cả đoạn quanh chỗ trống — câu điền thường phụ thuộc ý câu trước hoặc sau.',
          'Part 7: đọc câu hỏi trước rồi tìm thông tin; với nhóm văn bản, câu hỏi suy luận thường cần kết hợp thông tin ở hai văn bản.',
          'Phân bổ thời gian sao cho còn khoảng 50–55 phút cho Part 7 — phần nhiều câu và tốn thời gian nhất.',
        ],
        tip: 'Nếu hết giờ vẫn còn câu chưa làm, hãy chọn đại một đáp án: TOEIC không trừ điểm câu sai.',
      },
      {
        id: 'speaking-writing',
        h2: 'TOEIC Speaking & Writing',
        paras: [
          'Phần Nói có 11 câu trong khoảng 20 phút, phần Viết 8 câu trong khoảng 60 phút; mỗi phần chấm thang 0–200. Bạn thi trên máy tính, nói vào micro và gõ bài viết.',
        ],
        table: {
          head: ['Phần', 'Câu', 'Nhiệm vụ'],
          rows: [
            ['Speaking', 'Q1–2', 'Đọc to một đoạn văn (phát âm, ngữ điệu, trọng âm)'],
            ['Speaking', 'Q3–4', 'Mô tả một bức ảnh'],
            ['Speaking', 'Q5–7', 'Trả lời câu hỏi theo tình huống khảo sát/đời sống'],
            ['Speaking', 'Q8–10', 'Trả lời câu hỏi dựa trên thông tin cho sẵn (lịch, bảng)'],
            ['Speaking', 'Q11', 'Nêu ý kiến về một vấn đề, có lý do và ví dụ'],
            ['Writing', 'Q1–5', 'Viết một câu mô tả tranh với hai từ cho sẵn'],
            ['Writing', 'Q6–7', 'Trả lời email/yêu cầu bằng văn bản'],
            ['Writing', 'Q8', 'Viết bài luận nêu ý kiến'],
          ],
        },
      },
      {
        id: 'on-toeic-hieu-qua',
        h2: 'Ôn TOEIC hiệu quả cho người đi làm',
        bullets: [
          'Học từ vựng công sở theo chủ đề: họp, tuyển dụng, mua hàng, du lịch công tác, tài chính văn phòng.',
          'Mỗi ngày 15–30 phút: 10 câu Part 5 + một bài nghe Part 3/4 + ôn từ vựng.',
          'Thi thử theo Part, sau đó thi thử toàn bộ định kỳ để luyện sức bền 2 giờ.',
          'Với Speaking: luyện đọc to và trả lời câu hỏi có hẹn giờ; với Writing: luyện mẫu email phản hồi đủ các yêu cầu đề nêu.',
        ],
        after: [
          'Trong AI AGENT ENGLISH, phần Thi thử có đề Listening (Part 2–4) và Reading (Part 5–7) chấm ngay, thi thử Speaking có đọc to được chấm phát âm, và phần Luyện viết có dạng email, bài luận TOEIC được chấm điểm ước tính thang 0–200.',
        ],
      },
    ],
    faqs: [
      { q: 'TOEIC bao nhiêu điểm là tốt?', a: 'Tuỳ yêu cầu của nơi bạn nộp. Theo bảng ánh xạ tham khảo của ETS, khoảng 550 điểm Listening & Reading tương ứng mức tối thiểu của B1 và khoảng 785 điểm tương ứng B2.' },
      { q: 'Thi TOEIC có bị trừ điểm câu sai không?', a: 'Không. Điểm tính theo số câu đúng, vì vậy đừng bỏ trống câu nào.' },
      { q: 'Nên ôn Part nào trước?', a: 'Người mới thường bắt đầu với Part 5 (ngữ pháp, từ vựng) và Part 2 (phản xạ nghe) vì cải thiện nhanh, sau đó luyện Part 3, 4 và Part 7.' },
    ],
    goal: 'luyen-thi-toeic',
    related: ['meo-toeic-part-5', 'hoc-tu-vung-nho-lau', 'khung-cefr-la-gi'],
  },
  {
    slug: 'meo-toeic-part-5',
    category: 'toeic',
    title: 'Mẹo làm TOEIC Part 5: 7 dạng câu hỏi thường gặp',
    description: 'Cách làm nhanh TOEIC Part 5 (Incomplete Sentences): nhận diện 7 dạng câu hỏi về từ loại, thì, giới từ, liên từ, đại từ, mệnh đề quan hệ, từ vựng — kèm ví dụ có giải thích.',
    h1: 'Mẹo làm TOEIC Part 5: 7 dạng câu hỏi thường gặp',
    lead: 'Part 5 có 30 câu hoàn thành câu và là nơi dễ "ăn điểm" nhất phần Đọc nếu bạn nhận diện nhanh dạng câu hỏi. Mục tiêu là làm chắc, nhanh để dành thời gian cho Part 7.',
    published: '2026-10-27',
    updated: '2026-10-27',
    blocks: [
      {
        id: 'cach-lam',
        h2: 'Quy trình 3 bước cho mỗi câu',
        numbered: [
          'Nhìn 4 đáp án trước để biết dạng câu hỏi: cùng gốc từ khác đuôi (từ loại), cùng động từ khác dạng (thì, bị động), hay 4 từ khác nghĩa (từ vựng).',
          'Đọc phần câu quanh chỗ trống — với câu từ loại thường chỉ cần vài từ trước và sau.',
          'Chọn đáp án; nếu phân vân quá 30 giây, đánh dấu và đi tiếp.',
        ],
      },
      {
        id: 'tu-loai',
        h2: '1. Từ loại (word form)',
        paras: [
          'Dạng phổ biến nhất. Đáp án là các biến thể như success / successful / successfully / succeed. Hãy xác định vị trí: sau mạo từ và trước danh từ thường là tính từ; trước tính từ hoặc bổ nghĩa cho động từ thường là trạng từ; sau tính từ sở hữu thường là danh từ.',
          'Ví dụ: "The new software was ____ installed on all computers." → successfully (trạng từ bổ nghĩa cho động từ installed).',
        ],
      },
      {
        id: 'thi-dong-tu',
        h2: '2. Thì và dạng động từ',
        paras: [
          'Tìm dấu hiệu thời gian (since, by the end of, next week, currently) và chủ ngữ số ít/số nhiều. Chú ý câu bị động khi chủ ngữ là vật chịu tác động.',
          'Ví dụ: "The report ____ by Friday." → will be completed (bị động, tương lai).',
        ],
      },
      {
        id: 'gioi-tu',
        h2: '3. Giới từ',
        bullets: [
          'Thời gian: in (tháng, năm), on (ngày), at (giờ), by (trước hạn), until (kéo dài đến), during (trong suốt).',
          'Cụm cố định hay gặp: in charge of, responsible for, according to, in addition to, prior to.',
        ],
      },
      {
        id: 'lien-tu',
        h2: '4. Liên từ hay giới từ?',
        paras: [
          'Although / because / while + mệnh đề (có chủ ngữ và động từ); despite / because of / during + danh từ hoặc V-ing. Đây là bẫy rất hay gặp.',
          'Ví dụ: "____ the heavy rain, the event started on time." → Despite (theo sau là cụm danh từ).',
        ],
      },
      {
        id: 'dai-tu',
        h2: '5. Đại từ',
        paras: [
          'Phân biệt chủ ngữ (they), tân ngữ (them), sở hữu (their / theirs) và phản thân (themselves). "By + đại từ phản thân" nghĩa là tự mình làm.',
          'Ví dụ: "Ms. Lee prepared the presentation by ____." → herself.',
        ],
      },
      {
        id: 'menh-de-quan-he',
        h2: '6. Mệnh đề quan hệ và so sánh',
        bullets: [
          'who (người, làm chủ ngữ), whom (người, làm tân ngữ), which (vật), whose (sở hữu), that (thay who/which trong mệnh đề xác định).',
          'So sánh hơn có than; so sánh nhất thường có the và phạm vi (in the company, of all applicants).',
        ],
      },
      {
        id: 'tu-vung',
        h2: '7. Từ vựng và kết hợp từ (collocation)',
        paras: [
          'Bốn đáp án cùng từ loại nhưng khác nghĩa — cần hiểu câu. Học từ theo cụm sẽ làm nhanh hơn: meet a deadline, submit a proposal, conduct a survey, launch a product, reach an agreement.',
        ],
        tip: 'Ghi các câu sai vào sổ theo 7 dạng trên. Sau vài tuần, bạn sẽ thấy mình hay sai dạng nào để ôn tập trung.',
      },
      {
        id: 'luyen-tap',
        h2: 'Luyện Part 5 mỗi ngày',
        paras: [
          'Làm 10–15 câu mỗi ngày có bấm giờ (mục tiêu dưới 30 giây mỗi câu), chữa kỹ từng câu sai. Trong AI AGENT ENGLISH, lộ trình mục tiêu TOEIC có chặng ngữ pháp Part 5 & 6, đề thi thử Reading chấm ngay kèm lời giải tiếng Việt, và trợ lý Bo giải thích điểm ngữ pháp khi bạn hỏi.',
        ],
      },
    ],
    faqs: [
      { q: 'Nên làm Part 5 trong bao lâu?', a: 'Nhiều người đặt mục tiêu khoảng 10–12 phút cho 30 câu để còn đủ thời gian cho Part 6 và Part 7.' },
      { q: 'Có cần dịch cả câu ở Part 5 không?', a: 'Không phải lúc nào. Câu từ loại, đại từ, liên từ – giới từ thường chỉ cần nhìn cấu trúc quanh chỗ trống; chỉ câu từ vựng mới cần hiểu nghĩa cả câu.' },
    ],
    goal: 'luyen-thi-toeic',
    related: ['cau-truc-de-thi-toeic', 'hoc-tu-vung-nho-lau', 'luyen-noi-tieng-anh-mot-minh'],
  },
];
