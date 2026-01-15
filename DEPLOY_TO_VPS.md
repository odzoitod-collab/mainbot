# Развертывание бота на VPS сервере

## Данные сервера

- **IP:** 208.92.227.207
- **OS:** Ubuntu 20.04
- **Login:** root
- **Password:** 0ZkJ5CkPKEBq4F9z
- **Параметры:** 2 vCPU, 4 GB RAM, 78.1 GB Disk

---

## Шаг 1: Подключение к серверу

### С Mac/Linux:
```bash
ssh root@208.92.227.207
# Введите пароль: 0ZkJ5CkPKEBq4F9z
```

### С Windows (PowerShell):
```powershell
ssh root@208.92.227.207
# Введите пароль: 0ZkJ5CkPKEBq4F9z
```

---

## Шаг 2: Обновление системы

```bash
# Обновляем пакеты
apt update && apt upgrade -y

# Устанавливаем необходимые пакеты
apt install -y python3 python3-pip python3-venv git nano htop curl
```

---

## Шаг 3: Проверка Python

```bash
# Проверяем версию Python (Ubuntu 20.04 идет с Python 3.8, этого достаточно)
python3 --version

# Должно показать Python 3.8.x - это нормально, бот работает с Python 3.8+
```

---

## Шаг 4: Загрузка бота на сервер

**ВАЖНО:** Эту команду нужно выполнить на вашем Mac, а НЕ на сервере!

### Откройте НОВЫЙ терминал на Mac (не подключенный к серверу):

```bash
# На вашем Mac:
cd ~/Desktop/MainBotForIRL
rsync -avz --progress mainbot/ root@208.92.227.207:/root/mainbot/
```

Эта команда загрузит все файлы бота с вашего Mac на сервер.

---

## Шаг 5: Настройка окружения на сервере

**Теперь вернитесь в терминал, подключенный к серверу:**

```bash
cd /root/mainbot

# Создаем виртуальное окружение
python3 -m venv venv

# Активируем
source venv/bin/activate

# Устанавливаем зависимости
pip install --upgrade pip
pip install -r requirements.txt
```

---

## Шаг 6: Настройка переменных окружения

**ВАЖНО:** Токены и ключи уже есть в config.py, поэтому .env файл создавать НЕ НУЖНО!

Бот будет использовать настройки из `config.py`. Если в будущем захотите использовать .env:

```bash
# Создаем .env файл (опционально)
nano .env
```

Добавьте в файл:
```env
BOT_TOKEN=ваш_токен_бота
SUPABASE_URL=ваш_supabase_url
SUPABASE_KEY=ваш_supabase_key
```

Сохраните: `Ctrl+O`, `Enter`, `Ctrl+X`

---

## Шаг 7: Создание systemd сервиса

```bash
# Создаем файл сервиса
nano /etc/systemd/system/mainbot.service
```

Вставьте:
```ini
[Unit]
Description=Main Bot for IRL
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/mainbot
Environment="PATH=/root/mainbot/venv/bin"
ExecStart=/root/mainbot/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Сохраните: `Ctrl+O`, `Enter`, `Ctrl+X`

---

## Шаг 8: Запуск бота

```bash
# Перезагружаем systemd
systemctl daemon-reload

# Включаем автозапуск
systemctl enable mainbot

# Запускаем бота
systemctl start mainbot

# Проверяем статус
systemctl status mainbot

# Смотрим логи
journalctl -u mainbot -f
```

---

## Управление ботом

### Остановить бота:
```bash
systemctl stop mainbot
```

### Перезапустить бота:
```bash
systemctl restart mainbot
```

### Посмотреть логи:
```bash
# Последние 100 строк
journalctl -u mainbot -n 100

# В реальном времени
journalctl -u mainbot -f

# За последний час
journalctl -u mainbot --since "1 hour ago"
```

### Проверить статус:
```bash
systemctl status mainbot
```

---

## Шаг 9: Обновление бота

### Через rsync (с вашего Mac):
```bash
cd ~/Desktop/MainBotForIRL
rsync -avz --progress mainbot/ root@208.92.227.207:/root/mainbot/

