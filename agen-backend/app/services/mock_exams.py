"""
G8 · Thư viện đề thi thử IELTS / TOEIC (Listening + Reading) theo định dạng thật.

The bank is static (no LLM): each test is a few sections in the real format
(IELTS form completion / multiple choice / True-False-Not Given / sentence
completion; TOEIC Parts 2–7). Listening sections carry a script as speaker
lines; the web app reads them with the server voice (`playText`) once, like
the real test. Grading is deterministic and the band / score is an estimate
scaled from the official raw-score tables.
"""
from __future__ import annotations

import re
from copy import deepcopy

EXAM_IELTS = "ielts"
EXAM_TOEIC = "toeic"

# Raw score (out of 40) → IELTS band, from the public conversion tables.
_IELTS_LISTENING_BANDS = [(39, 9.0), (37, 8.5), (35, 8.0), (32, 7.5), (30, 7.0), (26, 6.5), (23, 6.0), (18, 5.5), (16, 5.0), (13, 4.5), (10, 4.0), (8, 3.5), (6, 3.0), (4, 2.5), (0, 2.0)]
_IELTS_READING_BANDS = [(39, 9.0), (37, 8.5), (35, 8.0), (33, 7.5), (30, 7.0), (27, 6.5), (23, 6.0), (19, 5.5), (15, 5.0), (13, 4.5), (10, 4.0), (8, 3.5), (6, 3.0), (4, 2.5), (0, 2.0)]

XP_PER_CORRECT = 3
XP_CAP = 40
GEMS_GOOD_SCORE = 8          # gems when ≥ 70 %
FREE_DAILY_ATTEMPTS = 1      # free accounts: one mock test a day


def _lines(*pairs: tuple[str, str]) -> list[dict]:
    """(speaker, text) pairs → audio lines. Women use the female voice, men the male voice."""
    out = []
    for speaker, text in pairs:
        voice = "male" if speaker.lower() in ("man", "male", "boy", "mr", "tom", "david", "ben", "mark", "peter", "james", "receptionist (m)", "narrator") else "female"
        out.append({"speaker": speaker, "text": text, "voice": voice})
    return out


