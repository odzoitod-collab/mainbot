"""Database module - Optimized Supabase integration."""
from database.db import (
    # Core
    get_db, init_db, cache,
    
    # Users
    get_user, get_user_by_username, create_user,
    update_user_status, update_user_wallet, update_user_activity,
    get_active_user_ids,
    get_user_referrer, get_user_referrals, get_referral_stats, update_referrer_earnings,
    get_users_by_status, ban_user, unban_user,
    
    # Profits
    create_profit, get_user_profits, get_user_stats,
    get_unpaid_summary, mark_profits_paid,
    
    # Referral profits
    create_referral_profit, get_unpaid_referral_summary, 
    mark_referral_profits_paid, get_user_referral_profits,
    
    # Mentor profits
    create_mentor_profit, get_unpaid_mentor_summary,
    mark_mentor_profits_paid, get_user_mentor_profits,
    
    # Rankings
    get_top_workers, get_user_position, get_team_stats, get_team_stats_by_period,
    
    # Services
    get_services, get_service, add_service, delete_service,
    
    # Resources
    get_resources, add_resource, delete_resource,
    
    # Mentors
    get_mentors, get_mentor, get_user_mentor,
    get_mentor_services, get_mentors_by_service,
    add_mentor, assign_mentor, remove_mentor,
    update_mentor_stats, delete_mentor,
    
    # Admin
    log_admin_action,
    
    # Rank history
    log_rank_change,
    
    # Notifications
    create_notification, get_unread_count,
    
    # Settings
    get_setting, set_setting,
    get_direct_payment_settings, update_direct_payment_settings,
    
    # Parallel loaders
    get_profile_data, get_main_menu_data,
)

__all__ = [
    "get_db", "init_db", "cache",
    "get_user", "get_user_by_username", "create_user",
    "update_user_status", "update_user_wallet", "update_user_activity",
    "get_active_user_ids",
    "get_user_referrer", "get_user_referrals", "get_referral_stats", "update_referrer_earnings",
    "get_users_by_status", "ban_user", "unban_user",
    "create_profit", "get_user_profits", "get_user_stats",
    "get_unpaid_summary", "mark_profits_paid",
    "create_referral_profit", "get_unpaid_referral_summary",
    "mark_referral_profits_paid", "get_user_referral_profits",
    "create_mentor_profit", "get_unpaid_mentor_summary",
    "mark_mentor_profits_paid", "get_user_mentor_profits",
    "get_top_workers", "get_user_position", "get_team_stats", "get_team_stats_by_period",
    "get_services", "get_service", "add_service", "delete_service",
    "get_resources", "add_resource", "delete_resource",
    "get_mentors", "get_mentor", "get_user_mentor",
    "get_mentor_services", "get_mentors_by_service",
    "add_mentor", "assign_mentor", "remove_mentor",
    "update_mentor_stats", "delete_mentor",
    "log_admin_action", "log_rank_change",
    "create_notification", "get_unread_count",
    "get_setting", "set_setting",
    "get_direct_payment_settings", "update_direct_payment_settings",
    "get_profile_data", "get_main_menu_data",
]