# Перезапускаем бота на сервере
ssh root@208.92.227.207 "systemctl restart mainbot"
```

### Или на сервере:
```bash
cd /root/mainbot
git pull  # если используете git
systemctl restart mainbot
```

---

## Шаг 10: Настройка файрвола (опционально)

```bash
# Устанавливаем UFW
apt install -y ufw

# Разрешаем SSH
ufw allow 22/tcp

# Включаем файрвол
ufw enable

# Проверяем статус
ufw status
```

---

## Мониторинг

### Использование ресурсов:
```bash
# CPU и память
htop

# Дисковое пространство
df -h

# Процессы Python
ps aux | grep python
```

### Автоматический перезапуск при падении:

Systemd автоматически перезапустит бота если он упадет (настроено в сервисе: `Restart=always`)

---

## Резервное копирование

### Создать бэкап:
```bash
cd /opt/bots
tar -czf mainbot-backup-$(date +%Y%m%d).tar.gz mainbot/
```

### Скачать бэкап на Mac:
```bash
scp root@208.92.227.207:/opt/bots/mainbot-backup-*.tar.gz ~/Desktop/
```

---

## Полезные команды

### Проверить что бот работает:
```bash
curl -s https://api.telegram.org/bot<YOUR_TOKEN>/getMe
```

### Очистить логи:
```bash
journalctl --vacuum-time=7d  # Удалить логи старше 7 дней
```

### Перезагрузить сервер:
```bash
reboot
```

---

## Troubleshooting

### Бот не запускается:

1. Проверьте логи:
```bash
journalctl -u mainbot -n 50
```

2. Проверьте права на файлы:
```bash
ls -la /opt/bots/mainbot/
```

### Проверьте виртуальное окружение:
```bash
source /root/mainbot/venv/bin/activate
python --version
pip list
```

### Ошибка "Module not found":

```bash
cd /root/mainbot
source venv/bin/activate
pip install -r requirements.txt
systemctl restart mainbot
```

### Бот работает но не отвечает:

1. Проверьте токен в .env
2. Проверьте подключение к Supabase
3. Проверьте логи на ошибки

---

## Быстрый скрипт развертывания

Создайте файл `deploy.sh` на вашем Mac:

```bash
#!/bin/bash

# Переменные
SERVER="root@208.92.227.207"
LOCAL_PATH="~/Desktop/MainBotForIRL/mainbot"
REMOTE_PATH="/root/mainbot"

echo "🚀 Загрузка файлов на сервер..."
rsync -avz --progress $LOCAL_PATH/ $SERVER:$REMOTE_PATH/

echo "🔄 Перезапуск бота..."
ssh $SERVER "systemctl restart mainbot"

echo "📊 Проверка статуса..."
ssh $SERVER "systemctl status mainbot --no-pager"

echo "✅ Готово!"
```

Использование:
```bash
chmod +x deploy.sh
./deploy.sh
```

---

## Безопасность

### Создать нового пользователя (рекомендуется):

```bash
# Создаем пользователя
adduser botuser

# Добавляем в sudo группу
usermod -aG sudo botuser

# Копируем бота
cp -r /root/mainbot /home/botuser/
chown -R botuser:botuser /home/botuser/mainbot

# Обновляем сервис
nano /etc/systemd/system/mainbot.service
# Измените User=root на User=botuser
# Измените WorkingDirectory на /home/botuser/mainbot

systemctl daemon-reload
systemctl restart mainbot
```

### Отключить вход по паролю (после настройки SSH ключей):

```bash
nano /etc/ssh/sshd_config
# Найдите и измените:
# PasswordAuthentication no

systemctl restart sshd
```

---

## Готово! 🎉

Ваш бот теперь работает на VPS сервере 24/7!

Проверить: отправьте `/start` боту в Telegram