EXAMS: list[dict] = [
    # ────────────────────────────────────────────────────────────────────
    {
        "id": "ielts-listening-1", "exam": EXAM_IELTS, "skill": "listening", "minutes": 12,
        "title": "IELTS Listening · Mini Test 1",
        "description": "3 phần rút gọn theo đúng dạng đề thật: điền form (Section 1), bài nói một người (Section 2), hội thoại học thuật (Section 3). Mỗi phần chỉ nghe một lần.",
        "sections": [
            {
                "id": "s1", "title": "Section 1 · Enrolling in a language course",
                "instructions": "Complete the form below. Write NO MORE THAN TWO WORDS AND/OR A NUMBER for each answer.",
                "audio": _lines(
                    ("Receptionist", "Good morning, Greenway Language Centre. How can I help you?"),
                    ("Woman", "Hi, I'd like to enrol in an evening English course, please."),
                    ("Receptionist", "Of course. Can I take your name first?"),
                    ("Woman", "Yes, it's Laura Mitchell. That's M-I-T-C-H-E-L-L."),
                    ("Receptionist", "Thank you, Laura. And which course are you interested in?"),
                    ("Woman", "The intermediate course, the one that starts in September."),
                    ("Receptionist", "Right. That class meets on Tuesdays and Thursdays, from seven to nine in the evening."),
                    ("Woman", "Tuesdays and Thursdays. That's fine. How much is the course?"),
                    ("Receptionist", "It's three hundred and twenty pounds for the ten-week term, and that includes the course book."),
                    ("Woman", "Three hundred and twenty. Okay. And where exactly are the classes held?"),
                    ("Receptionist", "In the main building on Park Road, room fourteen. There's parking behind the building."),
                    ("Woman", "Park Road, room fourteen. Great. Can I pay by card?"),
                    ("Receptionist", "Yes, or by bank transfer. I just need a contact number for you."),
                    ("Woman", "It's oh seven seven double two, four six nine, three one five."),
                    ("Receptionist", "Lovely. You'll get a confirmation email within a day."),
                ),
                "questions": [
                    {"id": "q1", "type": "gap", "prompt": "Name: Laura ______", "answer": ["Mitchell"], "explanation_vi": "Cô ấy đánh vần tên: M-I-T-C-H-E-L-L."},
                    {"id": "q2", "type": "gap", "prompt": "Course level: ______", "answer": ["intermediate"], "explanation_vi": "\"The intermediate course, the one that starts in September.\""},
                    {"id": "q3", "type": "gap", "prompt": "Class days: Tuesdays and ______", "answer": ["Thursdays", "Thursday"], "explanation_vi": "\"That class meets on Tuesdays and Thursdays.\""},
                    {"id": "q4", "type": "gap", "prompt": "Fee for the term: £ ______", "answer": ["320", "three hundred and twenty"], "explanation_vi": "\"It's three hundred and twenty pounds for the ten-week term.\""},
                    {"id": "q5", "type": "gap", "prompt": "Location: main building on ______ Road, room 14", "answer": ["Park"], "explanation_vi": "\"In the main building on Park Road, room fourteen.\""},
                ],
            },
            {
                "id": "s2", "title": "Section 2 · The new community library",
                "instructions": "Choose the correct letter, A, B or C.",
                "audio": _lines(
                    ("Woman", "Welcome, everyone, to the opening tour of the Riverside Community Library. I'm Helen, the head librarian. The library used to be a small room above the post office, but after two years of building work we now have this three-storey building. The ground floor is for children and families, with a story corner and a play area. The first floor holds the main adult collection and a quiet study room with forty desks. And on the top floor there's a café and a meeting room that local groups can book for free. Opening hours are nine to eight on weekdays, and ten to four on Saturdays. We're closed on Sundays. One thing I'd like to mention is membership. It used to cost five pounds a year, but from this month membership is completely free for everyone who lives in the town. You just need to bring something with your address on it, like a utility bill. Finally, our most popular new service: you can now borrow e-books and audiobooks through our app, up to six at a time, and they return themselves automatically, so there are no late fees."),
                ),
                "questions": [
                    {"id": "q6", "type": "mc", "prompt": "Where was the library before the new building opened?", "options": ["in a room above the post office", "in the town hall", "in a school"], "answer": 0, "explanation_vi": "\"The library used to be a small room above the post office.\""},
                    {"id": "q7", "type": "mc", "prompt": "What is on the top floor?", "options": ["the children's area", "a café and a meeting room", "a study room with 40 desks"], "answer": 1, "explanation_vi": "Tầng trên cùng có quán cà phê và phòng họp; phòng học 40 bàn ở tầng 1."},
                    {"id": "q8", "type": "mc", "prompt": "What has changed about membership?", "options": ["It now costs £5 a year.", "It is free for local residents.", "It requires a passport."], "answer": 1, "explanation_vi": "\"From this month membership is completely free for everyone who lives in the town.\""},
                ],
            },
            {
                "id": "s3", "title": "Section 3 · Planning a research project",
                "instructions": "Choose the correct letter, A, B or C.",
                "audio": _lines(
                    ("Man", "So, Anna, for our psychology project, I was thinking we could do a survey about sleep and exam results."),
                    ("Woman", "That's a good topic, Tom, but a survey on its own might be too simple. Our tutor said she wants to see some analysis, not just numbers."),
                    ("Man", "True. What if we interview ten students in detail as well, then compare the two sets of data?"),
                    ("Woman", "I like that. The interviews will give us the reasons behind the numbers. The problem is time. Interviews take ages to write up."),
                    ("Man", "We could record them and use the transcription software in the library. That cuts the writing time in half."),
                    ("Woman", "Perfect. And for the survey, let's use the online form rather than paper. Last time half the paper forms came back blank."),
                    ("Man", "Agreed. I'll draft the questions tonight and you can check them tomorrow before we send anything out."),
                ),
                "questions": [
                    {"id": "q9", "type": "mc", "prompt": "Why does Anna think a survey alone is not enough?", "options": ["The tutor wants analysis, not only figures.", "Students will not answer honestly.", "Surveys are expensive to run."], "answer": 0, "explanation_vi": "\"Our tutor said she wants to see some analysis, not just numbers.\""},
                    {"id": "q10", "type": "mc", "prompt": "How will they save time with the interviews?", "options": ["by interviewing fewer students", "by using transcription software", "by asking the tutor for help"], "answer": 1, "explanation_vi": "\"We could record them and use the transcription software in the library.\""},
                ],
            },
        ],
    },
    # ────────────────────────────────────────────────────────────────────
    {
        "id": "ielts-reading-1", "exam": EXAM_IELTS, "skill": "reading", "minutes": 15,
        "title": "IELTS Reading · Mini Test 1",
        "description": "Một bài đọc học thuật ngắn với ba dạng câu hỏi hay gặp: True / False / Not Given, hoàn thành câu và trắc nghiệm.",
        "sections": [
            {
                "id": "s1", "title": "Passage · The quiet rise of urban farming",
                "instructions": "Read the passage and answer questions 1–12.",
                "passage": (
                    "Growing food inside cities is not a new idea. During the Second World War, 'victory gardens' in Britain and the United States produced an estimated 40 per cent of the vegetables eaten at home. "
                    "What is new is the scale and the technology. Today, rooftop greenhouses in Montreal, vertical farms in Singapore and converted warehouses in London grow salad leaves, herbs and strawberries only a few kilometres from the people who eat them.\n\n"
                    "The main attraction is freshness. Lettuce picked in a rooftop greenhouse can reach a supermarket shelf within hours, whereas leaves trucked across a continent may be a week old before they are sold. "
                    "Shorter journeys also mean lower transport emissions, although researchers at Wageningen University point out that this benefit can disappear if a farm relies on artificial lighting powered by fossil fuels. "
                    "In their 2019 study, a vertical farm using grid electricity in a coal-dependent region produced more carbon per kilogram of lettuce than a conventional field farm.\n\n"
                    "Space is another challenge. Land in city centres is expensive, so most urban farms occupy places nobody else wants: flat roofs, disused railway tunnels and the basements of office blocks. "
                    "Growing Underground, a company in south London, raises micro-greens in a former air-raid shelter 33 metres below the streets of Clapham. Because the tunnels keep a steady temperature all year, the farm needs no heating in winter and no cooling in summer.\n\n"
                    "Perhaps the most surprising effect of urban farming is social rather than economic. Community gardens in Detroit, a city that lost more than half its population after 1950, have turned thousands of empty plots into shared growing spaces. "
                    "A survey by Michigan State University found that people who took part reported eating more vegetables and knowing more of their neighbours by name. The food produced is modest in quantity; the connections, residents say, are not."
                ),
                "questions": [
                    {"id": "q1", "type": "tfng", "prompt": "Victory gardens supplied nearly half of the vegetables eaten at home during the Second World War.", "options": ["TRUE", "FALSE", "NOT GIVEN"], "answer": 0, "explanation_vi": "\"an estimated 40 per cent\" ≈ gần một nửa → TRUE."},
                    {"id": "q2", "type": "tfng", "prompt": "Rooftop greenhouses in Montreal mainly grow fruit trees.", "options": ["TRUE", "FALSE", "NOT GIVEN"], "answer": 1, "explanation_vi": "Bài nói họ trồng \"salad leaves, herbs and strawberries\", không phải cây ăn quả → FALSE."},
                    {"id": "q3", "type": "tfng", "prompt": "Urban farms always produce less carbon than field farms.", "options": ["TRUE", "FALSE", "NOT GIVEN"], "answer": 1, "explanation_vi": "Nghiên cứu 2019 cho thấy trang trại thẳng đứng dùng điện than thải nhiều carbon hơn → FALSE."},
                    {"id": "q4", "type": "tfng", "prompt": "Growing Underground sells most of its produce to restaurants.", "options": ["TRUE", "FALSE", "NOT GIVEN"], "answer": 2, "explanation_vi": "Bài không nói họ bán cho ai → NOT GIVEN."},
                    {"id": "q5", "type": "tfng", "prompt": "The temperature in the Clapham tunnels stays almost the same throughout the year.", "options": ["TRUE", "FALSE", "NOT GIVEN"], "answer": 0, "explanation_vi": "\"the tunnels keep a steady temperature all year\" → TRUE."},
                    {"id": "q6", "type": "gap", "prompt": "Lettuce from a rooftop greenhouse can be on a supermarket shelf within ______.", "answer": ["hours"], "explanation_vi": "\"can reach a supermarket shelf within hours\"."},
                    {"id": "q7", "type": "gap", "prompt": "Most urban farms use spaces that nobody else ______.", "answer": ["wants"], "explanation_vi": "\"places nobody else wants\"."},
                    {"id": "q8", "type": "gap", "prompt": "Growing Underground's farm is in a former ______ shelter.", "answer": ["air-raid", "air raid"], "explanation_vi": "\"a former air-raid shelter 33 metres below the streets\"."},
                    {"id": "q9", "type": "gap", "prompt": "Detroit lost more than half its ______ after 1950.", "answer": ["population"], "explanation_vi": "\"a city that lost more than half its population after 1950\"."},
                    {"id": "q10", "type": "mc", "prompt": "According to the Wageningen researchers, when can the transport benefit of urban farming be lost?", "options": ["when farms use artificial light run on fossil fuels", "when lettuce is sold within hours", "when farms are built on rooftops"], "answer": 0, "explanation_vi": "\"this benefit can disappear if a farm relies on artificial lighting powered by fossil fuels\"."},
                    {"id": "q11", "type": "mc", "prompt": "Why does the Clapham farm not need heating?", "options": ["It uses waste heat from the trains.", "The tunnels stay at a constant temperature.", "It only grows plants in summer."], "answer": 1, "explanation_vi": "Nhiệt độ đường hầm ổn định quanh năm."},
                    {"id": "q12", "type": "mc", "prompt": "What does the writer say is the most surprising effect of urban farming in Detroit?", "options": ["the large amount of food produced", "the social connections between neighbours", "the rise in land prices"], "answer": 1, "explanation_vi": "\"the most surprising effect … is social rather than economic\"; sản lượng \"modest\", kết nối thì không."},
                ],
            },
        ],
    },
    # ────────────────────────────────────────────────────────────────────
    {
        "id": "toeic-listening-1", "exam": EXAM_TOEIC, "skill": "listening", "minutes": 10,
        "title": "TOEIC Listening · Mini Test 1",
        "description": "Part 2 (hỏi – đáp), Part 3 (hội thoại) và Part 4 (bài nói ngắn) theo bối cảnh công sở như đề thật.",
        "sections": [
            {
                "id": "p2", "title": "Part 2 · Question–Response",
                "instructions": "You will hear a question followed by three responses. Choose the best response.",
                "per_question_audio": True,
                "questions": [
                    {"id": "q1", "type": "mc", "prompt": "Listen and choose the best response.", "audio": _lines(("Man", "When is the budget report due?"), ("Woman", "A. On the third floor."), ("Woman", "B. By Friday afternoon."), ("Woman", "C. Yes, I read it.")), "options": ["On the third floor.", "By Friday afternoon.", "Yes, I read it."], "answer": 1, "explanation_vi": "Câu hỏi \"When\" → trả lời về thời gian."},
                    {"id": "q2", "type": "mc", "prompt": "Listen and choose the best response.", "audio": _lines(("Woman", "Who's leading the training session this afternoon?"), ("Man", "A. Ms. Park from Human Resources."), ("Man", "B. In the large conference room."), ("Man", "C. It lasted two hours.")), "options": ["Ms. Park from Human Resources.", "In the large conference room.", "It lasted two hours."], "answer": 0, "explanation_vi": "\"Who\" → trả lời là một người."},
                    {"id": "q3", "type": "mc", "prompt": "Listen and choose the best response.", "audio": _lines(("Man", "Would you like me to send the invoice today or tomorrow?"), ("Woman", "A. Today would be better, thanks."), ("Woman", "B. The printer is out of paper."), ("Woman", "C. No, I haven't seen it.")), "options": ["Today would be better, thanks.", "The printer is out of paper.", "No, I haven't seen it."], "answer": 0, "explanation_vi": "Câu hỏi lựa chọn \"today or tomorrow\" → chọn một trong hai."},
                    {"id": "q4", "type": "mc", "prompt": "Listen and choose the best response.", "audio": _lines(("Woman", "Why was the shipment delayed?"), ("Man", "A. About forty boxes."), ("Man", "B. There was a problem at customs."), ("Man", "C. To the Hanoi warehouse.")), "options": ["About forty boxes.", "There was a problem at customs.", "To the Hanoi warehouse."], "answer": 1, "explanation_vi": "\"Why\" → nêu lý do."},
                ],
            },
            {
                "id": "p3", "title": "Part 3 · Conversation",
                "instructions": "You will hear a conversation between two people. Answer three questions about it.",
                "audio": _lines(
                    ("Woman", "Hi David, I'm calling about the office furniture order. The desks arrived this morning, but the chairs didn't come with them."),
                    ("Man", "Oh, sorry about that. The chairs are on a separate delivery because they come from a different warehouse. They should be with you by Thursday."),
                    ("Woman", "Thursday? We have new staff starting on Wednesday. Is there any way to get them sooner?"),
                    ("Man", "Let me check. We do have an express option. It costs an extra fifty dollars, but the chairs would arrive tomorrow afternoon."),
                    ("Woman", "That's fine, please go ahead with the express delivery. Could you also email me the updated invoice?"),
                    ("Man", "Certainly. I'll send it within the hour."),
                ),
                "questions": [
                    {"id": "q5", "type": "mc", "prompt": "What is the problem?", "options": ["The desks are damaged.", "Part of the order has not arrived.", "The invoice is incorrect."], "answer": 1, "explanation_vi": "\"the chairs didn't come with them\" — ghế chưa tới."},
                    {"id": "q6", "type": "mc", "prompt": "Why does the woman need the chairs quickly?", "options": ["New employees start on Wednesday.", "A client is visiting.", "The old chairs were thrown away."], "answer": 0, "explanation_vi": "\"We have new staff starting on Wednesday.\""},
                    {"id": "q7", "type": "mc", "prompt": "What does the woman ask the man to do?", "options": ["cancel the order", "send a new invoice", "call the warehouse"], "answer": 1, "explanation_vi": "\"Could you also email me the updated invoice?\""},
                ],
            },
            {
                "id": "p4", "title": "Part 4 · Short talk",
                "instructions": "You will hear a short talk. Answer three questions about it.",
                "audio": _lines(
                    ("Man", "Good morning, everyone, and thank you for coming to this short briefing. As you know, our company is moving to the new Riverside office on the first of next month. Starting today, please pack your personal items into the boxes provided, and label each box with your name and department. Computers will be moved by the IT team on the Friday before the move, so please make sure all your files are saved to the shared drive by Thursday evening. The new building has no assigned parking, so we strongly encourage you to use the shuttle bus from Central Station, which runs every fifteen minutes. If you have any questions, contact Maria in Facilities."),
                ),
                "questions": [
                    {"id": "q8", "type": "mc", "prompt": "What is the talk mainly about?", "options": ["a new product launch", "an office relocation", "a change in working hours"], "answer": 1, "explanation_vi": "\"our company is moving to the new Riverside office\"."},
                    {"id": "q9", "type": "mc", "prompt": "What should employees do by Thursday evening?", "options": ["label their boxes", "save files to the shared drive", "return their parking passes"], "answer": 1, "explanation_vi": "\"make sure all your files are saved to the shared drive by Thursday evening\"."},
                    {"id": "q10", "type": "mc", "prompt": "How often does the shuttle bus run?", "options": ["every 5 minutes", "every 15 minutes", "every 50 minutes"], "answer": 1, "explanation_vi": "\"which runs every fifteen minutes\"."},
                ],
            },
        ],
    },
    # ────────────────────────────────────────────────────────────────────
    {
        "id": "toeic-reading-1", "exam": EXAM_TOEIC, "skill": "reading", "minutes": 15,
        "title": "TOEIC Reading · Mini Test 1",
        "description": "Part 5 (hoàn thành câu), Part 6 (hoàn thành đoạn văn) và Part 7 (đọc hiểu thông báo + email).",
        "sections": [
            {
                "id": "p5", "title": "Part 5 · Incomplete Sentences",
                "instructions": "Choose the word or phrase that best completes the sentence.",
                "questions": [
                    {"id": "q1", "type": "mc", "prompt": "The marketing team ______ the new campaign at next Monday's meeting.", "options": ["present", "will present", "presenting", "presented"], "answer": 1, "explanation_vi": "\"next Monday\" → thì tương lai: will present."},
                    {"id": "q2", "type": "mc", "prompt": "All employees must submit their expense reports ______ the end of the month.", "options": ["by", "until", "since", "during"], "answer": 0, "explanation_vi": "\"by + mốc thời gian\" = trước/hạn chót; \"until\" đi với hành động kéo dài."},
                    {"id": "q3", "type": "mc", "prompt": "Ms. Tran is responsible ______ coordinating the annual conference.", "options": ["of", "to", "for", "with"], "answer": 2, "explanation_vi": "Cụm cố định: responsible for + V-ing."},
                    {"id": "q4", "type": "mc", "prompt": "The hotel offers a ______ shuttle service to the airport every hour.", "options": ["complimentary", "compliment", "complimented", "compliments"], "answer": 0, "explanation_vi": "Cần tính từ đứng trước danh từ \"shuttle service\": complimentary (miễn phí)."},
                    {"id": "q5", "type": "mc", "prompt": "Sales figures for the third quarter were ______ higher than expected.", "options": ["significant", "significance", "significantly", "signify"], "answer": 2, "explanation_vi": "Trạng từ bổ nghĩa cho tính từ so sánh \"higher\"."},
                    {"id": "q6", "type": "mc", "prompt": "______ the heavy rain, the outdoor event went ahead as planned.", "options": ["Because", "Although", "Despite", "However"], "answer": 2, "explanation_vi": "Despite + danh từ; Although + mệnh đề."},
                ],
            },
            {
                "id": "p6", "title": "Part 6 · Text Completion",
                "instructions": "Read the e-mail and choose the best answer for each blank.",
                "passage": (
                    "To: All staff\nFrom: Daniel Reyes, Office Manager\nSubject: Printer maintenance\n\n"
                    "Dear colleagues,\n\n"
                    "The printers on the second and third floors will be ___(7)___ for maintenance on Wednesday, 14 May, from 9 a.m. to 12 p.m. "
                    "During this time, please use the printer in the mailroom on the ground floor. ___(8)___, we recommend printing any large documents before Wednesday morning. "
                    "The technician will also install new software that allows you to print directly from your phone. A short guide ___(9)___ to everyone by e-mail after the installation.\n\n"
                    "Thank you for your patience.\n\nDaniel"
                ),
                "questions": [
                    {"id": "q7", "type": "mc", "prompt": "(7)", "options": ["unavailable", "unable", "unlikely", "unaware"], "answer": 0, "explanation_vi": "Máy in \"không dùng được\" khi bảo trì: unavailable."},
                    {"id": "q8", "type": "mc", "prompt": "(8)", "options": ["Otherwise", "In addition", "For example", "Instead"], "answer": 1, "explanation_vi": "Thêm một lời khuyên nữa → In addition."},
                    {"id": "q9", "type": "mc", "prompt": "(9)", "options": ["sent", "was sent", "will be sent", "is sending"], "answer": 2, "explanation_vi": "Việc trong tương lai, bị động: will be sent."},
                ],
            },
            {
                "id": "p7", "title": "Part 7 · Reading Comprehension",
                "instructions": "Read the notice and the e-mail, then answer the questions.",
                "passage": (
                    "NOTICE — Lakeside Business Park\n"
                    "The main car park will be closed for resurfacing from Monday 3 June to Friday 7 June. "
                    "During this period, tenants may park free of charge at the Harbour Street multi-storey car park (a five-minute walk). "
                    "Please display the temporary permit, available from reception, on your dashboard. Vehicles without a permit will be charged the standard daily rate of $12. "
                    "We apologise for any inconvenience.\n\n"
                    "— — —\n\n"
                    "From: Priya Nair <p.nair@novatech.com>\nTo: reception@lakesidepark.com\nSubject: Temporary permits\n\n"
                    "Hello,\n\nI manage the NovaTech office on the fourth floor. We have eleven staff who drive to work, but I was only able to collect six permits this morning. "
                    "Could you let me know when more will be available? Two of our team start early, at 7 a.m., so it would help to have the permits by Friday this week. "
                    "Also, is the Harbour Street car park open 24 hours? One of our engineers sometimes works late.\n\nMany thanks,\nPriya"
                ),
                "questions": [
                    {"id": "q10", "type": "mc", "prompt": "Why is the main car park closing?", "options": ["to add more parking spaces", "to repair the surface", "to build a new reception"], "answer": 1, "explanation_vi": "\"closed for resurfacing\" = sửa lại mặt đường."},
                    {"id": "q11", "type": "mc", "prompt": "What will happen to a car parked at Harbour Street without a permit?", "options": ["It will be towed away.", "The driver will pay $12 a day.", "It will be moved to the main car park."], "answer": 1, "explanation_vi": "\"Vehicles without a permit will be charged the standard daily rate of $12.\""},
                    {"id": "q12", "type": "mc", "prompt": "How many more permits does Ms. Nair need?", "options": ["five", "six", "eleven"], "answer": 0, "explanation_vi": "11 nhân viên lái xe − 6 thẻ đã lấy = 5."},
                    {"id": "q13", "type": "mc", "prompt": "What does Ms. Nair want to know about the Harbour Street car park?", "options": ["how much it costs", "whether it is open all day and night", "how far it is from the office"], "answer": 1, "explanation_vi": "\"is the Harbour Street car park open 24 hours?\""},
                ],
            },
        ],
    },
]

