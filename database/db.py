"""
Optimized Supabase Database Module.
With caching, connection pooling, and parallel queries.
"""
import logging
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from functools import wraps
import time

from supabase import create_client, Client

import config

logger = logging.getLogger(__name__)

# ============================================
# CACHE SYSTEM
# ============================================

class Cache:
    """Simple in-memory cache with TTL."""
    
    def __init__(self):
        self._data: Dict[str, tuple] = {}  # key -> (value, expires_at)
    
    def get(self, key: str) -> Optional[Any]:
        if key in self._data:
            value, expires_at = self._data[key]
            if time.time() < expires_at:
                return value
            del self._data[key]
        return None
    
    def set(self, key: str, value: Any, ttl: int = 300):
        self._data[key] = (value, time.time() + ttl)
    
    def delete(self, key: str):
        self._data.pop(key, None)
    
    def clear_prefix(self, prefix: str):
        keys = [k for k in self._data if k.startswith(prefix)]
        for k in keys:
            del self._data[k]
    
    def clear(self):
        self._data.clear()


cache = Cache()

# Cache TTLs (seconds)
TTL_SHORT = 60       # 1 min - user data
TTL_MEDIUM = 300     # 5 min - services, resources
TTL_LONG = 600       # 10 min - settings, mentors


def cached(prefix: str, ttl: int = TTL_MEDIUM):
    """Decorator for caching function results."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            key = f"{prefix}:{':'.join(str(a) for a in args)}"
            result = cache.get(key)
            if result is not None:
                return result
            result = await func(*args, **kwargs)
            if result is not None:
                cache.set(key, result, ttl)
            return result
        return wrapper
    return decorator


# ============================================
# SUPABASE CLIENT
# ============================================

_client: Optional[Client] = None


def get_db() -> Client:
    """Get Supabase client singleton."""
    global _client
    if _client is None:
        url = config.SUPABASE_URL
        key = config.SUPABASE_KEY
        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY required")
        _client = create_client(url, key)
    return _client


async def init_db() -> None:
    """Initialize database connection."""
    try:
        db = get_db()
        db.table("bot_settings").select("key").limit(1).execute()
        logger.info("✅ Supabase connected")
        await _init_defaults()
        # Warm up cache
        asyncio.create_task(_warm_cache())
    except Exception as e:
        logger.error(f"❌ DB connection failed: {e}")
        raise


async def _warm_cache():
    """Pre-load frequently used data."""
    try:
        await asyncio.gather(
            get_services(),
            get_resources(),
            get_mentors(),
            get_direct_payment_settings(),
            return_exceptions=True
        )
        logger.info("✅ Cache warmed up")
    except:
        pass


async def _init_defaults() -> None:
    """Initialize default settings."""
    db = get_db()
    
    defaults = [
        ("maintenance_mode", "false", "Maintenance mode"),
        ("welcome_message", "Добро пожаловать!", "Welcome"),
        ("min_payout_amount", "50", "Min payout"),
    ]
    
    for key, value, desc in defaults:
        existing = db.table("bot_settings").select("key").eq("key", key).execute()
        if not existing.data:
            db.table("bot_settings").insert({"key": key, "value": value, "description": desc}).execute()
    
    existing = db.table("direct_payment_settings").select("id").eq("id", 1).execute()
    if not existing.data:
        db.table("direct_payment_settings").insert({
            "id": 1, "requisites": "Не настроено", "support_username": "support"
        }).execute()


# ============================================
# USER OPERATIONS
# ============================================

async def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    """Get user by ID (cached short)."""
    key = f"user:{user_id}"
    result = cache.get(key)
    if result is not None:
        return result
    
    data = get_db().table("users").select("*").eq("id", user_id).execute()
    result = data.data[0] if data.data else None
    if result:
        cache.set(key, result, TTL_SHORT)
    return result


async def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """Get user by username."""
    result = get_db().table("users").select("*").eq("username", username).execute()
    return result.data[0] if result.data else None


async def create_user(user_id: int, username: str, full_name: str,
                      experience_text: Optional[str], source_text: str,
                      referrer_id: Optional[int] = None) -> None:
    """Create new user."""
    data = {
        "id": user_id, "username": username, "full_name": full_name,
        "experience_text": experience_text, "source_text": source_text, "status": "pending"
    }
    if referrer_id:
        data["referrer_id"] = referrer_id
    get_db().table("users").insert(data).execute()


async def get_user_referrer(user_id: int) -> Optional[Dict[str, Any]]:
    """Get user's referrer."""
    user = await get_user(user_id)
    if not user or not user.get("referrer_id"):
        return None
    return await get_user(user["referrer_id"])


