"""
Static placement-test question bank — the fallback when the LLM is busy or out of quota.

Each item is (question, correct, wrong1, wrong2, wrong3, explanation_vi); reading items start with a
passage and listening items with the spoken text. The option order is shuffled deterministically so
the correct answer is not always "A".
"""
import zlib

LEVELS = ["PRE_A1", "A1", "A2", "B1", "B2", "C1"]

# vocabulary / grammar: (question, correct, w1, w2, w3, explanation)
VOCABULARY: dict[str, list[tuple]] = {
    "PRE_A1": [
        ("Which word is an animal that says 'meow'?", "cat", "dog", "bird", "fish", "Con mèo kêu 'meow'."),
        ("Which one is a fruit?", "apple", "chair", "table", "pen", "Apple là quả táo."),
        ("What colour is a banana?", "yellow", "blue", "black", "purple", "Chuối màu vàng (yellow)."),
    ],
    "A1": [
        ("What do you use to write on paper?", "a pen", "a spoon", "a shoe", "a clock", "Dùng bút (a pen) để viết."),
        ("Which word is the opposite of 'big'?", "small", "tall", "long", "fast", "Trái nghĩa của big là small."),
        ("'Breakfast' is the meal you eat in the ____.", "morning", "evening", "night", "afternoon", "Breakfast là bữa sáng."),
    ],
    "A2": [
        ("If you are 'exhausted', you feel very ____.", "tired", "hungry", "angry", "happy", "Exhausted = rất mệt."),
        ("A person who cooks in a restaurant is a ____.", "chef", "driver", "doctor", "teacher", "Chef là đầu bếp."),
        ("'Delicious' means the food tastes very ____.", "good", "bad", "cold", "old", "Delicious = rất ngon."),
    ],
    "B1": [
        ("Which word is closest in meaning to 'purchase'?", "buy", "sell", "borrow", "lend", "Purchase = mua."),
        ("She made a ____ to study every day, so she wrote a plan.", "decision", "direction", "decoration", "destination", "Make a decision = đưa ra quyết định."),
        ("An 'efficient' worker is someone who ____.", "works well without wasting time", "wastes time", "is always late", "never speaks", "Efficient = làm việc hiệu quả."),
    ],
    "B2": [
        ("Which word is closest in meaning to 'reluctant'?", "unwilling", "eager", "careless", "generous", "Reluctant = miễn cưỡng, không sẵn lòng."),
        ("The new law will ____ big changes in the way companies work.", "bring about", "bring along", "bring back", "bring out", "Bring about = gây ra, dẫn đến."),
        ("'Substantial' evidence is evidence that is ____.", "considerable", "weak", "secret", "outdated", "Substantial = đáng kể."),
    ],
    "C1": [
        ("Which word is closest in meaning to 'ubiquitous'?", "present everywhere", "rare", "ancient", "fragile", "Ubiquitous = có mặt khắp nơi."),
        ("His argument was so ____ that nobody could find a flaw in it.", "cogent", "dormant", "frugal", "trivial", "Cogent = thuyết phục, chặt chẽ."),
        ("To 'mitigate' a risk means to ____.", "make it less serious", "ignore it", "increase it", "predict it", "Mitigate = giảm nhẹ."),
    ],
}

GRAMMAR: dict[str, list[tuple]] = {
    "PRE_A1": [
        ("I ____ a student.", "am", "is", "are", "be", "Với I dùng am."),
        ("She ____ my sister.", "is", "am", "are", "be", "Với she dùng is."),
        ("This is ____ book.", "a", "an", "two", "many", "Book bắt đầu bằng phụ âm nên dùng a."),
    ],
    "A1": [
        ("He ____ to school every day.", "goes", "go", "going", "gone", "Ngôi thứ ba số ít thêm -es: goes."),
        ("There ____ two cats in the garden.", "are", "is", "am", "be", "Hai con mèo → are."),
        ("I ____ breakfast at 7 o'clock.", "have", "has", "having", "haves", "Với I dùng have."),
    ],
    "A2": [
        ("Yesterday we ____ to the cinema.", "went", "go", "gone", "going", "Quá khứ của go là went."),
        ("She is ____ than her brother.", "taller", "tall", "tallest", "more tall", "So sánh hơn của tall là taller."),
        ("I ____ TV when the phone rang.", "was watching", "watch", "watched", "am watching", "Hành động đang diễn ra thì bị cắt ngang → quá khứ tiếp diễn."),
    ],
    "B1": [
        ("If it rains tomorrow, we ____ at home.", "will stay", "stay", "would stay", "stayed", "Câu điều kiện loại 1: If + hiện tại, will + V."),
        ("I have lived here ____ 2019.", "since", "for", "from", "during", "Since + mốc thời gian."),
        ("The book ____ by millions of people.", "has been read", "has read", "have read", "is reading", "Bị động hiện tại hoàn thành: has been + V3."),
    ],
    "B2": [
        ("If I ____ more time, I would travel more.", "had", "have", "will have", "would have", "Điều kiện loại 2: If + quá khứ đơn."),
        ("He suggested ____ the meeting until Monday.", "postponing", "to postpone", "postpone", "postponed", "Suggest + V-ing."),
        ("By the time we arrived, the film ____.", "had already started", "already started", "has already started", "was already starting", "Hành động xảy ra trước một mốc quá khứ → quá khứ hoàn thành."),
    ],
    "C1": [
        ("Not only ____ late, but he also forgot the documents.", "was he", "he was", "did he", "he is", "Đảo ngữ sau 'Not only': was he."),
        ("Had I known about the delay, I ____ earlier.", "would have left", "would leave", "will leave", "had left", "Điều kiện loại 3 đảo ngữ: Had I known… would have + V3."),
        ("The proposal, ____ details were still unclear, was approved.", "whose", "which", "that", "whom", "Whose chỉ sở hữu: whose details."),
    ],
}

