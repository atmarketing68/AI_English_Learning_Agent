"""
G10 · Học qua podcast / video ngắn.

Static episodes (no LLM): a short podcast-style conversation or talk with a
Vietnamese line-by-line translation, key words, and comprehension questions.
Audio is the server voice (`/audio/tts`) per speaker, so nothing is hosted.
An episode may carry a `youtube_id` + `start`/`end` seconds; the web player
then embeds that video above the transcript (the transcript must match it).
"""
from __future__ import annotations

from copy import deepcopy

XP_PER_CORRECT = 3
XP_CAP = 15
GEMS_PERFECT = 3


def _l(speaker: str, text: str, vi: str) -> dict:
    return {"speaker": speaker, "text": text, "vi": vi}


EPISODES: list[dict] = [
    {
        "id": "pod-coffee-order", "kind": "podcast", "level": "A2", "minutes": 3, "topic": "Đời sống",
        "title": "At the coffee shop", "title_vi": "Gọi đồ ở quán cà phê",
        "description_vi": "Hội thoại ngắn khi gọi đồ uống, hỏi giá và trả tiền — câu dùng được ngay hôm nay.",
        "youtube_id": None,
        "lines": [
            _l("Barista", "Hi there! What can I get for you today?", "Chào bạn! Hôm nay mình lấy gì cho bạn?"),
            _l("Minh", "Hi! Can I have an iced milk coffee, please?", "Chào! Cho mình một cà phê sữa đá nhé."),
            _l("Barista", "Sure. Small or large?", "Được ạ. Cỡ nhỏ hay lớn?"),
            _l("Minh", "Large, please. And less sugar, if possible.", "Cỡ lớn. Và ít đường nếu được."),
            _l("Barista", "No problem. Anything to eat? Our banana bread is fresh this morning.", "Không vấn đề gì. Bạn ăn gì không? Bánh chuối sáng nay mới ra lò."),
            _l("Minh", "Oh, that sounds good. One slice, please. How much is that?", "Nghe ngon đấy. Cho mình một miếng. Tổng bao nhiêu?"),
            _l("Barista", "That's sixty-five thousand dong altogether. Cash or card?", "Tổng cộng sáu mươi lăm nghìn. Tiền mặt hay thẻ?"),
            _l("Minh", "Can I pay by QR code?", "Mình trả bằng mã QR được không?"),
            _l("Barista", "Of course. Here you go. Your drink will be ready in two minutes.", "Tất nhiên. Đây ạ. Đồ uống sẽ xong trong hai phút."),
        ],
        "vocab": [
            {"word": "iced", "definition": "có đá, lạnh"},
            {"word": "slice", "definition": "miếng, lát"},
            {"word": "altogether", "definition": "tổng cộng"},
            {"word": "less sugar", "definition": "ít đường"},
        ],
        "questions": [
            {"id": "q1", "prompt": "What size drink does Minh order?", "options": ["small", "large", "medium"], "answer": 1, "explanation_vi": "Minh nói \"Large, please.\""},
            {"id": "q2", "prompt": "What does Minh ask for?", "options": ["more ice", "less sugar", "extra milk"], "answer": 1, "explanation_vi": "\"And less sugar, if possible.\""},
            {"id": "q3", "prompt": "How does Minh pay?", "options": ["by cash", "by card", "by QR code"], "answer": 2, "explanation_vi": "\"Can I pay by QR code?\" — người bán đồng ý."},
            {"id": "q4", "prompt": "How much is the total?", "options": ["55,000 dong", "65,000 dong", "75,000 dong"], "answer": 1, "explanation_vi": "\"That's sixty-five thousand dong altogether.\""},
        ],
    },
    {
        "id": "pod-weekend-dalat", "kind": "podcast", "level": "A2", "minutes": 3, "topic": "Du lịch",
        "title": "A weekend in Da Lat", "title_vi": "Cuối tuần ở Đà Lạt",
        "description_vi": "Hai người bạn kể về chuyến đi Đà Lạt: thời tiết, đồ ăn và điều thích nhất. Luyện thì quá khứ đơn.",
        "youtube_id": None,
        "lines": [
            _l("Lan", "Hey Tom, how was your weekend? You look relaxed!", "Này Tom, cuối tuần thế nào? Trông cậu thư thái ghê!"),
            _l("Tom", "It was great. I went to Da Lat with my sister.", "Tuyệt lắm. Mình đi Đà Lạt với chị gái."),
            _l("Lan", "Nice! Was it cold?", "Hay đấy! Có lạnh không?"),
            _l("Tom", "Yes, very cold at night. We wore jackets all the time.", "Có, đêm rất lạnh. Bọn mình mặc áo khoác suốt."),
            _l("Lan", "What did you eat?", "Cậu đã ăn gì?"),
            _l("Tom", "We tried grilled rice paper at the night market. It was delicious and very cheap.", "Bọn mình ăn bánh tráng nướng ở chợ đêm. Ngon và rẻ lắm."),
            _l("Lan", "What was your favourite part of the trip?", "Cậu thích nhất điều gì trong chuyến đi?"),
            _l("Tom", "Watching the sunrise over the hills. We got up at five, but it was worth it.", "Ngắm bình minh trên đồi. Bọn mình dậy lúc năm giờ, nhưng rất đáng."),
            _l("Lan", "That sounds lovely. I want to go next month!", "Nghe thật tuyệt. Tháng sau mình muốn đi!"),
        ],
        "vocab": [
            {"word": "relaxed", "definition": "thư thái, thoải mái"},
            {"word": "grilled", "definition": "nướng"},
            {"word": "sunrise", "definition": "bình minh"},
            {"word": "worth it", "definition": "đáng công, xứng đáng"},
        ],
        "questions": [
            {"id": "q1", "prompt": "Who did Tom go to Da Lat with?", "options": ["his friend", "his sister", "his parents"], "answer": 1, "explanation_vi": "\"I went to Da Lat with my sister.\""},
            {"id": "q2", "prompt": "What was the weather like at night?", "options": ["hot", "rainy", "very cold"], "answer": 2, "explanation_vi": "\"Yes, very cold at night.\""},
            {"id": "q3", "prompt": "Where did they eat grilled rice paper?", "options": ["at the night market", "at the hotel", "in a restaurant"], "answer": 0, "explanation_vi": "\"…grilled rice paper at the night market.\""},
            {"id": "q4", "prompt": "Why did they get up at five?", "options": ["to catch a bus", "to watch the sunrise", "to go to the market"], "answer": 1, "explanation_vi": "Họ dậy sớm để ngắm bình minh trên đồi."},
        ],
    },
    {
        "id": "pod-work-from-home", "kind": "podcast", "level": "B1", "minutes": 4, "topic": "Công việc",
        "title": "Working from home: pros and cons", "title_vi": "Làm việc tại nhà: lợi và hại",
        "description_vi": "Hai đồng nghiệp tranh luận nhẹ nhàng về làm việc tại nhà. Học cách nêu ý kiến và đưa lý do.",
        "youtube_id": None,
        "lines": [
            _l("Anna", "So, David, you've been working from home three days a week now. How's it going?", "David này, giờ anh làm ở nhà ba ngày một tuần rồi. Thế nào?"),
            _l("David", "Honestly, better than I expected. I save almost two hours of commuting every day.", "Thật lòng là tốt hơn mình nghĩ. Mỗi ngày mình tiết kiệm gần hai tiếng đi lại."),
            _l("Anna", "That's a big advantage. But don't you feel lonely sometimes?", "Lợi thế lớn đấy. Nhưng đôi khi anh không thấy cô đơn à?"),
            _l("David", "A little. I miss chatting with the team over lunch. Video calls aren't quite the same.", "Một chút. Mình nhớ những lúc nói chuyện với nhóm khi ăn trưa. Gọi video không hẳn như vậy."),
            _l("Anna", "For me, the hardest part would be separating work and home life.", "Với mình, khó nhất có lẽ là tách bạch công việc và cuộc sống ở nhà."),
            _l("David", "You're right. At first I kept checking emails at ten p.m. Now I switch off my laptop at six, no matter what.", "Đúng vậy. Lúc đầu mình cứ kiểm tra email lúc mười giờ tối. Giờ thì sáu giờ là tắt máy, bất kể thế nào."),
            _l("Anna", "Do you think you're more productive at home?", "Anh có nghĩ ở nhà mình làm hiệu quả hơn không?"),
            _l("David", "For focused tasks like writing reports, definitely. For brainstorming, the office works better.", "Với việc cần tập trung như viết báo cáo thì chắc chắn rồi. Còn động não ý tưởng thì văn phòng tốt hơn."),
            _l("Anna", "So a mix of both is probably the best solution.", "Vậy kết hợp cả hai có lẽ là giải pháp tốt nhất."),
        ],
        "vocab": [
            {"word": "commuting", "definition": "việc đi lại giữa nhà và nơi làm"},
            {"word": "productive", "definition": "làm việc hiệu quả"},
            {"word": "switch off", "definition": "tắt (máy); ngừng nghĩ về công việc"},
            {"word": "brainstorming", "definition": "động não, cùng nghĩ ý tưởng"},
        ],
        "questions": [
            {"id": "q1", "prompt": "How much time does David save each day?", "options": ["about one hour", "almost two hours", "three hours"], "answer": 1, "explanation_vi": "\"I save almost two hours of commuting every day.\""},
            {"id": "q2", "prompt": "What does David miss about the office?", "options": ["the free coffee", "chatting with the team over lunch", "his big desk"], "answer": 1, "explanation_vi": "\"I miss chatting with the team over lunch.\""},
            {"id": "q3", "prompt": "What does David do at six p.m. now?", "options": ["checks emails", "switches off his laptop", "calls his team"], "answer": 1, "explanation_vi": "\"Now I switch off my laptop at six, no matter what.\""},
            {"id": "q4", "prompt": "According to David, which task is better in the office?", "options": ["writing reports", "brainstorming", "answering emails"], "answer": 1, "explanation_vi": "\"For brainstorming, the office works better.\""},
            {"id": "q5", "prompt": "What do they agree on at the end?", "options": ["Everyone should work from home.", "A mix of home and office is best.", "Offices are always better."], "answer": 1, "explanation_vi": "\"So a mix of both is probably the best solution.\""},
        ],
    },
    {
        "id": "pod-sleep-learning", "kind": "podcast", "level": "B1", "minutes": 4, "topic": "Sức khoẻ",
        "title": "Why sleep helps you learn", "title_vi": "Vì sao ngủ đủ giúp học tốt hơn",
        "description_vi": "Bài nói ngắn về giấc ngủ và trí nhớ, kèm mẹo ôn từ vựng trước khi ngủ.",
        "youtube_id": None,
        "lines": [
            _l("Narrator", "Have you ever studied late into the night, only to forget everything the next morning?", "Bạn đã bao giờ học đến khuya rồi sáng hôm sau quên sạch chưa?"),
            _l("Narrator", "Scientists say that sleep is not just rest for the body. It is also when the brain organises what we learned during the day.", "Các nhà khoa học nói giấc ngủ không chỉ để cơ thể nghỉ ngơi. Đó còn là lúc não sắp xếp những gì ta học trong ngày."),
            _l("Narrator", "During deep sleep, new memories are replayed and moved into long-term storage.", "Trong giấc ngủ sâu, ký ức mới được 'phát lại' và chuyển vào trí nhớ dài hạn."),
            _l("Narrator", "That is why a short review before bed can be so effective. Ten minutes with your vocabulary list is enough.", "Vì vậy ôn lại một chút trước khi ngủ rất hiệu quả. Mười phút với danh sách từ vựng là đủ."),
            _l("Narrator", "On the other hand, staying up all night to cram usually backfires. You feel tired, and you remember less.", "Ngược lại, thức trắng đêm để nhồi nhét thường phản tác dụng. Bạn mệt và nhớ ít hơn."),
            _l("Narrator", "Most adults need seven to nine hours of sleep. Teenagers need even more.", "Phần lớn người lớn cần bảy đến chín tiếng ngủ. Thanh thiếu niên còn cần nhiều hơn."),
            _l("Narrator", "So tonight, put your phone away, review a few words, and get a good night's sleep. Your brain will do the rest.", "Vậy tối nay, cất điện thoại, ôn vài từ và ngủ một giấc ngon. Não bạn sẽ lo phần còn lại."),
        ],
        "vocab": [
            {"word": "long-term", "definition": "dài hạn"},
            {"word": "cram", "definition": "học nhồi nhét"},
            {"word": "backfire", "definition": "phản tác dụng"},
            {"word": "replay", "definition": "phát lại, lặp lại"},
        ],
        "questions": [
            {"id": "q1", "prompt": "What does the brain do during sleep, according to the talk?", "options": ["It stops working.", "It organises what we learned.", "It forgets new words."], "answer": 1, "explanation_vi": "\"…the brain organises what we learned during the day.\""},
            {"id": "q2", "prompt": "How long should a review before bed be?", "options": ["about ten minutes", "one hour", "all night"], "answer": 0, "explanation_vi": "\"Ten minutes with your vocabulary list is enough.\""},
            {"id": "q3", "prompt": "What happens when you stay up all night to cram?", "options": ["You remember more.", "You feel tired and remember less.", "You sleep better."], "answer": 1, "explanation_vi": "\"You feel tired, and you remember less.\""},
            {"id": "q4", "prompt": "How much sleep do most adults need?", "options": ["five to six hours", "seven to nine hours", "ten to twelve hours"], "answer": 1, "explanation_vi": "\"Most adults need seven to nine hours of sleep.\""},
        ],
    },
    {
        "id": "pod-electric-motorbikes", "kind": "podcast", "level": "B2", "minutes": 5, "topic": "Xã hội",
        "title": "Will cities switch to electric motorbikes?", "title_vi": "Thành phố có chuyển sang xe máy điện?",
        "description_vi": "Phỏng vấn ngắn về xe máy điện ở đô thị: lợi ích, trở ngại và điều người dùng quan tâm. Luyện nghe ý kiến hai chiều.",
        "youtube_id": None,
        "lines": [
            _l("Host", "Welcome back to City Talk. Today we're asking whether electric motorbikes could replace petrol bikes in our cities. With me is urban planner Hoa.", "Chào mừng trở lại City Talk. Hôm nay chúng ta bàn liệu xe máy điện có thể thay xe xăng ở đô thị. Cùng tôi là chuyên gia quy hoạch đô thị Hoa."),
            _l("Hoa", "Thanks for having me. The short answer is: gradually, yes, but not overnight.", "Cảm ơn đã mời tôi. Trả lời ngắn gọn: dần dần thì có, nhưng không thể ngay lập tức."),
            _l("Host", "What's the main benefit people notice first?", "Lợi ích chính mà người ta thấy đầu tiên là gì?"),
            _l("Hoa", "The noise. Or rather, the lack of it. Streets become noticeably quieter, and there are no exhaust fumes at traffic lights.", "Tiếng ồn. Hay đúng hơn là không có tiếng ồn. Đường phố yên tĩnh hơn rõ rệt, và không còn khói xả ở đèn đỏ."),
            _l("Host", "So why isn't everyone switching already?", "Vậy sao mọi người chưa chuyển hết?"),
            _l("Hoa", "Two reasons. First, charging. Many people live in apartments without a place to plug in. Second, the upfront price is still higher, even though running costs are lower.", "Hai lý do. Thứ nhất là sạc. Nhiều người sống ở chung cư không có chỗ cắm sạc. Thứ hai, giá mua ban đầu vẫn cao hơn dù chi phí sử dụng thấp hơn."),
            _l("Host", "What could change that?", "Điều gì có thể thay đổi tình hình?"),
            _l("Hoa", "Battery-swap stations are promising. You ride in, exchange an empty battery for a full one in under a minute, and ride out.", "Trạm đổi pin rất hứa hẹn. Bạn chạy vào, đổi pin hết lấy pin đầy trong chưa tới một phút rồi chạy tiếp."),
            _l("Host", "And your advice for listeners thinking about buying one?", "Lời khuyên của chị cho thính giả đang định mua?"),
            _l("Hoa", "Check where you'll charge it before you check the colour. That one decision matters more than anything else.", "Hãy xem mình sẽ sạc ở đâu trước khi chọn màu. Quyết định đó quan trọng hơn mọi thứ khác."),
        ],
        "vocab": [
            {"word": "gradually", "definition": "dần dần"},
            {"word": "exhaust fumes", "definition": "khói xả (của xe)"},
            {"word": "upfront price", "definition": "giá phải trả ban đầu"},
            {"word": "promising", "definition": "đầy hứa hẹn"},
        ],
        "questions": [
            {"id": "q1", "prompt": "What is Hoa's short answer to the main question?", "options": ["Never.", "Gradually, but not overnight.", "Yes, very soon."], "answer": 1, "explanation_vi": "\"gradually, yes, but not overnight.\""},
            {"id": "q2", "prompt": "Which benefit do people notice first?", "options": ["cheaper parking", "quieter streets", "faster travel"], "answer": 1, "explanation_vi": "\"The noise. Or rather, the lack of it.\""},
            {"id": "q3", "prompt": "What is one problem for people living in apartments?", "options": ["no place to charge", "no parking at work", "high insurance"], "answer": 0, "explanation_vi": "\"Many people live in apartments without a place to plug in.\""},
            {"id": "q4", "prompt": "What does Hoa say about battery-swap stations?", "options": ["They are too slow.", "They are promising.", "They are expensive to use."], "answer": 1, "explanation_vi": "\"Battery-swap stations are promising.\""},
            {"id": "q5", "prompt": "What should buyers check first?", "options": ["the colour", "where they will charge it", "the top speed"], "answer": 1, "explanation_vi": "\"Check where you'll charge it before you check the colour.\""},
        ],
    },
    {
        "id": "pod-interview-tips", "kind": "podcast", "level": "B2", "minutes": 5, "topic": "Sự nghiệp",
        "title": "A recruiter's interview tips", "title_vi": "Mẹo phỏng vấn từ nhà tuyển dụng",
        "description_vi": "Nhà tuyển dụng chia sẻ cách trả lời 'Tell me about yourself' và câu hỏi điểm yếu. Học cụm từ dùng được khi đi phỏng vấn.",
        "youtube_id": None,
        "lines": [
            _l("Host", "Our guest today has interviewed hundreds of candidates. Welcome, Mark.", "Khách mời hôm nay đã phỏng vấn hàng trăm ứng viên. Chào mừng anh Mark."),
            _l("Mark", "Happy to be here.", "Rất vui được có mặt."),
            _l("Host", "Let's start with the classic: 'Tell me about yourself.' What do recruiters actually want to hear?", "Bắt đầu với câu kinh điển: 'Hãy giới thiệu về bản thân.' Nhà tuyển dụng thực sự muốn nghe gì?"),
            _l("Mark", "Not your life story. Give a ninety-second answer in three parts: what you do now, one achievement you're proud of, and why this role is the logical next step.", "Không phải cả cuộc đời bạn. Trả lời trong chín mươi giây gồm ba phần: hiện bạn làm gì, một thành tích bạn tự hào, và vì sao vị trí này là bước tiếp theo hợp lý."),
            _l("Host", "And the dreaded weakness question?", "Còn câu hỏi đáng sợ về điểm yếu?"),
            _l("Mark", "Pick a real weakness that isn't central to the job, then explain what you're doing about it. 'I used to find public speaking stressful, so I joined a speaking club, and now I present to clients every month.'", "Chọn một điểm yếu thật nhưng không cốt lõi với công việc, rồi nói bạn đang khắc phục ra sao. 'Tôi từng thấy nói trước đám đông rất áp lực, nên tôi tham gia câu lạc bộ nói, và giờ tôi thuyết trình cho khách hàng mỗi tháng.'"),
            _l("Host", "What's the most common mistake you see?", "Lỗi phổ biến nhất anh thấy là gì?"),
            _l("Mark", "Not asking any questions at the end. It suggests you're not really interested. Prepare at least two, like 'What does success look like in the first three months?'", "Không hỏi câu nào ở cuối. Điều đó cho thấy bạn không thực sự quan tâm. Hãy chuẩn bị ít nhất hai câu, như 'Thành công trong ba tháng đầu trông như thế nào?'"),
            _l("Host", "Great advice. Thanks, Mark.", "Lời khuyên tuyệt vời. Cảm ơn anh Mark."),
        ],
        "vocab": [
            {"word": "candidate", "definition": "ứng viên"},
            {"word": "achievement", "definition": "thành tích"},
            {"word": "dreaded", "definition": "đáng sợ, ai cũng ngại"},
            {"word": "logical next step", "definition": "bước tiếp theo hợp lý"},
        ],
        "questions": [
            {"id": "q1", "prompt": "How long should your answer to 'Tell me about yourself' be?", "options": ["about ninety seconds", "five minutes", "ten seconds"], "answer": 0, "explanation_vi": "\"Give a ninety-second answer in three parts.\""},
            {"id": "q2", "prompt": "Which is NOT one of the three parts Mark suggests?", "options": ["what you do now", "your family background", "why this role is the next step"], "answer": 1, "explanation_vi": "Ba phần: việc hiện tại, một thành tích, lý do chọn vị trí — không có gia đình."},
            {"id": "q3", "prompt": "What kind of weakness should you choose?", "options": ["one that is central to the job", "a real one that isn't central to the job", "a fake one"], "answer": 1, "explanation_vi": "\"Pick a real weakness that isn't central to the job.\""},
            {"id": "q4", "prompt": "What is the most common mistake?", "options": ["arriving late", "not asking questions at the end", "talking too fast"], "answer": 1, "explanation_vi": "\"Not asking any questions at the end.\""},
        ],
    },
]

