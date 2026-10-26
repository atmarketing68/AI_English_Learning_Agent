"""
G4 · Cửa hàng & đá quý (gems) — a small cosmetic economy for younger learners.

Gems are earned by finishing lessons, claiming quests, the weekly goal and the
league, and by the 60-second blitz. They buy avatars, colours and frames.
XP stays the competitive score (league); gems are only for the shop, so the
two never fight.

Catalogue is data; purchases live on LearnerProfile (gems, avatar, owned_items).
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.learner_profile import LearnerProfile

# Gems awarded for…
GEMS_LESSON = {"S": 15, "A": 12, "B": 8, "C": 5, "D": 3}      # by lesson grade
GEMS_QUEST = 3
GEMS_WEEKLY_GOAL = 10
GEMS_LEAGUE = {1: 40, 3: 30, 10: 20}                           # by last-week rank
GEMS_BLITZ_PER_CORRECT = 1
GEMS_BLITZ_MAX = 10

DEFAULT_AVATAR = {"emoji": "🙂", "color": "sky", "frame": "none"}

# id → item. kind: avatar | color | frame. Free items are owned by everyone.
CATALOGUE: list[dict] = [
    # Avatars (emoji)
    {"id": "av_smile", "kind": "avatar", "name_vi": "Mặt cười", "value": "🙂", "price": 0},
    {"id": "av_fox", "kind": "avatar", "name_vi": "Cáo lanh lợi", "value": "🦊", "price": 30},
    {"id": "av_panda", "kind": "avatar", "name_vi": "Gấu trúc", "value": "🐼", "price": 30},
    {"id": "av_cat", "kind": "avatar", "name_vi": "Mèo con", "value": "🐱", "price": 30},
    {"id": "av_frog", "kind": "avatar", "name_vi": "Ếch xanh", "value": "🐸", "price": 40},
    {"id": "av_tiger", "kind": "avatar", "name_vi": "Hổ con", "value": "🐯", "price": 50},
    {"id": "av_koala", "kind": "avatar", "name_vi": "Gấu koala", "value": "🐨", "price": 50},
    {"id": "av_octopus", "kind": "avatar", "name_vi": "Bạch tuộc", "value": "🐙", "price": 60},
    {"id": "av_unicorn", "kind": "avatar", "name_vi": "Kỳ lân", "value": "🦄", "price": 90},
    {"id": "av_dragon", "kind": "avatar", "name_vi": "Rồng nhỏ", "value": "🐲", "price": 120},
    {"id": "av_robot", "kind": "avatar", "name_vi": "Robot Bo", "value": "🤖", "price": 150},
    {"id": "av_astronaut", "kind": "avatar", "name_vi": "Phi hành gia", "value": "🧑‍🚀", "price": 200},
    # Background colours
    {"id": "co_sky", "kind": "color", "name_vi": "Xanh trời", "value": "sky", "price": 0},
    {"id": "co_mint", "kind": "color", "name_vi": "Bạc hà", "value": "mint", "price": 15},
    {"id": "co_peach", "kind": "color", "name_vi": "Đào", "value": "peach", "price": 15},
    {"id": "co_lilac", "kind": "color", "name_vi": "Tím lilac", "value": "lilac", "price": 20},
    {"id": "co_lemon", "kind": "color", "name_vi": "Chanh vàng", "value": "lemon", "price": 20},
    {"id": "co_galaxy", "kind": "color", "name_vi": "Dải ngân hà", "value": "galaxy", "price": 60},
    # Frames
    {"id": "fr_none", "kind": "frame", "name_vi": "Không viền", "value": "none", "price": 0},
    {"id": "fr_leaf", "kind": "frame", "name_vi": "Vòng lá", "value": "leaf", "price": 40},
    {"id": "fr_star", "kind": "frame", "name_vi": "Viền sao", "value": "star", "price": 60},
    {"id": "fr_gold", "kind": "frame", "name_vi": "Viền vàng", "value": "gold", "price": 100},
    {"id": "fr_rainbow", "kind": "frame", "name_vi": "Cầu vồng", "value": "rainbow", "price": 150},
]
_BY_ID = {item["id"]: item for item in CATALOGUE}
_SLOT = {"avatar": "emoji", "color": "color", "frame": "frame"}     # item kind → avatar key
FREE_ITEMS = {item["id"] for item in CATALOGUE if item["price"] == 0}


class ShopError(ValueError):
    pass


def avatar_of(learner: LearnerProfile) -> dict:
    data = learner.avatar if isinstance(learner.avatar, dict) else {}
    return {**DEFAULT_AVATAR, **{k: v for k, v in data.items() if k in DEFAULT_AVATAR}}


def owned(learner: LearnerProfile) -> set[str]:
    items = learner.owned_items if isinstance(learner.owned_items, list) else []
    return FREE_ITEMS | {str(i) for i in items}


def award_gems(learner: LearnerProfile, amount: int) -> int:
    """Add gems (never negative). Returns the amount actually added."""
    amount = max(0, int(amount))
    learner.gems = (learner.gems or 0) + amount
    return amount


def gems_for_grade(grade: str) -> int:
    return GEMS_LESSON.get(grade, 3)


def gems_for_league_rank(rank: int | None) -> int:
    if not rank:
        return 0
    for upto, gems in sorted(GEMS_LEAGUE.items()):
        if rank <= upto:
            return gems
    return 0


def catalogue_for(learner: LearnerProfile) -> list[dict]:
    have = owned(learner)
    current = avatar_of(learner)
    out = []
    for item in CATALOGUE:
        out.append({
            **item,
            "owned": item["id"] in have,
            "equipped": current.get(_SLOT[item["kind"]]) == item["value"],
        })
    return out


def buy(db: Session, learner: LearnerProfile, item_id: str) -> dict:
    item = _BY_ID.get(item_id)
    if not item:
        raise ShopError("Không có vật phẩm này.")
    if item_id in owned(learner):
        raise ShopError("Bạn đã có vật phẩm này rồi.")
    if (learner.gems or 0) < item["price"]:
        raise ShopError(f"Chưa đủ đá quý: cần {item['price']}, bạn có {learner.gems or 0}.")
    learner.gems = (learner.gems or 0) - item["price"]
    learner.owned_items = sorted(owned(learner) - FREE_ITEMS | {item_id})
    equip(db, learner, item_id)
    return item


def equip(db: Session, learner: LearnerProfile, item_id: str) -> dict:
    item = _BY_ID.get(item_id)
    if not item:
        raise ShopError("Không có vật phẩm này.")
    if item_id not in owned(learner):
        raise ShopError("Bạn chưa sở hữu vật phẩm này.")
    avatar = avatar_of(learner)
    avatar[_SLOT[item["kind"]]] = item["value"]
    learner.avatar = avatar
    return avatar