# listening: (spoken text, question, correct, w1, w2, w3, explanation)
LISTENING: dict[str, list[tuple]] = {
    "PRE_A1": [
        ("Hello! My name is Tom. I am eight years old.", "How old is Tom?", "eight", "six", "seven", "nine", "Tom nói: I am eight years old."),
        ("This is my cat. Her name is Lucy.", "What is the cat's name?", "Lucy", "Lily", "Lisa", "Lena", "Tên con mèo là Lucy."),
    ],
    "A1": [
        ("I get up at six thirty and have breakfast at seven.", "When does the speaker have breakfast?", "at 7:00", "at 6:00", "at 6:30", "at 7:30", "Breakfast at seven = 7 giờ."),
        ("Can I have a cup of tea, please? No sugar.", "What does the speaker want?", "tea without sugar", "coffee with sugar", "tea with sugar", "water", "Người nói muốn trà không đường."),
    ],
    "A2": [
        ("The train to Hue leaves at half past nine from platform four.", "Which platform does the train leave from?", "platform four", "platform two", "platform three", "platform five", "Platform four."),
        ("I'm sorry I'm late. The bus broke down, so I walked the last two kilometres.", "Why is the speaker late?", "The bus broke down", "They missed the train", "They woke up late", "They got lost", "The bus broke down = xe buýt hỏng."),
    ],
    "B1": [
        ("Passengers for flight 218 to Singapore are asked to go to gate twelve, as the original gate has been changed.", "What has changed?", "the gate", "the flight time", "the destination", "the airline", "The original gate has been changed."),
        ("I was going to cook tonight, but I'm so tired that I think I'll just order a pizza.", "What will the speaker probably do?", "order a pizza", "cook dinner", "go to bed without eating", "eat at a restaurant", "I'll just order a pizza."),
    ],
    "B2": [
        ("Although the museum is free on Sundays, I'd recommend booking in advance because it gets extremely crowded.", "What does the speaker advise?", "Book ahead", "Go on Monday", "Avoid the museum", "Pay at the door", "Recommend booking in advance = nên đặt trước."),
        ("Sales fell slightly in the first quarter, but the new marketing campaign should help us recover by summer.", "What does the speaker expect?", "Sales will recover by summer", "Sales will keep falling", "The campaign will stop", "Prices will rise", "Should help us recover by summer."),
    ],
    "C1": [
        ("Frankly, I'd have thought the committee would be more receptive to the idea, given how much groundwork we laid beforehand.", "How does the speaker feel?", "surprised and disappointed", "pleased", "indifferent", "relieved", "Người nói không ngờ ủy ban lại ít cởi mở."),
        ("The findings, while promising, should be treated with caution, as the sample size was relatively small.", "What is the speaker's attitude to the findings?", "cautiously optimistic", "completely certain", "strongly negative", "uninterested", "Hứa hẹn nhưng cần thận trọng."),
    ],
}