async def get_user_referrals(user_id: int) -> List[Dict[str, Any]]:
    """Get users referred by this user."""
    result = get_db().table("users").select("*").eq("referrer_id", user_id).execute()
    return result.data or []


async def get_referral_stats(user_id: int) -> Dict[str, Any]:
    """Get referral statistics."""
    user, referrals = await asyncio.gather(
        get_user(user_id),
        get_user_referrals(user_id)
    )
    return {
        "count": len(referrals),
        "earnings": float(user.get("referral_earnings", 0)) if user else 0
    }


async def update_referrer_earnings(referrer_id: int, amount: float) -> None:
    """Add referral earnings."""
    user = await get_user(referrer_id)
    if user:
        new_earnings = float(user.get("referral_earnings", 0)) + amount
        get_db().table("users").update({"referral_earnings": new_earnings}).eq("id", referrer_id).execute()
        cache.delete(f"user:{referrer_id}")


async def create_referral_profit(referrer_id: int, referral_id: int, profit_id: int, amount: float) -> int:
    """Create referral profit record."""
    result = get_db().table("referral_profits").insert({
        "referrer_id": referrer_id, "referral_id": referral_id,
        "profit_id": profit_id, "amount": amount, "status": "hold"
    }).execute()
    return result.data[0]["id"] if result.data else 0


async def get_unpaid_referral_summary() -> List[Dict[str, Any]]:
    """Get unpaid referral profits summary."""
    result = get_db().rpc("get_unpaid_referral_summary").execute()
    return result.data or []


async def mark_referral_profits_paid(user_id: int) -> int:
    """Mark referral profits as paid."""
    db = get_db()
    count = db.table("referral_profits").select("id", count="exact").eq("referrer_id", user_id).eq("status", "hold").execute().count or 0
    db.table("referral_profits").update({"status": "paid", "paid_at": datetime.utcnow().isoformat()}).eq("referrer_id", user_id).eq("status", "hold").execute()
    return count


async def get_user_referral_profits(user_id: int) -> List[Dict[str, Any]]:
    """Get user's referral profit history."""
    result = get_db().table("referral_profits").select("*, referral:referral_id(username, full_name)").eq("referrer_id", user_id).order("created_at", desc=True).execute()
    return result.data or []


async def create_mentor_profit(mentor_id: int, mentor_user_id: int, student_id: int, profit_id: int, amount: float, percent: int) -> int:
    """Create mentor profit record."""
    result = get_db().table("mentor_profits").insert({
        "mentor_id": mentor_id, "mentor_user_id": mentor_user_id, "student_id": student_id,
        "profit_id": profit_id, "amount": amount, "percent": percent, "status": "hold"
    }).execute()
    return result.data[0]["id"] if result.data else 0


async def get_unpaid_mentor_summary() -> List[Dict[str, Any]]:
    """Get unpaid mentor profits summary."""
    result = get_db().rpc("get_unpaid_mentor_summary").execute()
    return result.data or []


async def mark_mentor_profits_paid(user_id: int) -> int:
    """Mark mentor profits as paid."""
    db = get_db()
    count = db.table("mentor_profits").select("id", count="exact").eq("mentor_user_id", user_id).eq("status", "hold").execute().count or 0
    db.table("mentor_profits").update({"status": "paid", "paid_at": datetime.utcnow().isoformat()}).eq("mentor_user_id", user_id).eq("status", "hold").execute()
    return count