_BY_ID = {e["id"]: e for e in EXAMS}


def list_exams() -> list[dict]:
    return EXAMS


def get_exam(exam_id: str) -> dict | None:
    return _BY_ID.get(exam_id)


def question_count(exam: dict) -> int:
    return sum(len(s["questions"]) for s in exam["sections"])


def public_exam(exam: dict) -> dict:
    """The test as the learner sees it: no answers, no explanations."""
    out = deepcopy(exam)
    for section in out["sections"]:
        for q in section["questions"]:
            q.pop("answer", None)
            q.pop("explanation_vi", None)
    return out


def _norm(text: str) -> str:
    text = (text or "").strip().lower()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def _check(q: dict, given) -> bool:
    if q["type"] == "gap":
        return _norm(str(given)) in {_norm(a) for a in q["answer"]} if given not in (None, "") else False
    try:
        return int(given) == int(q["answer"])
    except (TypeError, ValueError):
        return False


def estimate_score(exam: dict, pct: float) -> float:
    """IELTS band (0–9, half steps) or TOEIC section score (5–495, steps of 5)."""
    if exam["exam"] == EXAM_IELTS:
        raw40 = round(pct / 100 * 40)
        table = _IELTS_LISTENING_BANDS if exam["skill"] == "listening" else _IELTS_READING_BANDS
        for floor, band in table:
            if raw40 >= floor:
                return band
        return 2.0
    return float(5 + round(pct / 100 * 490 / 5) * 5)


