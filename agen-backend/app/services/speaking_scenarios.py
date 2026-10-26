"""
G2 · Luyện nói 3 bước — kho tình huống có bối cảnh Việt Nam.

Mỗi tình huống có một nhân vật AI (persona), 5–6 cụm từ cần học, lời mở đầu
và mục tiêu. Bước 1 (học cụm từ) và bước 2 (nói lặp lại) không cần LLM; bước 3
(roleplay) dùng system prompt dựng từ persona nên lời mở đầu cũng có sẵn.

Dữ liệu thuần, không I/O.
"""
from __future__ import annotations

from typing import Optional

CATEGORIES: dict[str, str] = {
    "daily": "Đời sống hằng ngày",
    "travel": "Du lịch & đi lại",
    "work": "Công việc",
    "school": "Trường học",
    "social": "Giao tiếp xã hội",
    "health": "Sức khỏe",
}

LEVEL_ORDER = ["PRE_A1", "A1", "A2", "B1", "B2", "C1", "C2"]


def _s(
    id: str, category: str, level: str, emoji: str,
    title_vi: str, title_en: str,
    persona_name: str, persona_role_en: str, persona_role_vi: str, persona_style: str, voice: str,
    learner_role_en: str, learner_role_vi: str,
    goal_en: str, goal_vi: str,
    first_message: str,
    phrases: list[tuple[str, str]],
) -> dict:
    return {
        "id": id,
        "category": category,
        "level": level,
        "emoji": emoji,
        "title_vi": title_vi,
        "title_en": title_en,
        "persona": {
            "name": persona_name,
            "role_en": persona_role_en,
            "role_vi": persona_role_vi,
            "style": persona_style,
            "voice": voice,           # "female" | "male" → chọn giọng TTS
        },
        "learner_role_en": learner_role_en,
        "learner_role_vi": learner_role_vi,
        "goal_en": goal_en,
        "goal_vi": goal_vi,
        "first_message": first_message,
        "phrases": [{"en": en, "vi": vi} for en, vi in phrases],
    }