# reading: (passage, question, correct, w1, w2, w3, explanation)
READING: dict[str, list[tuple]] = {
    "PRE_A1": [
        ("Mai has a red bag. She has two books in the bag.", "What colour is Mai's bag?", "red", "blue", "green", "black", "Mai has a red bag."),
        ("I like dogs. My dog is big. His name is Max.", "What is the dog's name?", "Max", "Mac", "Mark", "Mike", "His name is Max."),
    ],
    "A1": [
        ("Tom lives in Da Nang. He works in a shop. He goes to work by bike.", "How does Tom go to work?", "by bike", "by bus", "on foot", "by car", "He goes to work by bike."),
        ("Lan has a brother and a sister. Her brother is ten and her sister is five.", "How old is Lan's sister?", "five", "ten", "fifteen", "seven", "Her sister is five."),
    ],
    "A2": [
        ("Last Saturday, Nam wanted to play football, but it rained all day. So he stayed at home and read a comic book.", "Why did Nam stay at home?", "It rained all day", "He was ill", "He had homework", "He had no friends", "It rained all day."),
        ("The café opens at 8 a.m. and closes at 6 p.m. It is closed on Mondays, but on Sundays it stays open until 8 p.m.", "When does the café close on Sundays?", "at 8 p.m.", "at 6 p.m.", "at 8 a.m.", "It is closed", "On Sundays it stays open until 8 p.m."),
    ],
    "B1": [
        ("Many people think that learning a language is only about grammar. However, research shows that regular speaking practice, even for ten minutes a day, helps learners remember words better.", "What helps learners remember words better?", "Speaking regularly", "Studying only grammar", "Reading long books", "Taking exams", "Regular speaking practice helps."),
        ("Linh applied for a job at an international company. Although she was nervous, she prepared well for the interview and answered every question confidently. A week later, she received an offer.", "What happened after the interview?", "She got a job offer", "She was rejected", "She applied again", "She was too nervous to answer", "She received an offer."),
    ],
    "B2": [
        ("Remote work has changed city life. Many companies now allow employees to work from home several days a week, which has reduced traffic in the mornings but has also left some city-centre cafés with fewer customers.", "What is one effect of remote work mentioned?", "Some cafés have fewer customers", "There is more traffic", "Rents are higher", "Working hours are longer", "Some city-centre cafés have fewer customers."),
        ("The author argues that cheap flights, while convenient for travellers, impose hidden environmental costs that ticket prices do not reflect.", "What is the author's main point?", "Cheap flights have hidden environmental costs", "Flights are too expensive", "Travelling is unnecessary", "Airlines should fly more", "Chi phí môi trường ẩn không nằm trong giá vé."),
    ],
    "C1": [
        ("Although the policy was ostensibly designed to reduce inequality, critics contend that its unintended consequences have disproportionately burdened the very communities it was meant to protect.", "What do the critics claim?", "The policy has harmed the groups it aimed to help", "The policy has fully succeeded", "The policy was never implemented", "The policy only affects wealthy communities", "Hậu quả ngoài ý muốn gây hại cho chính nhóm được bảo vệ."),
        ("The scientist was reluctant to draw firm conclusions from the data, noting that correlation does not necessarily imply causation.", "Why was the scientist cautious?", "A link between two things does not prove one causes the other", "The data was missing", "She disliked the topic", "The results were obvious", "Tương quan không có nghĩa là nhân quả."),
    ],
}


def _level(effective_level: str) -> str:
    return effective_level if effective_level in LEVELS else ("C1" if effective_level == "C2" else "A1")


def _shuffle(question: str, correct: str, wrongs: list[str]) -> tuple[dict[str, str], str]:
    """Place the correct option at a position derived from the question text."""
    pos = zlib.crc32(question.encode("utf-8")) % 4
    options = list(wrongs[:3])
    options.insert(pos, correct)
    letters = ["A", "B", "C", "D"]
    return dict(zip(letters, options)), letters[pos]


def bank_question(skill: str, effective_level: str, occurrence: int = 0) -> dict:
    """A placement question of `skill` at `effective_level` in the PlacementQuestionOutput shape."""
    level = _level(effective_level)
    if skill == "grammar":
        items, passage_kind = GRAMMAR[level], None
    elif skill == "reading":
        items, passage_kind = READING[level], "passage"
    elif skill == "listening":
        items, passage_kind = LISTENING[level], "audio"
    else:
        items, passage_kind = VOCABULARY[level], None
    item = items[occurrence % len(items)]
    if passage_kind:
        text, question, correct, w1, w2, w3, explanation = item
    else:
        text = ""
        question, correct, w1, w2, w3, explanation = item
    options, answer = _shuffle(question, correct, [w1, w2, w3])
    return {
        "skill": skill if skill in ("vocabulary", "grammar", "reading", "listening") else "vocabulary",
        "level": level,
        "passage": text if passage_kind == "passage" else "",
        "audio_text": text if passage_kind == "audio" else "",
        "question": question,
        "options": options,
        "correct_answer": answer,
        "explanation": explanation,
        "effective_level": level,
    }