async def get_user_mentor_profits(user_id: int) -> List[Dict[str, Any]]:
    """Get user's mentor profit history."""
    result = get_db().table("mentor_profits").select("*, student:student_id(username, full_name)").eq("mentor_user_id", user_id).order("created_at", desc=True).execute()
    return result.data or []


async def update_user_status(user_id: int, status: str) -> None:
    """Update user status."""
    get_db().table("users").update({"status": status}).eq("id", user_id).execute()
    cache.delete(f"user:{user_id}")


async def update_user_wallet(user_id: int, wallet: str) -> None:
    """Update user wallet."""
    get_db().table("users").update({"wallet_address": wallet}).eq("id", user_id).execute()
    cache.delete(f"user:{user_id}")


async def update_user_activity(user_id: int) -> None:
    """Update last activity (fire and forget)."""
    try:
        get_db().table("users").update({"last_activity": datetime.utcnow().isoformat()}).eq("id", user_id).execute()
    except:
        pass


async def get_active_user_ids() -> List[int]:
    """Get all active user IDs."""
    result = get_db().table("users").select("id").eq("status", "active").execute()
    return [r["id"] for r in result.data or []]


# ============================================
# PROFIT OPERATIONS
# ============================================

async def create_profit(worker_id: int, amount: float, net_profit: float, service_name: str) -> int:
    """Create profit record."""
    result = get_db().table("profits").insert({
        "worker_id": worker_id, "amount": amount,
        "net_profit": net_profit, "service_name": service_name, "status": "hold"
    }).execute()
    cache.delete(f"user:{worker_id}")
    cache.clear_prefix(f"stats:{worker_id}")
    return result.data[0]["id"] if result.data else 0