SCENARIOS: list[dict] = [
    # ── A1 ───────────────────────────────────────────────────────────────────
    _s("cafe_order", "daily", "A1", "☕", "Gọi đồ ở quán cà phê", "Ordering at a coffee shop",
       "Linh", "a barista at a small coffee shop in Hanoi", "Nhân viên pha chế", "friendly, patient, speaks slowly", "female",
       "a customer", "Khách hàng",
       "Order a drink, ask the price and pay.", "Gọi một món đồ uống, hỏi giá và thanh toán.",
       "Hi there! Welcome to Cộng Cà Phê. What would you like to drink today?",
       [("Can I have an iced milk coffee, please?", "Cho tôi một ly cà phê sữa đá nhé."),
        ("How much is it?", "Bao nhiêu tiền vậy?"),
        ("Less sugar, please.", "Ít đường thôi ạ."),
        ("Can I pay by card?", "Tôi trả bằng thẻ được không?"),
        ("For here or to go? — To go, please.", "Dùng tại đây hay mang đi? — Mang đi ạ.")]),
    _s("market_shopping", "daily", "A1", "🥬", "Mua rau ở chợ", "Buying vegetables at the market",
       "Cô Ba", "a vegetable seller at a local market", "Cô bán rau ở chợ", "warm, talkative, likes to bargain", "female",
       "a shopper", "Người đi chợ",
       "Buy some vegetables, ask the price and bargain a little.", "Mua vài loại rau, hỏi giá và mặc cả một chút.",
       "Good morning! Fresh vegetables today. What do you need?",
       [("How much are the tomatoes?", "Cà chua bao nhiêu một cân?"),
        ("I'd like one kilo, please.", "Cho tôi một cân nhé."),
        ("That's a bit expensive. Can you make it cheaper?", "Hơi đắt. Bớt cho tôi chút được không?"),
        ("Do you have any fresh mangoes?", "Cô có xoài tươi không?"),
        ("Thank you, see you tomorrow!", "Cảm ơn cô, mai gặp lại!")]),
    _s("self_intro", "social", "A1", "👋", "Giới thiệu bản thân", "Introducing yourself",
       "Emma", "a new neighbour from Australia", "Hàng xóm mới người Úc", "cheerful, curious, asks simple questions", "female",
       "yourself", "Chính bạn",
       "Introduce yourself: name, age, job or school, hobbies.", "Giới thiệu bản thân: tên, tuổi, công việc/trường học, sở thích.",
       "Hello! I just moved in next door. I'm Emma. What's your name?",
       [("Nice to meet you. My name is Minh.", "Rất vui được gặp bạn. Tôi tên là Minh."),
        ("I'm twenty years old.", "Tôi hai mươi tuổi."),
        ("I'm a student at Hanoi University.", "Tôi là sinh viên Đại học Hà Nội."),
        ("In my free time, I like playing football.", "Lúc rảnh tôi thích đá bóng."),
        ("Where are you from?", "Bạn đến từ đâu?")]),
    _s("directions", "travel", "A1", "🗺️", "Hỏi đường", "Asking for directions",
       "Tom", "a tourist looking for Hoan Kiem Lake", "Khách du lịch đang tìm Hồ Gươm", "polite, a little lost, grateful", "male",
       "a local person helping a tourist", "Người địa phương chỉ đường",
       "Help the tourist find the lake and a good place to eat.", "Chỉ đường cho khách tới hồ và gợi ý chỗ ăn ngon.",
       "Excuse me, could you help me? I'm looking for Hoan Kiem Lake.",
       [("Go straight ahead, then turn left.", "Đi thẳng, rồi rẽ trái."),
        ("It's about five minutes on foot.", "Đi bộ khoảng năm phút."),
        ("The lake is next to the post office.", "Hồ ở ngay cạnh bưu điện."),
        ("You can take a taxi or a Grab bike.", "Bạn có thể đi taxi hoặc xe ôm Grab."),
        ("You're welcome. Enjoy your trip!", "Không có gì. Chúc bạn chuyến đi vui vẻ!")]),
    _s("restaurant_order", "daily", "A1", "🍜", "Gọi món ở quán phở", "Ordering at a pho restaurant",
       "Anh Tuấn", "a waiter at a busy pho restaurant", "Nhân viên phục vụ quán phở", "quick, polite, helpful", "male",
       "a customer", "Khách hàng",
       "Order a bowl of pho and a drink, then ask for the bill.", "Gọi một bát phở và đồ uống, rồi xin tính tiền.",
       "Good evening! Table for how many people?",
       [("A table for two, please.", "Cho tôi bàn hai người."),
        ("I'd like a bowl of beef pho, please.", "Cho tôi một bát phở bò."),
        ("Can I have some more lime?", "Cho tôi thêm chanh được không?"),
        ("It's delicious!", "Ngon quá!"),
        ("Can I have the bill, please?", "Cho tôi tính tiền nhé.")]),
    _s("phone_number", "daily", "A1", "📱", "Hỏi và cho số điện thoại", "Exchanging phone numbers",
       "Sarah", "a classmate from your English club", "Bạn cùng câu lạc bộ tiếng Anh", "friendly, speaks clearly", "female",
       "a club member", "Thành viên câu lạc bộ",
       "Ask for a phone number, say yours, and spell your name.", "Hỏi số điện thoại, đọc số của bạn và đánh vần tên.",
       "That was a fun class! Let's keep in touch. Do you have Zalo?",
       [("What's your phone number?", "Số điện thoại của bạn là gì?"),
        ("My number is 0912 345 678.", "Số của tôi là 0912 345 678."),
        ("Can you say that again, please?", "Bạn nói lại được không?"),
        ("How do you spell your name?", "Tên bạn đánh vần thế nào?"),
        ("I'll text you tonight.", "Tối nay tôi nhắn cho bạn nhé.")]),
    _s("family_talk", "social", "A1", "👨‍👩‍👧", "Nói về gia đình", "Talking about your family",
       "Mr. Lee", "a friendly English teacher from Singapore", "Thầy giáo tiếng Anh người Singapore", "kind, encouraging, asks follow-up questions", "male",
       "a student", "Học sinh",
       "Describe your family: members, jobs and what you do together.", "Kể về gia đình: thành viên, nghề nghiệp, hoạt động chung.",
       "Hi! Today let's talk about family. How many people are there in your family?",
       [("There are four people in my family.", "Gia đình tôi có bốn người."),
        ("My father is a doctor and my mother is a teacher.", "Bố tôi là bác sĩ, mẹ tôi là giáo viên."),
        ("I have a younger sister.", "Tôi có một em gái."),
        ("We often eat dinner together.", "Chúng tôi thường ăn tối cùng nhau."),
        ("My grandmother lives with us.", "Bà tôi sống cùng chúng tôi.")]),
    _s("bus_ticket", "travel", "A1", "🚌", "Mua vé xe buýt", "Buying a bus ticket",
       "Chú Hải", "a ticket seller at Mỹ Đình bus station", "Nhân viên bán vé bến xe Mỹ Đình", "direct, efficient, helpful", "male",
       "a passenger", "Hành khách",
       "Buy a ticket to Ha Long, ask the time and the platform.", "Mua vé đi Hạ Long, hỏi giờ chạy và cửa lên xe.",
       "Hello, where are you going today?",
       [("One ticket to Ha Long, please.", "Cho tôi một vé đi Hạ Long."),
        ("What time does the bus leave?", "Mấy giờ xe chạy?"),
        ("How long does it take?", "Đi mất bao lâu?"),
        ("Which gate is it?", "Xe ở cửa số mấy?"),
        ("Is there a bus in the afternoon?", "Buổi chiều có chuyến không?")]),

    # ── A2 ───────────────────────────────────────────────────────────────────
    _s("hotel_checkin", "travel", "A2", "🏨", "Nhận phòng khách sạn ở Đà Nẵng", "Checking in at a hotel in Da Nang",
       "Ms. Hạnh", "a hotel receptionist in Da Nang", "Lễ tân khách sạn", "professional, polite, clear", "female",
       "a guest", "Khách lưu trú",
       "Check in, ask about breakfast, Wi-Fi and the beach.", "Nhận phòng, hỏi về bữa sáng, Wi-Fi và đường ra biển.",
       "Good afternoon and welcome to Sea Breeze Hotel. Do you have a reservation?",
       [("I have a reservation under the name Nguyen.", "Tôi đã đặt phòng tên Nguyễn."),
        ("What time is breakfast served?", "Bữa sáng phục vụ lúc mấy giờ?"),
        ("Could I have the Wi-Fi password, please?", "Cho tôi xin mật khẩu Wi-Fi được không?"),
        ("Is the beach far from here?", "Bãi biển có xa đây không?"),
        ("I'd like a room with a sea view.", "Tôi muốn phòng nhìn ra biển."),
        ("What time is check-out?", "Mấy giờ trả phòng?")]),
    _s("grab_ride", "travel", "A2", "🛵", "Đi Grab", "Taking a Grab ride",
       "Anh Dũng", "a Grab driver in Ho Chi Minh City", "Tài xế Grab", "chatty, friendly, knows the city well", "male",
       "a passenger", "Hành khách",
       "Confirm the destination, chat about traffic and ask to stop somewhere.", "Xác nhận điểm đến, nói chuyện về kẹt xe và nhờ dừng dọc đường.",
       "Hi! Are you going to Ben Thanh Market? Please put on the helmet.",
       [("Yes, that's right. How long will it take?", "Đúng rồi. Đi mất bao lâu ạ?"),
        ("The traffic is really heavy today.", "Hôm nay kẹt xe quá."),
        ("Could you drive a little slower, please?", "Anh chạy chậm một chút được không?"),
        ("Can we stop at a convenience store on the way?", "Mình ghé cửa hàng tiện lợi trên đường được không?"),
        ("You can drop me off here. Thank you!", "Anh cho tôi xuống đây nhé. Cảm ơn anh!")]),
    _s("doctor_visit", "health", "A2", "🩺", "Đi khám bệnh", "Visiting the doctor",
       "Dr. Mai", "a doctor at a family clinic", "Bác sĩ phòng khám gia đình", "calm, caring, asks clear questions", "female",
       "a patient", "Bệnh nhân",
       "Describe your symptoms and ask what to do.", "Mô tả triệu chứng và hỏi cách điều trị.",
       "Hello, please have a seat. What seems to be the problem today?",
       [("I have a headache and a sore throat.", "Tôi bị đau đầu và đau họng."),
        ("I've had a fever since yesterday.", "Tôi bị sốt từ hôm qua."),
        ("Do I need to take any medicine?", "Tôi có cần uống thuốc không?"),
        ("How many times a day should I take it?", "Ngày uống mấy lần ạ?"),
        ("Can I go to work tomorrow?", "Mai tôi đi làm được không?")]),
    _s("pharmacy", "health", "A2", "💊", "Mua thuốc ở hiệu thuốc", "At the pharmacy",
       "Chị Thu", "a pharmacist", "Dược sĩ", "careful, helpful, explains clearly", "female",
       "a customer", "Khách mua thuốc",
       "Ask for medicine for a cold and understand how to take it.", "Hỏi mua thuốc cảm và hiểu cách dùng.",
       "Good morning. How can I help you?",
       [("I need something for a cold.", "Tôi cần thuốc trị cảm."),
        ("Do you have anything for a cough?", "Chị có thuốc ho không?"),
        ("How should I take this?", "Thuốc này uống thế nào?"),
        ("Are there any side effects?", "Có tác dụng phụ gì không?"),
        ("I'm allergic to penicillin.", "Tôi bị dị ứng với penicillin.")]),
    _s("job_small_talk", "work", "A2", "🏢", "Ngày đầu đi làm", "First day at work",
       "David", "your new team leader at a tech company", "Trưởng nhóm mới ở công ty công nghệ", "welcoming, relaxed, professional", "male",
       "a new employee", "Nhân viên mới",
       "Introduce yourself to the team and ask about your work.", "Giới thiệu bản thân với nhóm và hỏi về công việc.",
       "Welcome to the team! I'm David. How was your trip to the office this morning?",
       [("Nice to meet you. I'm excited to start.", "Rất vui được gặp anh. Tôi rất háo hức bắt đầu."),
        ("I worked as a designer for two years.", "Tôi từng làm thiết kế hai năm."),
        ("What will I be working on?", "Tôi sẽ làm việc gì ạ?"),
        ("Who should I ask if I have questions?", "Có thắc mắc tôi nên hỏi ai?"),
        ("What time does the team usually have lunch?", "Nhóm thường ăn trưa lúc mấy giờ?")]),
    _s("school_teacher", "school", "A2", "🎒", "Nói chuyện với giáo viên", "Talking to your teacher",
       "Ms. Brown", "your English teacher", "Cô giáo tiếng Anh", "patient, supportive, speaks clearly", "female",
       "a student", "Học sinh",
       "Ask about homework and explain why you were absent.", "Hỏi về bài tập và giải thích lý do nghỉ học.",
       "Good morning! I didn't see you in class yesterday. Is everything okay?",
       [("I'm sorry, I was sick yesterday.", "Em xin lỗi, hôm qua em bị ốm."),
        ("What did we study yesterday?", "Hôm qua lớp học gì ạ?"),
        ("Could you explain this exercise again?", "Cô giảng lại bài này được không ạ?"),
        ("When is the homework due?", "Khi nào phải nộp bài tập ạ?"),
        ("Can I hand it in tomorrow?", "Mai em nộp được không ạ?")]),
    _s("weekend_plans", "social", "A2", "🎉", "Hẹn bạn cuối tuần", "Making weekend plans",
       "Jake", "a friend from your gym", "Bạn tập cùng phòng gym", "energetic, easy-going, loves food", "male",
       "a friend", "Bạn bè",
       "Suggest an activity, agree on a time and place.", "Đề xuất hoạt động, thống nhất giờ và địa điểm.",
       "Hey! Any plans for the weekend? I'm free on Saturday.",
       [("Do you want to go to the cinema on Saturday?", "Thứ Bảy đi xem phim không?"),
        ("What time should we meet?", "Mình gặp nhau mấy giờ?"),
        ("Let's meet at seven in front of the mall.", "Gặp nhau lúc bảy giờ trước trung tâm thương mại nhé."),
        ("How about a bowl of bún chả after that?", "Sau đó ăn bún chả nhé?"),
        ("Sounds great! See you then.", "Tuyệt! Hẹn gặp lại.")]),
    _s("clothes_shop", "daily", "A2", "👕", "Mua quần áo", "Shopping for clothes",
       "Ngọc", "a shop assistant at a clothing store", "Nhân viên cửa hàng quần áo", "stylish, attentive, polite", "female",
       "a customer", "Khách hàng",
       "Ask for a size, try something on and ask about a discount.", "Hỏi cỡ, thử đồ và hỏi giảm giá.",
       "Hello! Welcome. Are you looking for anything in particular?",
       [("I'm looking for a white shirt.", "Tôi đang tìm một chiếc áo sơ mi trắng."),
        ("Do you have this in a medium?", "Cái này có cỡ M không?"),
        ("Can I try it on?", "Tôi thử được không?"),
        ("It's a little too big. Do you have a smaller one?", "Hơi rộng. Có cỡ nhỏ hơn không?"),
        ("Is there a discount today?", "Hôm nay có giảm giá không?")]),

    # ── B1 ───────────────────────────────────────────────────────────────────
    _s("job_interview", "work", "B1", "💼", "Phỏng vấn xin việc", "Job interview",
       "Ms. Carter", "an HR manager at an international company", "Trưởng phòng nhân sự công ty quốc tế", "professional, friendly but direct", "female",
       "a job candidate", "Ứng viên",
       "Talk about your experience, strengths and why you want the job.", "Nói về kinh nghiệm, điểm mạnh và lý do ứng tuyển.",
       "Thanks for coming in today. To start, could you tell me a little about yourself?",
       [("I graduated from Foreign Trade University in 2024.", "Tôi tốt nghiệp Đại học Ngoại thương năm 2024."),
        ("I have two years of experience in marketing.", "Tôi có hai năm kinh nghiệm marketing."),
        ("My biggest strength is that I learn quickly.", "Điểm mạnh nhất của tôi là học hỏi nhanh."),
        ("I'm interested in this role because I enjoy working with people.", "Tôi quan tâm vị trí này vì thích làm việc với mọi người."),
        ("Could you tell me more about the team?", "Chị có thể nói thêm về nhóm được không?"),
        ("When can I expect to hear back from you?", "Khi nào tôi có thể nhận phản hồi?")]),
    _s("complaint_delivery", "daily", "B1", "📦", "Khiếu nại đơn hàng giao sai", "Complaining about a wrong delivery",
       "Kevin", "a customer-service agent for an online shop", "Nhân viên chăm sóc khách hàng shop online", "apologetic, solution-focused", "male",
       "a customer", "Khách hàng",
       "Explain the problem politely and ask for a refund or exchange.", "Trình bày vấn đề lịch sự, yêu cầu hoàn tiền hoặc đổi hàng.",
       "Hello, thank you for contacting us. How can I help you today?",
       [("I received the wrong item yesterday.", "Hôm qua tôi nhận nhầm hàng."),
        ("I ordered a blue one, but I got a black one.", "Tôi đặt màu xanh nhưng nhận màu đen."),
        ("I'd like to exchange it, please.", "Tôi muốn đổi hàng."),
        ("How long will the refund take?", "Hoàn tiền mất bao lâu?"),
        ("Could you send me a confirmation email?", "Bạn gửi email xác nhận cho tôi được không?")]),
    _s("airport_checkin", "travel", "B1", "✈️", "Làm thủ tục ở sân bay", "Checking in at the airport",
       "Mr. Nam", "an airline check-in agent at Tan Son Nhat airport", "Nhân viên làm thủ tục sân bay Tân Sơn Nhất", "efficient, polite, precise", "male",
       "a passenger", "Hành khách",
       "Check in, choose a seat and ask about baggage.", "Làm thủ tục, chọn chỗ ngồi và hỏi về hành lý.",
       "Good morning. May I see your passport and booking, please?",
       [("Here's my passport. I'm flying to Bangkok.", "Đây là hộ chiếu. Tôi bay đi Bangkok."),
        ("Could I have a window seat, please?", "Cho tôi ghế cạnh cửa sổ được không?"),
        ("How many bags can I check in?", "Tôi được ký gửi mấy kiện hành lý?"),
        ("Is my bag over the weight limit?", "Hành lý của tôi có quá cân không?"),
        ("Which gate does the flight leave from?", "Chuyến bay ở cổng số mấy?")]),
    _s("apartment_rent", "daily", "B1", "🏠", "Thuê căn hộ", "Renting an apartment",
       "Ms. Phương", "a landlord showing an apartment", "Chủ nhà cho thuê căn hộ", "businesslike, friendly, firm on price", "female",
       "a tenant", "Người thuê nhà",
       "Ask about rent, bills, the deposit and the contract.", "Hỏi giá thuê, tiền điện nước, tiền cọc và hợp đồng.",
       "Welcome! This is the apartment. It's on the fifth floor with a balcony. What do you think?",
       [("How much is the rent per month?", "Tiền thuê một tháng bao nhiêu?"),
        ("Does that include electricity and water?", "Giá đó đã gồm điện nước chưa?"),
        ("How much is the deposit?", "Tiền cọc bao nhiêu?"),
        ("Is the contract for one year?", "Hợp đồng một năm phải không?"),
        ("Can I move in next week?", "Tuần sau tôi chuyển vào được không?")]),
    _s("presentation_qna", "school", "B1", "🎤", "Trả lời câu hỏi sau thuyết trình", "Answering questions after a presentation",
       "Professor Green", "a lecturer at your university", "Giảng viên đại học", "thoughtful, challenging but fair", "male",
       "a student presenter", "Sinh viên thuyết trình",
       "Answer questions about your project clearly and confidently.", "Trả lời câu hỏi về dự án một cách rõ ràng, tự tin.",
       "Thank you for your presentation on plastic waste in Vietnam. I have a few questions. First, why did you choose this topic?",
       [("I chose this topic because it affects my hometown.", "Em chọn đề tài này vì nó ảnh hưởng đến quê em."),
        ("That's a good question. Let me explain.", "Câu hỏi hay ạ. Để em giải thích."),
        ("According to our survey, most people agree.", "Theo khảo sát của chúng em, đa số đồng ý."),
        ("I'm not sure, but I think the main reason is cost.", "Em không chắc, nhưng em nghĩ lý do chính là chi phí."),
        ("Thank you for your feedback.", "Cảm ơn thầy đã góp ý.")]),
    _s("making_friends_travel", "social", "B1", "🌏", "Làm quen với du khách", "Making friends with a traveller",
       "Sofia", "a backpacker from Spain travelling in Vietnam", "Du khách ba lô người Tây Ban Nha", "open, adventurous, loves local food", "female",
       "a local friend", "Người bạn địa phương",
       "Recommend places to visit and food to try; ask about her trip.", "Gợi ý địa điểm, món ăn và hỏi về chuyến đi của cô ấy.",
       "Hi! I just arrived in Hanoi yesterday. Do you have any tips for a first-time visitor?",
       [("You should definitely visit the Old Quarter.", "Bạn nhất định nên đi phố cổ."),
        ("Have you tried egg coffee yet?", "Bạn đã thử cà phê trứng chưa?"),
        ("How long are you staying in Vietnam?", "Bạn ở Việt Nam bao lâu?"),
        ("If you like nature, Ninh Binh is only two hours away.", "Nếu thích thiên nhiên, Ninh Bình chỉ cách hai tiếng."),
        ("Let me know if you need any help.", "Cần gì cứ nhắn mình nhé.")]),

    # ── B2 ───────────────────────────────────────────────────────────────────
    _s("work_meeting", "work", "B2", "📊", "Họp nhóm: đề xuất ý tưởng", "Team meeting: proposing an idea",
       "Rachel", "a product manager leading a weekly meeting", "Quản lý sản phẩm chủ trì họp tuần", "sharp, collaborative, asks for data", "female",
       "a team member", "Thành viên nhóm",
       "Propose an idea, respond to concerns and agree on next steps.", "Đề xuất ý tưởng, phản hồi lo ngại và chốt bước tiếp theo.",
       "Okay everyone, let's move on. I heard you had a proposal for the onboarding flow?",
       [("I'd like to suggest simplifying the sign-up process.", "Tôi muốn đề xuất đơn giản hóa quy trình đăng ký."),
        ("The data shows that 40% of users drop off at step two.", "Dữ liệu cho thấy 40% người dùng bỏ dở ở bước hai."),
        ("I understand your concern, but I think the benefits outweigh the risks.", "Tôi hiểu lo ngại của chị, nhưng lợi ích lớn hơn rủi ro."),
        ("Could we run a small test for two weeks first?", "Mình chạy thử nhỏ trong hai tuần trước được không?"),
        ("I'll prepare a detailed plan by Friday.", "Tôi sẽ chuẩn bị kế hoạch chi tiết trước thứ Sáu.")]),
    _s("debate_social_media", "school", "B2", "💬", "Tranh luận: mạng xã hội", "Debate: social media and teenagers",
       "Alex", "a debate club partner who takes the opposite side", "Bạn câu lạc bộ tranh luận (phe đối lập)", "confident, logical, challenges you politely", "male",
       "a debater", "Người tranh luận",
       "Give your opinion with reasons and respond to counter-arguments.", "Nêu quan điểm có lý do và phản biện lập luận đối phương.",
       "I'll start: I believe social media does more harm than good for teenagers. What's your view?",
       [("I partly agree, but I think it depends on how it's used.", "Tôi đồng ý một phần, nhưng còn tùy cách sử dụng."),
        ("On the one hand, it connects people; on the other hand, it can be addictive.", "Một mặt nó kết nối mọi người; mặt khác nó dễ gây nghiện."),
        ("That's a fair point, however, the research is mixed.", "Ý hay, tuy nhiên nghiên cứu còn chưa thống nhất."),
        ("In my experience, it helps students learn from each other.", "Theo kinh nghiệm của tôi, nó giúp học sinh học hỏi lẫn nhau."),
        ("To sum up, the key is balance and education.", "Tóm lại, mấu chốt là sự cân bằng và giáo dục.")]),
]

