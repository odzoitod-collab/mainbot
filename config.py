"""Bot configuration."""
from typing import List

# ============================================
# TELEGRAM BOT
# ============================================
BOT_TOKEN: str = "8451842564:AAE8wIEZyb2c4EQ8BdBa4Murtt7lSxZMRQU"
BOT_USERNAME: str = "irlteam_bot"

# ============================================
# ADMINS
# ============================================
ADMIN_IDS: List[int] = [844012884, 7606408498, 8227295387]

# ============================================
# CHANNELS & GROUPS
# ============================================
# Канал для профитов (сюда приходят уведомления о новых профитах)
PROFITS_CHANNEL_ID: int = -1003076536737
# Канал для заявок (сюда приходят анкеты новых пользователей)
APPLICATIONS_CHANNEL_ID: int = -1003424658660


# Общий чат команды
CHAT_GROUP_ID: int = -1003076536737

# ============================================
# REFERRAL SYSTEM
# ============================================
REFERRAL_PERCENT: int = 5
WEBSITE_URL: str = "https://example.com"

# ============================================
# SUPABASE DATABASE
# ============================================
SUPABASE_URL: str = "https://sqoehqvvrbbgaqvkniyw.supabase.co"
SUPABASE_KEY: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNxb2VocXZ2cmJiZ2FxdmtuaXl3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjY5ODkzODUsImV4cCI6MjA4MjU2NTM4NX0.-Qam5GFLwzFCvM2MrEYv3HbLeRYUPOLPnLRqcLPcasg"
SUPABASE_SERVICE_KEY: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNxb2VocXZ2cmJiZ2FxdmtuaXl3Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2Njk4OTM4NSwiZXhwIjoyMDgyNTY1Mzg1fQ.aGsql2VZ_l_71JQgUfxmjSMEVoLxqiu3sWhTJMTj3oc"

# ============================================
# WEB APPS (Telegram Mini Apps)
# ============================================
WEBAPP_ANALYTICS: str = "https://anakaitack-web.vercel.app/"
WEBAPP_REFERRALS: str = "https://anakaitack-web-9fio.vercel.app/"
WEBAPP_PROFITS_HISTORY: str = "https://hisrory.vercel.app/"
WEBAPP_HUB: str = "https://hisrory-vo62.vercel.app/"

# ============================================
# IMAGES
# ============================================
BRAND_IMAGE_WELCOME: str = "images/welcome.png"  # Регистрация
BRAND_IMAGE_LOGO: str = "images/logo.png"        # Всё остальное
BRAND_IMAGE_PROFIT: str = "images/профит.jpg"    # Уведомления о профитах
