/**
 * Hướng dẫn sử dụng theo đối tượng (/huong-dan-su-dung/<slug>). Ảnh chụp thật từ ứng dụng với dữ liệu mẫu,
 * lưu ở public/guides/*.webp (1440×900, ảnh điện thoại 720 px rộng). Chụp lại khi giao diện đổi nhiều.
 */
import type { SeoIcon } from './pages';

export interface GuideImage { src: string; alt: string; caption?: string; mobile?: boolean }
export interface GuideStep { id: string; title: string; text: string[]; bullets?: string[]; tip?: string; images?: GuideImage[] }
export interface Guide {
  slug: string;
  icon: SeoIcon;
  cardTitle: string;
  cardDesc: string;
  title: string;
  description: string;
  h1: string;
  lead: string;
  steps: GuideStep[];
  faqs: { q: string; a: string }[];
  related: string[];          // other guide slugs
}

const img = (name: string, alt: string, caption?: string): GuideImage => ({ src: `/guides/${name}.webp`, alt, caption, mobile: name.endsWith('mobile') });

export const GUIDES: Guide[] = [
  {
    slug: 'nguoi-hoc',
    icon: 'talk',
    cardTitle: 'Người học',
    cardDesc: 'Từ tạo tài khoản, kiểm tra trình độ đến học bài, luyện nói, luyện viết, thi thử và lập kế hoạch ôn thi.',
    title: 'Hướng dẫn sử dụng cho người học',
    description: 'Hướng dẫn dùng AI AGENT ENGLISH từng bước có ảnh minh hoạ: tạo tài khoản, kiểm tra đầu vào, học bài, luyện nói, luyện viết, thi thử IELTS/TOEIC, kế hoạch ôn thi, Hỏi Bo.',
    h1: 'Hướng dẫn sử dụng AI AGENT ENGLISH cho người học',
    lead: 'Mười phút đầu tiên quyết định bạn có học đều được không. Làm theo các bước dưới đây để có lộ trình đúng trình độ, rồi mỗi ngày chỉ cần mở trang chủ và làm theo nhiệm vụ hôm nay.',
    steps: [
      {
        id: 'tao-tai-khoan', title: '1. Tạo tài khoản hoặc học thử',
        text: [
          'Vào aiagentenglish.com, bấm "Học miễn phí". Ở mục "Bạn là" chọn Học viên, điền họ tên, tên hiển thị, email, mật khẩu (ít nhất 8 ký tự, có chữ và số), tuổi và cấp học rồi bấm "Bắt đầu học ngay".',
          'Muốn xem thử trước? Bấm "Học thử ngay" trên trang chủ để học mà không cần đăng ký; khi muốn giữ tiến bộ, lưu tài khoản bằng email — XP, chuỗi ngày và sổ từ vựng được giữ nguyên.',
        ],
        images: [img('nh-register', 'Trang tạo tài khoản AI AGENT ENGLISH với ba lựa chọn Học viên, Phụ huynh, Giáo viên / Công ty')],
      },
      {
        id: 'kiem-tra-dau-vao', title: '2. Làm bài kiểm tra đầu vào (8–10 phút)',
        text: [
          'Bài kiểm tra có 14 câu về từ vựng, ngữ pháp, đọc, nghe và nói; độ khó tự điều chỉnh theo câu trả lời. Hãy bật loa và cho phép trình duyệt dùng micro (nên dùng Chrome hoặc Edge) để làm phần nghe và đọc to.',
          'Kết quả xếp bạn vào trình độ CEFR (từ Pre-A1 đến C1) và là cơ sở tạo lộ trình học riêng.',
        ],
        images: [
          img('nh-placement', 'Màn hình bắt đầu bài kiểm tra đầu vào: 14 câu, 4 kỹ năng, kết quả ngay'),
          img('nh-placement-q', 'Một câu hỏi từ vựng trong bài kiểm tra đầu vào với 4 lựa chọn'),
        ],
        tip: 'Trả lời thật, đừng đoán bừa: xếp đúng trình độ thì bài học mới vừa sức và bạn tiến bộ nhanh hơn.',
      },
      {
        id: 'trang-chu', title: '3. Trang chủ: biết hôm nay cần học gì',
        text: [
          'Trang chủ cho biết trình độ, chuỗi ngày học, tổng XP, đá quý và bốn vòng kỹ năng Nghe – Nói – Đọc – Viết. Bên dưới là Bài học tiếp theo trong lộ trình, Nhiệm vụ hôm nay (ba nhiệm vụ nhỏ có thưởng XP) và thẻ chuỗi ngày kèm mục tiêu tuần.',
          'Thanh bên trái (hoặc thanh dưới trên điện thoại) dẫn tới mọi phần: Lộ trình, Bài học, Ôn tập, Blitz 60s, Sổ từ vựng, Luyện nói, Luyện viết, Podcast, CLB nói, Thi thử, Hỏi Bo, Mục tiêu, Kế hoạch thi, Giải đấu, Bạn học, Lớp học.',
        ],
        bullets: [
          'Lỡ một ngày? Bảo vệ chuỗi tự giữ chuỗi cho bạn (nhận thêm khi đạt mục tiêu tuần). Nếu chuỗi đã đứt, trong ngày hôm sau bạn có thể bấm "Sửa" để mua lại chuỗi bằng đá quý.',
          'Đạt mục tiêu tuần (3, 5 hoặc 7 ngày) để nhận thêm XP và một bảo vệ chuỗi.',
        ],
        images: [
          img('nh-dashboard', 'Trang chủ người học: lời chào, chuỗi ngày, XP, 4 vòng kỹ năng, bài học tiếp theo và nhiệm vụ hôm nay'),
          img('nh-mobile', 'Trang chủ trên điện thoại', 'Trên điện thoại, thanh điều hướng nằm ở cuối màn hình.'),
        ],
      },
      {
        id: 'hoc-bai', title: '4. Học bài và ôn tập',
        text: [
          'Vào Bài học, chọn kỹ năng (Vocabulary, Grammar, Reading, Listening) để tạo bài mới theo đúng trình độ, hoặc học bài gợi ý hôm nay. Mỗi câu trả lời được chấm ngay kèm giải thích tiếng Việt; câu sai có thể bấm để AI giải thích thêm.',
          'Từ mới và câu sai tự vào phần Ôn tập. Mở Ôn tập khi có từ đến hạn — ứng dụng nhắc ôn đúng lúc bạn sắp quên. Khi chỉ có một phút, chơi Blitz 60 giây để ôn nhanh.',
        ],
        images: [img('nh-lesson', 'Một câu hỏi trong bài học từ vựng chủ đề gọi đồ uống')],
      },
      {
        id: 'luyen-noi', title: '5. Luyện nói theo tình huống',
        text: [
          'Mở Luyện nói, lọc theo chủ đề (đời sống, du lịch, công việc, trường học…) và chọn một tình huống có nhãn "Hợp trình độ". Mỗi tình huống đi qua ba bước: học cụm từ → nói lặp lại có chấm phát âm theo từng từ → hội thoại tự do với nhân vật AI.',
          'Nhấn giữ nút micro để nói. AI trả lời, sửa câu và gợi ý cách nói tự nhiên hơn; bạn có thể nghe lại câu mẫu bất cứ lúc nào.',
        ],
        images: [img('nh-speaking', 'Danh sách tình huống luyện nói như phỏng vấn xin việc, làm thủ tục sân bay, thuê căn hộ')],
      },
      {
        id: 'luyen-viet', title: '6. Luyện viết và chấm theo band',
        text: [
          'Mở Luyện viết, chọn Viết tự do (ý kiến, kể chuyện, miêu tả, thư/email) hoặc Luyện thi (IELTS Task 2, IELTS Task 1 dạng thư, TOEIC email, TOEIC opinion essay). AI ra đề vừa trình độ, có gợi ý dàn ý và cụm từ hữu ích.',
          'Nộp bài để nhận điểm, các lỗi kèm giải thích tiếng Việt, bài đã sửa; với dạng luyện thi có thêm band IELTS theo 4 tiêu chí hoặc điểm TOEIC 0–200. Bài cũ nằm ở "Bài viết gần đây".',
        ],
        images: [img('nh-writing', 'Trang Luyện viết với các dạng viết tự do và luyện thi chấm theo band')],
      },
      {
        id: 'thi-thu', title: '7. Thi thử IELTS / TOEIC',
        text: [
          'Phần Thi thử có đề IELTS và TOEIC Listening, Reading đúng định dạng (có đồng hồ, phần nghe phát một lần) và thi Speaking với giám khảo AI. Nộp bài là có band/điểm ước tính và lời giải từng câu.',
          'Gói miễn phí làm được một đề mỗi ngày; Premium không giới hạn. Bài kiểm tra do giáo viên giao trong lớp không tính vào lượt miễn phí.',
        ],
        images: [img('nh-exams', 'Thư viện đề thi thử IELTS và TOEIC, kèm thi Speaking với giám khảo AI')],
      },
      {
        id: 'ke-hoach-thi', title: '8. Lập kế hoạch ôn thi',
        text: [
          'Mở Kế hoạch thi, chọn IELTS hoặc TOEIC, nhập band/điểm mục tiêu và ngày thi rồi bấm "Lập kế hoạch". Ứng dụng so điểm hiện tại từng kỹ năng với mục tiêu, dự kiến điểm vào ngày thi và chia lộ trình theo tuần — kỹ năng yếu được ưu tiên.',
          'Mỗi tuần có chỉ tiêu bài học, đề thi thử, bài viết và lượt luyện nói; nhãn "Đúng tiến độ" / "Chậm tiến độ" cho biết bạn có kịp không.',
        ],
        images: [img('nh-plan', 'Kế hoạch ôn thi IELTS 6.5 còn 84 ngày, điểm hiện tại từng kỹ năng và lộ trình theo tuần')],
      },
      {
        id: 'hoi-bo-podcast', title: '9. Hỏi Bo, nghe podcast, câu lạc bộ nói',
        text: [
          'Hỏi Bo: gõ thắc mắc ngữ pháp hoặc cách dùng từ bằng tiếng Việt, Bo trả lời kèm quy tắc, ví dụ nghe được và lỗi hay gặp (gói miễn phí có giới hạn số câu mỗi ngày).',
          'Podcast: chọn tập theo trình độ, đọc phụ đề song song, chạm vào từ để xem nghĩa và lưu vào sổ từ vựng. CLB nói: vào phòng 2–4 người theo chủ đề, có AI dẫn chuyện.',
        ],
        images: [
          img('nh-tutor', 'Hỏi Bo giải thích khác nhau giữa since và for, có ví dụ và lỗi hay gặp'),
          img('nh-listen', 'Thư viện podcast theo trình độ với nhiều chủ đề đời sống và công việc'),
        ],
      },
      {
        id: 'lop-hoc', title: '10. Tham gia lớp học của giáo viên',
        text: [
          'Nếu giáo viên hoặc công ty gửi mã (dạng LOP-XXXX hoặc CTY-XXXX), mở Lớp học và nhập mã. Bài tập được giao và bài kiểm tra lớp hiện ở đây kèm hạn nộp; bấm "Làm bài" để làm. Nhận xét của giáo viên cũng xuất hiện trên trang này.',
        ],
        images: [img('nh-classes', 'Trang Lớp học với bài kiểm tra lớp, điểm đã làm và bài tập đang chờ')],
      },
    ],
    faqs: [
      { q: 'Quên mật khẩu thì làm sao?', a: 'Ở trang Đăng nhập, dùng chức năng lấy lại mật khẩu theo email. Nếu không nhận được email, kiểm tra thư mục Spam hoặc liên hệ hỗ trợ.' },
      { q: 'Có dùng được trên điện thoại không?', a: 'Có. Mở aiagentenglish.com bằng trình duyệt điện thoại; trên trang chủ có thẻ hướng dẫn thêm ứng dụng vào màn hình chính để mở nhanh như app.' },
      { q: 'Làm sao bật nhắc học mỗi ngày?', a: 'Trên trang chủ, thẻ Nhắc học cho chọn giờ nhắc; bật thông báo trên thiết bị và/hoặc nhận email. Ứng dụng chỉ nhắc khi hôm đó bạn chưa học.' },
    ],
    related: ['hoc-sinh', 'phu-huynh', 'giao-vien'],
  },
  {
    slug: 'hoc-sinh',
    icon: 'kids',
    cardTitle: 'Học sinh nhỏ tuổi',
    cardDesc: 'Giao diện vui nhộn cùng Bo: nhiệm vụ, Blitz 60 giây, cửa hàng nhân vật, giải đấu và huy hiệu.',
    title: 'Hướng dẫn sử dụng cho học sinh',
    description: 'Hướng dẫn học sinh dùng AI AGENT ENGLISH: giao diện vui nhộn với Bo, nhiệm vụ hằng ngày, Blitz 60 giây, đá quý và cửa hàng, giải đấu tuần, huy hiệu và mã liên kết cho bố mẹ.',
    h1: 'Hướng dẫn sử dụng cho học sinh',
    lead: 'Với học viên dưới 16 tuổi, ứng dụng tự chuyển sang giao diện nhiều màu sắc có bạn đồng hành Bo. Cách học giống người lớn, nhưng có thêm trò chơi và phần thưởng để con muốn quay lại mỗi ngày.',
    steps: [
      {
        id: 'trang-chu', title: '1. Trang chủ có Bo',
        text: [
          'Bo chào con, nhắc giữ chuỗi ngày và khen khi làm tốt (Bo còn đọc lời nhắn bằng tiếng Việt cho bé chưa đọc giỏi). Trang chủ hiện trình độ, chuỗi ngày, XP, đá quý, bốn vòng kỹ năng và ba nhiệm vụ hôm nay.',
          'Nếu thích giao diện người lớn, có thể đổi giao diện trong Hồ sơ.',
        ],
        images: [
          img('hs-dashboard', 'Trang chủ giao diện vui nhộn của học sinh với linh vật Bo, chuỗi ngày và nhiệm vụ hôm nay'),
          img('hs-mobile', 'Trang chủ học sinh trên điện thoại'),
        ],
      },
      {
        id: 'blitz', title: '2. Blitz 60 giây',
        text: [
          'Trò chơi ôn từ: chọn nghĩa đúng của từ thật nhanh trong 60 giây. Mỗi câu đúng được thêm XP và đá quý (có giới hạn mỗi ngày để con không chơi quá nhiều).',
        ],
        images: [img('hs-blitz', 'Màn hình bắt đầu trò chơi Blitz 60 giây')],
      },
      {
        id: 'cua-hang', title: '3. Đá quý và cửa hàng',
        text: [
          'Đá quý nhận được khi học xong bài, làm nhiệm vụ, đạt mục tiêu tuần, chơi Blitz và đứng cao trong giải đấu. Vào Cửa hàng để đổi nhân vật, màu nền và khung avatar.',
        ],
        images: [img('hs-shop', 'Cửa hàng với các nhân vật như cáo, gấu trúc, mèo con, kỳ lân, rồng nhỏ')],
      },
      {
        id: 'giai-dau', title: '4. Giải đấu tuần',
        text: [
          'Mỗi tuần con thi đua XP với một nhóm bạn cùng hạng (Đồng, Bạc, Vàng, Kim cương). Nhóm đứng đầu được lên hạng và nhận thưởng; nhóm cuối có thể xuống hạng. Thứ Hai bắt đầu tuần mới.',
        ],
        images: [img('hs-league', 'Bảng giải đấu tuần với hạng Đồng, Bạc, Vàng, Kim cương và vùng thăng hạng')],
      },
      {
        id: 'ho-so', title: '5. Hồ sơ, huy hiệu và mã cho bố mẹ',
        text: [
          'Trang Hồ sơ hiện chuỗi ngày, điểm XP, số bài đã học và các huy hiệu đạt được. Mã liên kết (dạng AGEN-XXXX) cũng ở đây — đưa mã này cho bố mẹ để bố mẹ nhận báo cáo tuần của con.',
        ],
        images: [img('hs-profile', 'Hồ sơ học sinh với điểm XP, chuỗi ngày và bộ sưu tập huy hiệu')],
        tip: 'Bố mẹ nên ngồi cùng con trong buổi đầu: làm bài kiểm tra trình độ, chọn thời gian học mỗi ngày và bật nhắc học.',
      },
    ],
    faqs: [
      { q: 'Con dưới 16 tuổi có bắt buộc dùng giao diện vui nhộn không?', a: 'Không. Giao diện được chọn tự động theo tuổi, nhưng có thể đổi sang giao diện cổ điển trong Hồ sơ.' },
      { q: 'Con có thể chơi Blitz cả ngày không?', a: 'Phần thưởng XP và đá quý từ Blitz có giới hạn mỗi ngày, để trò chơi chỉ là phần ôn tập ngắn bên cạnh bài học chính.' },
    ],
    related: ['phu-huynh', 'nguoi-hoc', 'giao-vien'],
  },
  {
    slug: 'phu-huynh',
    icon: 'kids',
    cardTitle: 'Phụ huynh',
    cardDesc: 'Liên kết với con, đọc báo cáo tuần, nhận cảnh báo nghỉ học, in báo cáo PDF và gói gia đình.',
    title: 'Hướng dẫn sử dụng cho phụ huynh',
    description: 'Hướng dẫn phụ huynh dùng AI AGENT ENGLISH: tạo tài khoản phụ huynh, liên kết với con bằng mã, đọc báo cáo tuần, xem bài kiểm tra ở lớp, nhận cảnh báo và tải báo cáo PDF.',
    h1: 'Hướng dẫn sử dụng cho phụ huynh',
    lead: 'Tài khoản phụ huynh giúp bố mẹ biết con học thế nào mà không cần giỏi tiếng Anh: báo cáo hằng tuần bằng tiếng Việt, cảnh báo khi con nghỉ học và gợi ý bố mẹ nên làm gì.',
    steps: [
      {
        id: 'tao-tai-khoan', title: '1. Tạo tài khoản phụ huynh',
        text: ['Bấm "Học miễn phí", ở mục "Bạn là" chọn Phụ huynh, điền họ tên, tên hiển thị (ví dụ "Bố Minh"), email và mật khẩu rồi bấm "Tạo tài khoản phụ huynh".'],
        images: [img('ph-register', 'Trang đăng ký với lựa chọn Phụ huynh')],
      },
      {
        id: 'lien-ket', title: '2. Liên kết với con',
        text: [
          'Mở ứng dụng của con → Hồ sơ để lấy mã liên kết (dạng AGEN-XXXX). Trên trang Phụ huynh, bấm "Liên kết với con", nhập mã và quan hệ (bố, mẹ…) rồi bấm "Liên kết". Có thể liên kết nhiều con.',
        ],
        images: [img('ph-link', 'Ô nhập mã liên kết với con trên trang phụ huynh')],
      },
      {
        id: 'bao-cao', title: '3. Đọc báo cáo tuần',
        text: [
          'Chọn tên con để xem báo cáo 7 ngày gần nhất: số buổi học, XP tuần, phút học, chuỗi ngày, độ chính xác; hồ sơ sáu kỹ năng; và ba nhận xét bằng tiếng Việt — con đã tiến bộ gì, con cần hỗ trợ gì, phụ huynh nên làm gì.',
          'Nếu con học trong lớp có giáo viên dùng ứng dụng, mục "Bài kiểm tra ở lớp" cho biết con đã làm bài kiểm tra nào, điểm của con và điểm trung bình lớp.',
        ],
        images: [
          img('ph-dashboard', 'Trang phụ huynh với báo cáo tuần của con: buổi học, XP, phút học, chuỗi ngày, độ chính xác'),
          img('ph-mobile', 'Trang phụ huynh trên điện thoại'),
        ],
      },
      {
        id: 'pdf', title: '4. Tải báo cáo PDF để in',
        text: ['Bấm "Tải PDF" trong báo cáo để mở bản in gọn gàng, rồi chọn "Lưu dưới dạng PDF" hoặc in ra giấy — tiện trao đổi với giáo viên hoặc lưu theo dõi.'],
        images: [img('ph-pdf', 'Báo cáo tuần bản in PDF với hồ sơ kỹ năng và nhận xét')],
      },
      {
        id: 'canh-bao', title: '5. Nhận báo cáo và cảnh báo tự động',
        text: [
          'Bật "Email báo cáo tuần và cảnh báo nghỉ học" để nhận báo cáo vào Chủ nhật và cảnh báo khi con nghỉ 2 ngày liên tiếp. Có thể nhận thêm qua thông báo trên điện thoại (trình duyệt hoặc ứng dụng) và Zalo khi các kênh này được bật.',
          'Gói gia đình: một lần thanh toán, tối đa 4 con được dùng Premium.',
        ],
      },
    ],
    faqs: [
      { q: 'Con có thấy bố mẹ đang theo dõi không?', a: 'Việc liên kết cần mã từ tài khoản của con, nên con biết. Báo cáo chỉ gồm số liệu học tập, không gồm nội dung trò chuyện riêng.' },
      { q: 'Một tài khoản phụ huynh theo dõi được mấy con?', a: 'Theo dõi được nhiều con; gói gia đình phủ Premium cho tối đa 4 con đã liên kết.' },
      { q: 'Bỏ liên kết thế nào?', a: 'Trong báo cáo của con, bấm "Huỷ liên kết". Có thể liên kết lại bằng mã của con bất cứ lúc nào.' },
    ],
    related: ['hoc-sinh', 'nguoi-hoc', 'giao-vien'],
  },
  {
    slug: 'giao-vien',
    icon: 'class',
    cardTitle: 'Giáo viên & doanh nghiệp',
    cardDesc: 'Tạo lớp bằng mã, giao bài, bài kiểm tra định kỳ, chấm rubric, xem tiến bộ và xuất báo cáo.',
    title: 'Hướng dẫn sử dụng cho giáo viên và doanh nghiệp',
    description: 'Hướng dẫn giáo viên, trung tâm và doanh nghiệp dùng AI AGENT ENGLISH: tạo lớp, giao bài tuần, bài kiểm tra lặp hằng tháng, in bảng điểm, biểu đồ tiến bộ band, nhận xét và báo cáo.',
    h1: 'Hướng dẫn sử dụng cho giáo viên và doanh nghiệp',
    lead: 'Bạn tạo lớp và giao việc; AI tạo bài đúng trình độ từng học viên và chấm ngay; bạn xem điểm, chấm lại khi cần và xuất báo cáo — tất cả ở một nơi.',
    steps: [
      {
        id: 'tao-nhom', title: '1. Tạo tài khoản và tạo nhóm',
        text: [
          'Đăng ký với vai trò "Giáo viên / Công ty". Ở trang Nhóm của tôi, nhập tên nhóm, chọn Lớp học hoặc Doanh nghiệp rồi bấm "Tạo nhóm". Mỗi nhóm có một mã (LOP-XXXX hoặc CTY-XXXX) để học viên tham gia.',
          'Gói theo ghế giúp các thành viên trong nhóm được dùng Premium; xem ở mục "Gói lớp học / doanh nghiệp theo ghế".',
        ],
        images: [img('gv-home', 'Trang Nhóm của tôi: tạo nhóm lớp học hoặc doanh nghiệp, danh sách nhóm')],
      },
      {
        id: 'giao-bai', title: '2. Gửi mã và giao bài tuần',
        text: [
          'Bấm vào mã nhóm để sao chép và gửi cho học viên; họ nhập mã ở mục Lớp học. Ở "Giao bài tuần", điền tiêu đề, kỹ năng (từ vựng, ngữ pháp, đọc, nghe), chủ đề, hạn nộp và ghi chú. Mỗi học viên nhận bài học do AI tạo theo đúng trình độ; học xong là bài tập được tính hoàn thành.',
        ],
        images: [img('gv-group', 'Trang lớp: mã tham gia, báo cáo PDF/CSV, giao bài tuần và danh sách bài tập')],
      },
      {
        id: 'kiem-tra', title: '3. Bài kiểm tra lớp và bảng điểm',
        text: [
          'Ở "Bài kiểm tra lớp", chọn đề thi thử (Nghe/Đọc hoặc Nói, IELTS/TOEIC), ngày mở và hạn nộp. Cả lớp nhận thông báo; lần làm đầu tiên trong hạn được tính điểm và không tốn lượt thi miễn phí của học viên. Sáng ngày hết hạn, ai chưa làm được nhắc.',
          'Tích "Lặp lại hằng tháng" để hệ thống tự giao đề mới (ưu tiên đề lớp chưa làm) cùng khung ngày vào tháng sau. Bấm vào một bài để xem điểm từng người, rồi "In bảng điểm" để lưu PDF hoặc in.',
        ],
        images: [
          img('gv-tests', 'Bài kiểm tra lớp đang mở với điểm từng học viên, nút in bảng điểm và lặp lại hằng tháng'),
          img('gv-sheet', 'Bảng điểm bài kiểm tra lớp bản in với điểm trung bình, cao nhất, thấp nhất'),
        ],
      },
      {
        id: 'hoc-vien', title: '4. Theo dõi từng học viên',
        text: [
          'Bảng Thành viên cho thấy trình độ, XP tuần, chuỗi ngày, số bài tập đã xong, ai học hôm nay. Bấm tên một học viên để xem bài học, bài viết, bài thi thử, bài thi nói, bài kiểm tra lớp và biểu đồ tiến bộ band IELTS Writing / Speaking theo thời gian.',
          'Mở một bài viết để chấm lại theo rubric 4 tiêu chí IELTS (band tổng làm tròn theo luật IELTS) và gửi nhận xét — học viên nhận thông báo ngay. Có thể cấp chứng nhận hoàn thành có mã xác thực.',
        ],
        images: [
          img('gv-members', 'Bảng thành viên lớp với XP tuần, chuỗi ngày, bài tập và gói'),
          img('gv-charts', 'Biểu đồ tiến bộ IELTS Writing của một học viên theo 4 tiêu chí'),
        ],
      },
      {
        id: 'bao-cao', title: '5. Báo cáo nhóm và câu lạc bộ nói',
        text: [
          'Bấm "Báo cáo · PDF / CSV" để in báo cáo cả nhóm hoặc tải file CSV mở bằng Excel (XP, chuỗi ngày, bài tập, điểm bài kiểm tra). Mục "Câu lạc bộ nói hằng tuần" đặt lịch buổi nói cố định cho lớp: phòng tự mở, cả lớp được nhắc trước giờ học.',
        ],
        images: [img('gv-report', 'Báo cáo lớp bản in với tiến độ từng thành viên và bài tập đã giao')],
      },
    ],
    faqs: [
      { q: 'Học viên chưa có tài khoản thì sao?', a: 'Học viên tự đăng ký (miễn phí) rồi nhập mã lớp. Một học viên có thể ở nhiều lớp.' },
      { q: 'Có xuất hoá đơn cho doanh nghiệp không?', a: 'Có. Khi thanh toán gói theo ghế, doanh nghiệp điền thông tin xuất hoá đơn VAT; biên nhận xem được trong tài khoản.' },
      { q: 'Dừng bài kiểm tra lặp hằng tháng thế nào?', a: 'Mở bài kiểm tra mới nhất trong danh sách và bấm "Đang lặp hằng tháng · Dừng".' },
    ],
    related: ['nguoi-hoc', 'phu-huynh', 'hoc-sinh'],
  },
];

export const GUIDE_BY_SLUG: Record<string, Guide> = Object.fromEntries(GUIDES.map(g => [g.slug, g]));