def grade(exam: dict, answers: dict) -> dict:
    """Score every question. Returns correct/total/pct/estimate, per-section counts and per-question detail."""
    sections, details = [], []
    correct = total = 0
    for section in exam["sections"]:
        s_correct = 0
        for q in section["questions"]:
            given = answers.get(q["id"])
            ok = _check(q, given)
            s_correct += ok
            if q["type"] == "gap":
                expected = q["answer"][0]
                given_text = str(given) if given not in (None, "") else ""
            else:
                expected = q["options"][q["answer"]]
                given_text = q["options"][int(given)] if isinstance(given, int) and 0 <= given < len(q["options"]) else (str(given) if given not in (None, "") else "")
            details.append({"id": q["id"], "section_id": section["id"], "correct": ok, "given": given_text, "expected": expected, "explanation_vi": q.get("explanation_vi", "")})
        n = len(section["questions"])
        sections.append({"id": section["id"], "title": section["title"], "correct": s_correct, "total": n})
        correct += s_correct
        total += n
    pct = round(correct / total * 100, 1) if total else 0.0
    return {"correct": correct, "total": total, "pct": pct, "estimate": estimate_score(exam, pct), "sections": sections, "details": details}


def xp_for(correct: int) -> int:
    return min(XP_CAP, correct * XP_PER_CORRECT)