_BY_ID = {e["id"]: e for e in EPISODES}


def list_episodes(db=None) -> list[dict]:
    """Hand-written episodes, then (with a db) G11 AI episodes an admin approved, newest first."""
    if db is None:
        return EPISODES
    from app.services.podcast_generator import approved_episodes
    return EPISODES + approved_episodes(db)


def get_episode(episode_id: str, db=None) -> dict | None:
    if episode_id in _BY_ID or db is None:
        return _BY_ID.get(episode_id)
    from app.services.podcast_generator import episode_by_public_id
    return episode_by_public_id(db, episode_id)


def public_episode(ep: dict) -> dict:
    out = deepcopy(ep)
    for q in out["questions"]:
        q.pop("answer", None)
        q.pop("explanation_vi", None)
    return out


def grade(ep: dict, answers: dict) -> dict:
    details, correct = [], 0
    for q in ep["questions"]:
        given = answers.get(q["id"])
        try:
            ok = int(given) == q["answer"]
        except (TypeError, ValueError):
            ok = False
        correct += ok
        details.append({"id": q["id"], "correct": ok, "expected": q["options"][q["answer"]], "explanation_vi": q["explanation_vi"]})
    total = len(ep["questions"])
    return {"correct": correct, "total": total, "pct": round(correct / total * 100, 1) if total else 0.0, "details": details}
