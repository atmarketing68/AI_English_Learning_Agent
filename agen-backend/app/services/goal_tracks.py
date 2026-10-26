"""
G3 · Khoá theo mục tiêu — IELTS, TOEIC và phỏng vấn xin việc.

A track is a fixed sequence of lesson specs (skill + topic + level) that the
existing lesson generators turn into content, so no new agent is needed.
Progress is tracked per (learner, lesson code) in GoalTrackProgress.

Data only; no I/O.
"""
from __future__ import annotations

from typing import Optional


def _lesson(code: str, title_vi: str, skill: str, topic: str, level: str) -> dict:
    return {"code": code, "title_vi": title_vi, "skill": skill, "topic": topic, "level": level}


TRACKS: list[dict] = [
    {
        "id": "ielts",
        "emoji": "🎓",
        "title_vi": "Luyện thi IELTS (mục tiêu 5.5–6.5)",
        "title_en": "IELTS preparation",
        "description_vi": "Từ vựng học thuật, ngữ pháp hay mất điểm, đọc hiểu và nghe theo dạng đề IELTS.",
        "target_level": "B2",
        "goals": ["luyen_thi"],
        "modules": [
            {"code": "IELTS-M1", "title_vi": "Từ vựng học thuật", "lessons": [
                _lesson("IELTS-M1-L1", "Giáo dục & học tập", "vocabulary", "IELTS academic vocabulary: education and learning", "B1"),
                _lesson("IELTS-M1-L2", "Môi trường & khí hậu", "vocabulary", "IELTS academic vocabulary: environment and climate change", "B1"),
                _lesson("IELTS-M1-L3", "Công nghệ & xã hội", "vocabulary", "IELTS academic vocabulary: technology and society", "B2"),
                _lesson("IELTS-M1-L4", "Sức khoẻ & lối sống", "vocabulary", "IELTS academic vocabulary: health and lifestyle", "B2"),
            ]},
            {"code": "IELTS-M2", "title_vi": "Ngữ pháp band 6+", "lessons": [
                _lesson("IELTS-M2-L1", "Câu phức & mệnh đề quan hệ", "grammar", "Complex sentences and relative clauses for IELTS writing", "B1"),
                _lesson("IELTS-M2-L2", "Câu bị động & danh hoá", "grammar", "Passive voice and nominalisation in academic English", "B2"),
                _lesson("IELTS-M2-L3", "Câu điều kiện & giả định", "grammar", "Conditionals (types 2 and 3) for expressing opinions", "B2"),
                _lesson("IELTS-M2-L4", "Từ nối & mạch lạc", "grammar", "Linking words and cohesion for IELTS Writing Task 2", "B1"),
            ]},
            {"code": "IELTS-M3", "title_vi": "Reading & Listening theo dạng đề", "lessons": [
                _lesson("IELTS-M3-L1", "Reading: True/False/Not Given", "reading", "IELTS Reading passage about urban development with True/False/Not Given questions", "B2"),
                _lesson("IELTS-M3-L2", "Reading: nối tiêu đề đoạn", "reading", "IELTS Reading passage about renewable energy with paragraph heading questions", "B2"),
                _lesson("IELTS-M3-L3", "Listening Part 1: điền thông tin", "listening", "IELTS Listening Section 1: a phone call booking accommodation (form completion)", "B1"),
                _lesson("IELTS-M3-L4", "Listening Part 3: thảo luận học thuật", "listening", "IELTS Listening Section 3: two students discussing a research project", "B2"),
            ]},
        ],
    },
    {
        "id": "toeic",
        "emoji": "💼",
        "title_vi": "Luyện thi TOEIC (mục tiêu 600+)",
        "title_en": "TOEIC preparation",
        "description_vi": "Từ vựng văn phòng, ngữ pháp Part 5, đọc email/thông báo và nghe hội thoại nơi làm việc.",
        "target_level": "B1",
        "goals": ["luyen_thi", "cong_viec"],
        "modules": [
            {"code": "TOEIC-M1", "title_vi": "Từ vựng công sở", "lessons": [
                _lesson("TOEIC-M1-L1", "Văn phòng & nhân sự", "vocabulary", "TOEIC vocabulary: office life and human resources", "A2"),
                _lesson("TOEIC-M1-L2", "Họp hành & lịch trình", "vocabulary", "TOEIC vocabulary: meetings, schedules and appointments", "A2"),
                _lesson("TOEIC-M1-L3", "Mua bán & hợp đồng", "vocabulary", "TOEIC vocabulary: sales, orders and contracts", "B1"),
                _lesson("TOEIC-M1-L4", "Đi lại & khách sạn công tác", "vocabulary", "TOEIC vocabulary: business travel and hotels", "B1"),
            ]},
            {"code": "TOEIC-M2", "title_vi": "Ngữ pháp Part 5 & 6", "lessons": [
                _lesson("TOEIC-M2-L1", "Loại từ & vị trí từ", "grammar", "TOEIC Part 5: word forms (noun, verb, adjective, adverb) and word position", "A2"),
                _lesson("TOEIC-M2-L2", "Thì & hoà hợp chủ vị", "grammar", "TOEIC Part 5: verb tenses and subject-verb agreement", "B1"),
                _lesson("TOEIC-M2-L3", "Giới từ & liên từ", "grammar", "TOEIC Part 5: prepositions and conjunctions in business sentences", "B1"),
                _lesson("TOEIC-M2-L4", "Đại từ quan hệ & rút gọn", "grammar", "TOEIC Part 6: relative pronouns and reduced clauses in business emails", "B1"),
            ]},
            {"code": "TOEIC-M3", "title_vi": "Reading & Listening Part 3–7", "lessons": [
                _lesson("TOEIC-M3-L1", "Part 7: email & thông báo", "reading", "TOEIC Part 7: a company email and an office notice with comprehension questions", "B1"),
                _lesson("TOEIC-M3-L2", "Part 7: quảng cáo & bài báo", "reading", "TOEIC Part 7: an advertisement and a short news article", "B1"),
                _lesson("TOEIC-M3-L3", "Part 3: hội thoại nơi làm việc", "listening", "TOEIC Part 3: a conversation between two colleagues about a delayed shipment", "A2"),
                _lesson("TOEIC-M3-L4", "Part 4: thông báo ngắn", "listening", "TOEIC Part 4: an airport announcement and a voicemail message", "B1"),
            ]},
        ],
    },
    {
        "id": "interview",
        "emoji": "🤝",
        "title_vi": "Tiếng Anh phỏng vấn xin việc",
        "title_en": "Job interview English",
        "description_vi": "Giới thiệu bản thân, kể kinh nghiệm theo STAR, trả lời câu hỏi khó và hỏi ngược nhà tuyển dụng.",
        "target_level": "B1",
        "goals": ["cong_viec"],
        "modules": [
            {"code": "INT-M1", "title_vi": "Nền tảng", "lessons": [
                _lesson("INT-M1-L1", "Từ vựng CV & vị trí", "vocabulary", "Job interview vocabulary: CV, roles, responsibilities and skills", "A2"),
                _lesson("INT-M1-L2", "Giới thiệu bản thân chuyên nghiệp", "grammar", "Present simple and present perfect for talking about your experience in interviews", "A2"),
                _lesson("INT-M1-L3", "Nghe: câu hỏi phỏng vấn thường gặp", "listening", "A job interview: common questions and model answers (tell me about yourself, strengths)", "B1"),
            ]},
            {"code": "INT-M2", "title_vi": "Kể chuyện theo STAR", "lessons": [
                _lesson("INT-M2-L1", "Động từ hành động & thành tích", "vocabulary", "Action verbs and achievement vocabulary for describing work results", "B1"),
                _lesson("INT-M2-L2", "Thì quá khứ kể kinh nghiệm", "grammar", "Past simple and past continuous for STAR interview stories", "B1"),
                _lesson("INT-M2-L3", "Đọc: mô tả công việc", "reading", "Reading a job description and matching requirements to your experience", "B1"),
            ]},
            {"code": "INT-M3", "title_vi": "Câu hỏi khó & hỏi ngược", "lessons": [
                _lesson("INT-M3-L1", "Điểm yếu, lương, lý do nghỉ việc", "vocabulary", "Diplomatic language for weaknesses, salary expectations and reasons for leaving", "B1"),
                _lesson("INT-M3-L2", "Câu hỏi lịch sự & điều kiện", "grammar", "Polite questions, modal verbs and conditionals in interviews (would, could, if)", "B1"),
                _lesson("INT-M3-L3", "Nghe: cuối buổi phỏng vấn", "listening", "The end of a job interview: asking the interviewer questions and next steps", "B1"),
            ]},
        ],
    },
]

_BY_ID = {t["id"]: t for t in TRACKS}
_LESSON_INDEX: dict[str, tuple[dict, dict, dict]] = {
    lesson["code"]: (track, module, lesson)
    for track in TRACKS for module in track["modules"] for lesson in module["lessons"]
}


def list_tracks() -> list[dict]:
    return TRACKS


def get_track(track_id: str) -> Optional[dict]:
    return _BY_ID.get(track_id)


def find_lesson(code: str) -> Optional[tuple[dict, dict, dict]]:
    """(track, module, lesson) for a lesson code."""
    return _LESSON_INDEX.get(code)


def track_lesson_codes(track: dict) -> list[str]:
    return [lesson["code"] for module in track["modules"] for lesson in module["lessons"]]


def recommended_track_ids(learning_goal: Optional[str]) -> list[str]:
    return [t["id"] for t in TRACKS if learning_goal and learning_goal in t["goals"]]
