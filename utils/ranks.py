"""Rank system utilities."""
from typing import Dict, Tuple, Optional


def get_rank_info(total_profit: float) -> Dict[str, any]:
    """
    Get rank information based on total profit.
    
    Ranks:
    - Новичок: 0-49,999
    - Воркер: 50,000-99,999
    - Профи: 100,000-149,999
    - Эксперт: 150,000-199,999
    - Легенда: 200,000+
    """
    ranks = [
        {"name": "Новичок", "emoji": "🌱", "min": 0, "max": 49999, "bonus": 0, "color": "🟢", "level": 1},
        {"name": "Воркер", "emoji": "⚡", "min": 50000, "max": 99999, "bonus": 2, "color": "🔵", "level": 2},
        {"name": "Профи", "emoji": "💎", "min": 100000, "max": 149999, "bonus": 5, "color": "🟣", "level": 3},
        {"name": "Эксперт", "emoji": "👑", "min": 150000, "max": 199999, "bonus": 7, "color": "🟡", "level": 4},
        {"name": "Легенда", "emoji": "🔥", "min": 200000, "max": float('inf'), "bonus": 10, "color": "🔴", "level": 5}
    ]
    
    for rank in ranks:
        if rank["min"] <= total_profit <= rank["max"]:
            # Calculate progress to next rank
            if rank["max"] != float('inf'):
                progress = ((total_profit - rank["min"]) / (rank["max"] - rank["min"] + 1)) * 100
                next_rank_needed = rank["max"] + 1 - total_profit
            else:
                progress = 100
                next_rank_needed = 0
            
            return {
                "name": rank["name"],
                "emoji": rank["emoji"],
                "bonus": rank["bonus"],
                "color": rank["color"],
                "level": rank["level"],
                "progress": progress,
                "next_rank_needed": next_rank_needed,
                "current_profit": total_profit,
                "min_profit": rank["min"],
                "max_profit": rank["max"]
            }
    
    return ranks[0]  # Default to Новичок


def get_rank_badge(total_profit: float) -> str:
    """Get rank badge emoji and name."""
    rank = get_rank_info(total_profit)
    return f"{rank['emoji']} {rank['name']}"


def get_progress_bar(progress: float, length: int = 10) -> str:
    """Generate progress bar."""
    filled = int((progress / 100) * length)
    empty = length - filled
    return "█" * filled + "░" * empty


def check_rank_up(old_profit: float, new_profit: float) -> Optional[Dict[str, any]]:
    """
    Check if user ranked up.
    Returns new rank info if ranked up, None otherwise.
    """
    old_rank = get_rank_info(old_profit)
    new_rank = get_rank_info(new_profit)
    
    if new_rank["level"] > old_rank["level"]:
        return new_rank
    
    return None


def get_rank_reward_message(rank_info: Dict[str, any]) -> str:
    """Get congratulations message for rank up."""
    messages = {
        2: (
            f"🎉 <b>ПОЗДРАВЛЯЕМ С ПОВЫШЕНИЕМ!</b>\n\n"
            f"⚡ Вы достигли ранга <b>ВОРКЕР</b>!\n\n"
            f"🎁 <b>Награды:</b>\n"
            f"💰 +2% к каждому профиту\n"
            f"🔓 Доступ к расширенной статистике\n"
            f"⭐ Новый значок в профиле\n\n"
            f"Продолжайте в том же духе! 💪"
        ),
        3: (
            f"🎊 <b>НЕВЕРОЯТНО! НОВЫЙ РАНГ!</b>\n\n"
            f"💎 Вы стали <b>ПРОФИ</b>!\n\n"
            f"🎁 <b>Награды:</b>\n"
            f"💰 +5% к каждому профиту\n"
            f"👨‍🏫 Возможность стать наставником\n"
            f"🏆 Приоритет в топе команды\n"
            f"⭐ Эксклюзивный значок\n\n"
            f"Вы в топе! 🚀"
        ),
        4: (
            f"👑 <b>ЛЕГЕНДАРНОЕ ДОСТИЖЕНИЕ!</b>\n\n"
            f"👑 Вы достигли ранга <b>ЭКСПЕРТ</b>!\n\n"
            f"🎁 <b>Награды:</b>\n"
            f"💰 +7% к каждому профиту\n"
            f"💼 Доступ к VIP сервисам\n"
            f"🎯 Персональная поддержка\n"
            f"⭐ Золотой значок\n\n"
            f"Вы элита команды! 👑"
        ),
        5: (
            f"🔥 <b>МАКСИМАЛЬНЫЙ РАНГ ДОСТИГНУТ!</b>\n\n"
            f"🔥 Вы стали <b>ЛЕГЕНДОЙ</b>!\n\n"
            f"🎁 <b>Награды:</b>\n"
            f"💰 +10% к каждому профиту\n"
            f"💎 Все VIP привилегии\n"
            f"🎖️ Место в зале славы\n"
            f"⭐ Легендарный значок\n"
            f"🏆 Особый статус в команде\n\n"
            f"Вы достигли вершины! 🏔️"
        )
    }
    
    return messages.get(rank_info["level"], "🎉 Поздравляем с повышением ранга!")


def get_all_ranks() -> list:
    """Get list of all ranks."""
    return [
        {"name": "Новичок", "emoji": "🌱", "min": 0, "max": 49999, "bonus": 0, "level": 1},
        {"name": "Воркер", "emoji": "⚡", "min": 50000, "max": 99999, "bonus": 2, "level": 2},
        {"name": "Профи", "emoji": "💎", "min": 100000, "max": 149999, "bonus": 5, "level": 3},
        {"name": "Эксперт", "emoji": "👑", "min": 150000, "max": 199999, "bonus": 7, "level": 4},
        {"name": "Легенда", "emoji": "🔥", "min": 200000, "max": float('inf'), "bonus": 10, "level": 5}
    ]