_BY_ID = {s["id"]: s for s in SCENARIOS}


def list_scenarios(level: Optional[str] = None) -> list[dict]:
    """All scenarios; `level` only adds a `recommended` flag (nothing is hidden)."""
    out = []
    for s in SCENARIOS:
        item = {k: v for k, v in s.items() if k != "phrases"}
        item["phrase_count"] = len(s["phrases"])
        item["recommended"] = _recommended(s["level"], level)
        out.append(item)
    return out


def _recommended(scenario_level: str, learner_level: Optional[str]) -> bool:
    if not learner_level or learner_level not in LEVEL_ORDER or scenario_level not in LEVEL_ORDER:
        return False
    li = LEVEL_ORDER.index(learner_level)
    si = LEVEL_ORDER.index(scenario_level)
    return si in (li, li + 1) or (li == 0 and si <= 1)


def get_scenario(scenario_id: str) -> Optional[dict]:
    return _BY_ID.get(scenario_id)


def build_system_prompt(scenario: dict, learner_level: str) -> str:
    """System prompt for the roleplay step; the persona stays in character."""
    p = scenario["persona"]
    return (
        f"You are {p['name']}, {p['role_en']}. Personality: {p['style']}. "
        f"Scenario: {scenario['title_en']}. The learner plays {scenario['learner_role_en']}. "
        f"Setting: Vietnam. The learner's goal: {scenario['goal_en']} "
        f"The learner is a Vietnamese CEFR {learner_level} student, so use natural English at that level "
        f"(short sentences for A1–A2). Stay in character, keep each reply to 1–2 sentences and end with a "
        f"question or a prompt so the learner keeps talking. Gently steer the conversation toward the goal "
        f"and wrap up naturally after about 6 turns."
    )