async def get_user_profits(user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
    """Get user's profit history."""
    result = get_db().table("profits").select("*").eq("worker_id", user_id).order("created_at", desc=True).limit(limit).execute()
    return result.data or []


async def get_user_stats(user_id: int) -> Dict[str, Any]:
    """Get user statistics (cached)."""
    key = f"stats:{user_id}"
    result = cache.get(key)
    if result:
        return result
    
    db = get_db()
    data = db.rpc("get_user_stats", {"p_user_id": user_id}).execute()
    
    if data.data:
        stats = data.data[0]
        breakdown = db.table("profits").select("service_name, net_profit").eq("worker_id", user_id).execute()
        services = {}
        for r in breakdown.data or []:
            svc = r["service_name"]
            services[svc] = services.get(svc, 0) + float(r["net_profit"])
        stats["service_breakdown"] = [{"service_name": k, "service_profit": v} for k, v in services.items()]
        cache.set(key, stats, TTL_SHORT)
        return stats
    
    return {"total_count": 0, "total_profit": 0, "avg_profit": 0, "max_profit": 0,
            "month_profit": 0, "week_profit": 0, "day_profit": 0, "service_breakdown": []}


async def get_unpaid_summary() -> List[Dict[str, Any]]:
    """Get unpaid profits summary."""
    result = get_db().rpc("get_unpaid_profits_summary").execute()
    return result.data or []


async def mark_profits_paid(user_id: int) -> int:
    """Mark profits as paid."""
    db = get_db()
    count = db.table("profits").select("id", count="exact").eq("worker_id", user_id).eq("status", "hold").execute().count or 0
    db.table("profits").update({"status": "paid", "paid_at": datetime.utcnow().isoformat()}).eq("worker_id", user_id).eq("status", "hold").execute()
    cache.clear_prefix(f"stats:{user_id}")
    return count


# ============================================
# RANKINGS (cached)
# ============================================

@cached("top", TTL_SHORT)
async def get_top_workers(period: str = "all", limit: int = 10) -> List[Dict[str, Any]]:
    """Get top workers (cached)."""
    result = get_db().rpc("get_top_workers", {"p_period": period, "p_limit": limit}).execute()
    return result.data or []


async def get_user_position(user_id: int) -> Dict[str, Any]:
    """Get user's ranking position."""
    key = f"pos:{user_id}"
    result = cache.get(key)
    if result:
        return result
    
    data = get_db().rpc("get_user_position", {"p_user_id": user_id}).execute()
    
    if data.data:
        pos = data.data[0]
        team_avg = float(pos.get("team_avg_profit") or 0)
        user_avg = float(pos.get("user_avg_profit") or 0)
        avg_diff = ((user_avg - team_avg) / team_avg * 100) if team_avg > 0 else 0
        
        result = {
            "overall_rank": pos.get("overall_rank") or 1,
            "overall_profit": float(pos.get("overall_profit") or 0),
            "monthly_rank": pos.get("monthly_rank") or 1,
            "monthly_profit": float(pos.get("monthly_profit") or 0),
            "total_users": pos.get("total_users") or 1,
            "user_avg_profit": user_avg,
            "team_avg_profit": team_avg,
            "avg_diff_percent": avg_diff
        }
        cache.set(key, result, TTL_SHORT)
        return result
    
    return {"overall_rank": 1, "overall_profit": 0, "monthly_rank": 1, "monthly_profit": 0,
            "total_users": 1, "user_avg_profit": 0, "team_avg_profit": 0, "avg_diff_percent": 0}


async def get_team_stats() -> Dict[str, Any]:
    """Get team statistics."""
    result = get_db().rpc("get_team_stats").execute()
    stats = result.data[0] if result.data else {"month_profit": 0, "day_profit": 0, "total_workers": 0}
    stats["top_workers"] = await get_top_workers("all", 10)
    return stats


# ============================================
# SERVICES (cached long)
# ============================================

@cached("services", TTL_MEDIUM)
async def get_services() -> List[Dict[str, Any]]:
    """Get all active services (cached)."""
    result = get_db().table("services").select("*").eq("is_active", True).order("name").execute()
    return result.data or []


async def get_service(service_id: int) -> Optional[Dict[str, Any]]:
    """Get service by ID."""
    services = await get_services()
    return next((s for s in services if s["id"] == service_id), None)


async def add_service(name: str, icon: str = "🔹", description: str = None,
                      manual_link: str = None, bot_link: str = None) -> int:
    """Add new service."""
    result = get_db().table("services").insert({
        "name": name, "icon": icon, "description": description,
        "manual_link": manual_link, "bot_link": bot_link
    }).execute()
    cache.clear_prefix("services")
    return result.data[0]["id"] if result.data else 0


async def delete_service(service_id: int) -> None:
    """Soft delete service."""
    get_db().table("services").update({"is_active": False}).eq("id", service_id).execute()
    cache.clear_prefix("services")


# ============================================
# RESOURCES (cached long)
# ============================================

@cached("resources", TTL_MEDIUM)
async def get_resources() -> List[Dict[str, Any]]:
    """Get all active resources (cached)."""
    result = get_db().table("resources").select("*").eq("is_active", True).order("type").order("title").execute()
    return result.data or []


async def add_resource(title: str, link: str, res_type: str) -> int:
    """Add new resource."""
    result = get_db().table("resources").insert({"title": title, "content_link": link, "type": res_type}).execute()
    cache.clear_prefix("resources")
    return result.data[0]["id"] if result.data else 0


async def delete_resource(resource_id: int) -> None:
    """Soft delete resource."""
    get_db().table("resources").update({"is_active": False}).eq("id", resource_id).execute()
    cache.clear_prefix("resources")


# ============================================
# MENTORS (cached)
# ============================================

@cached("mentors", TTL_MEDIUM)
async def get_mentors() -> List[Dict[str, Any]]:
    """Get all active mentors (cached)."""
    result = get_db().table("mentor_details").select("*").execute()
    return result.data or []


async def get_mentor_services() -> List[str]:
    """Get services with mentors."""
    mentors = await get_mentors()
    return sorted(set(m["service_name"] for m in mentors)) if mentors else []


async def get_mentors_by_service(service_name: str) -> List[Dict[str, Any]]:
    """Get mentors for service."""
    mentors = await get_mentors()
    return [m for m in mentors if m["service_name"] == service_name]


async def get_mentor(mentor_id: int) -> Optional[Dict[str, Any]]:
    """Get mentor by ID."""
    mentors = await get_mentors()
    return next((m for m in mentors if m["id"] == mentor_id), None)


async def get_user_mentor(user_id: int) -> Optional[Dict[str, Any]]:
    """Get user's assigned mentor."""
    user = await get_user(user_id)
    if not user or not user.get("mentor_id"):
        return None
    return await get_mentor(user["mentor_id"])


async def add_mentor(user_id: int, service_name: str, percent: int) -> int:
    """Add new mentor."""
    result = get_db().table("mentors").insert({
        "user_id": user_id, "service_name": service_name, "percent": percent
    }).execute()
    cache.clear_prefix("mentors")
    return result.data[0]["id"] if result.data else 0


async def assign_mentor(user_id: int, mentor_id: int) -> None:
    """Assign mentor to user."""
    db = get_db()
    db.table("users").update({"mentor_id": mentor_id}).eq("id", user_id).execute()
    mentor = await get_mentor(mentor_id)
    if mentor:
        db.table("mentors").update({"students_count": (mentor.get("students_count") or 0) + 1}).eq("id", mentor_id).execute()
    cache.delete(f"user:{user_id}")
    cache.clear_prefix("mentors")


async def remove_mentor(user_id: int) -> None:
    """Remove mentor from user."""
    db = get_db()
    user = await get_user(user_id)
    if user and user.get("mentor_id"):
        mentor = await get_mentor(user["mentor_id"])
        if mentor:
            db.table("mentors").update({"students_count": max(0, (mentor.get("students_count") or 0) - 1)}).eq("id", user["mentor_id"]).execute()
    db.table("users").update({"mentor_id": None}).eq("id", user_id).execute()
    cache.delete(f"user:{user_id}")
    cache.clear_prefix("mentors")


async def update_mentor_stats(mentor_id: int, profit: float) -> None:
    """Update mentor earnings."""
    mentor = await get_mentor(mentor_id)
    if mentor:
        get_db().table("mentors").update({
            "total_earned": float(mentor.get("total_earned") or 0) + profit,
            "rating": float(mentor.get("rating") or 0) + 1
        }).eq("id", mentor_id).execute()
        cache.clear_prefix("mentors")


async def delete_mentor(mentor_id: int) -> None:
    """Soft delete mentor."""
    db = get_db()
    db.table("users").update({"mentor_id": None}).eq("mentor_id", mentor_id).execute()
    db.table("mentors").update({"is_active": False}).eq("id", mentor_id).execute()
    cache.clear_prefix("mentors")
    cache.clear_prefix("user")


# ============================================
# ADMIN & LOGS
# ============================================

async def log_admin_action(admin_id: int, admin_username: str, action_type: str,
                           details: str = None, target_user_id: int = None) -> int:
    """Log admin action (fire and forget style)."""
    try:
        result = get_db().table("admin_logs").insert({
            "admin_id": admin_id, "admin_username": admin_username,
            "action_type": action_type, "action_details": details, "target_user_id": target_user_id
        }).execute()
        return result.data[0]["id"] if result.data else 0
    except:
        return 0


async def log_rank_change(user_id: int, old_rank: str, new_rank: str,
                          old_level: int, new_level: int, total_profit: float) -> int:
    """Log rank change."""
    result = get_db().table("rank_history").insert({
        "user_id": user_id, "old_rank": old_rank, "new_rank": new_rank,
        "old_level": old_level, "new_level": new_level, "total_profit": total_profit
    }).execute()
    return result.data[0]["id"] if result.data else 0


async def create_notification(user_id: int, notif_type: str, title: str, message: str) -> int:
    """Create notification."""
    result = get_db().table("notifications").insert({
        "user_id": user_id, "notification_type": notif_type, "title": title, "message": message
    }).execute()
    return result.data[0]["id"] if result.data else 0


async def get_unread_count(user_id: int) -> int:
    """Get unread notification count."""
    result = get_db().table("notifications").select("id", count="exact").eq("user_id", user_id).eq("is_read", False).execute()
    return result.count or 0


# ============================================
# SETTINGS (cached long)
# ============================================

async def get_setting(key: str, default: str = None) -> Optional[str]:
    """Get bot setting (cached)."""
    cache_key = f"setting:{key}"
    result = cache.get(cache_key)
    if result is not None:
        return result
    
    data = get_db().table("bot_settings").select("value").eq("key", key).execute()
    value = data.data[0]["value"] if data.data else default
    if value:
        cache.set(cache_key, value, TTL_LONG)
    return value


async def set_setting(key: str, value: str) -> None:
    """Set bot setting."""
    get_db().table("bot_settings").upsert({"key": key, "value": value}).execute()
    cache.delete(f"setting:{key}")


@cached("direct_payment", TTL_LONG)
async def get_direct_payment_settings() -> Optional[Dict[str, Any]]:
    """Get direct payment settings (cached)."""
    result = get_db().table("direct_payment_settings").select("*").eq("id", 1).execute()
    return result.data[0] if result.data else None


async def update_direct_payment_settings(requisites: str, info: str, support: str) -> None:
    """Update direct payment settings."""
    get_db().table("direct_payment_settings").upsert({
        "id": 1, "requisites": requisites, "additional_info": info, "support_username": support
    }).execute()
    cache.clear_prefix("direct_payment")


# ============================================
# PARALLEL DATA LOADING
# ============================================

async def get_profile_data(user_id: int) -> Dict[str, Any]:
    """Load all profile data in parallel."""
    user, stats, position, mentor = await asyncio.gather(
        get_user(user_id),
        get_user_stats(user_id),
        get_user_position(user_id),
        get_user_mentor(user_id)
    )
    return {"user": user, "stats": stats, "position": position, "mentor": mentor}


async def get_main_menu_data(user_id: int) -> Dict[str, Any]:
    """Load main menu data in parallel."""
    user, unread = await asyncio.gather(
        get_user(user_id),
        get_unread_count(user_id)
    )
    return {"user": user, "unread": unread}


# ============================================
# USERS BY STATUS & BAN/UNBAN
# ============================================

async def get_users_by_status(status: str) -> List[Dict[str, Any]]:
    """Get users by status."""
    result = get_db().table("users").select("*").eq("status", status).order("created_at", desc=True).execute()
    return result.data or []


async def ban_user(user_id: int) -> None:
    """Ban user."""
    get_db().table("users").update({"status": "banned"}).eq("id", user_id).execute()
    cache.delete(f"user:{user_id}")


async def unban_user(user_id: int) -> None:
    """Unban user (set to active)."""
    get_db().table("users").update({"status": "active"}).eq("id", user_id).execute()
    cache.delete(f"user:{user_id}")


async def get_team_stats_by_period(period: str) -> Dict[str, Any]:
    """Get team statistics by period."""
    from datetime import datetime, timedelta
    
    db = get_db()
    now = datetime.utcnow()
    
    if period == "today":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "week":
        start = now - timedelta(days=7)
    elif period == "month":
        start = now - timedelta(days=30)
    else:  # all
        start = datetime(2020, 1, 1)
    
    # Get profits in period
    profits = db.table("profits").select("net_profit, worker_id").gte("created_at", start.isoformat()).execute()
    
    total_profit = sum(float(p['net_profit']) for p in profits.data or [])
    profits_count = len(profits.data or [])
    active_workers = len(set(p['worker_id'] for p in profits.data or []))
    avg_profit = total_profit / profits_count if profits_count > 0 else 0
    
    return {
        "total_profit": total_profit,
        "profits_count": profits_count,
        "active_workers": active_workers,
        "avg_profit": avg_profit
    }
