"""Design utilities for consistent bot styling."""

# Minimal theme symbols
EMOJI = {
    'dot_top': '╭·',
    'dot_mid': '├·',
    'dot_bottom': '╰·',
    'node_top': '╭•',
    'node_mid': '│╭•',
    'node_mid_end': '│╰•',
    'node_bottom': '╰•',
}

# Block separators
BLOCK = {
    'top': EMOJI['dot_top'],
    'middle': EMOJI['dot_mid'],
    'bottom': EMOJI['dot_bottom'],
    'line': '',
    'dot_line': '',
}

# Color indicators (kept for compatibility)
COLOR = {
    'blue': '•',
    'light_blue': '•',
    'dark_blue': '•',
    'white': '•',
    'green': '•',
    'red': '•',
    'yellow': '•',
    'purple': '•',
}


def header(title: str, icon: str = "") -> str:
    """Create a minimal header block without prefixes."""
    prefix = f"{icon} " if icon else ""
    return f"{prefix}<b>{title.upper()}</b>"


def section(title: str, content: str, icon: str = EMOJI['dot_mid']) -> str:
    """Create a section block."""
    return f"\n{icon} <b>{title}</b>\n{content}"


def info_line(label: str, value: str, icon: str = EMOJI['node_mid']) -> str:
    """Create an info line."""
    return f"{icon} <b>{label}:</b> {value}"


def block_separator() -> str:
    """Create a visual separator without dots."""
    return "\n"


def card(title: str, items: list, icon: str = EMOJI['dot_mid']) -> str:
    """Create a card-style block."""
    lines = [f"\n{icon} <b>{title}</b>"]
    for item in items:
        lines.append(f"{EMOJI['node_mid']} {item}")
    return "\n".join(lines)


def progress_bar(percentage: float, length: int = 10, filled: str = '█', empty: str = '░') -> str:
    """Create a progress bar with simple blocks."""
    filled_count = int((percentage / 100) * length)
    empty_count = length - filled_count
    return filled * filled_count + empty * empty_count


def rank_badge(rank_name: str, rank_emoji: str, bonus: int) -> str:
    """Create a rank badge (minimal, emoji kept only for compatibility)."""
    return f"{rank_name.upper()} (+{bonus}%)"


def stat_block(label: str, value: str, icon: str = EMOJI['node_mid']) -> str:
    """Create a stat block."""
    return f"{icon} {label}\n   <b>{value}</b>"


def notification_badge(count: int) -> str:
    """Create notification badge (minimal)."""
    if count == 0:
        return "0"
    elif count < 10:
        return str(count)
    else:
        return "9+"


def service_card(name: str, icon: str, description: str = None) -> str:
    """Create a service card."""
    icon_display = icon or "🛠"
    lines = [f"\n{icon_display} <b>{name}</b>"]
    if description:
        lines.append(f"   ✏️ {description}")
    return "\n".join(lines)


def profit_card(service: str, amount: float, net_profit: float, date: str, status: str) -> str:
    """Create a profit card with minimal but important info."""
    status_icon = "✅" if status == "paid" else "⏳"
    return (
        f"\n{status_icon} <b>{net_profit:.2f} RUB</b> • {service}\n"
        f"   📅 {date}"
    )


def user_card(name: str, username: str, rank_emoji: str, rank_name: str) -> str:
    """Create a user card."""
    return (
        f"\n{EMOJI['dot_mid']} <b>{name}</b>\n"
        f"{EMOJI['node_mid']} @{username}\n"
        f"{EMOJI['node_mid_end']} {rank_name}"
    )


def mentor_card(name: str, username: str, service: str, percent: int, rating: float, students: int) -> str:
    """Create a mentor card."""
    return (
        f"\n{EMOJI['dot_mid']} <b>{name}</b>\n"
        f"{EMOJI['node_mid']} @{username}\n"
        f"{EMOJI['node_mid']} Сервис: {service}\n"
        f"{EMOJI['node_mid']} Процент: {percent}%\n"
        f"{EMOJI['node_mid']} Рейтинг: {rating:.1f}\n"
        f"{EMOJI['node_mid_end']} Ученики: {students}"
    )
