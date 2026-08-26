# 🎭 Mafia Game Online

Современная многопользовательская веб-игра в «Мафию» в реальном времени с поддержкой азербайджанского, русского и английского языков (AZ/RU/EN), 3D-анимацией карточек ролей, синхронизацией игровых фаз (День / Голосование / Ночь), звуковыми эффектами Web Audio API и push-уведомлениями.

---

## 🚀 Особенности

- 🎲 **3D Interactive Role Cards**: Анимированные 3D карточки ролей с тактильной вибрацией и звуковыми эффектами.
- 🌐 **Мультиязычность (AZ, RU, EN)**: Переключение языков на лету с сохранением выбора.
- ☀️🌙 **Синхронизация фаз в реальном времени**:
  - **☀️ День**: Таймер речи для игроков (60 секунд).
  - **🗳️ Голосование**: Выбор исключаемого игрока.
  - **🌙 Ночь**: Затемнение экранов всех игроков («Город засыпает») с ночным колоколом.
- 📊 **Баланс сил и авто-определение победителя**: Подсчет живых сил (Мафия vs Мирный город) и уведомление о победе.
- 🔊 **Звуковой движок (Web Audio API)**: Мгновенные синтезированные звуковые эффекты без тяжелых внешних файлов.
- 📱 **Push & Vibration**: Web Notifications API и Vibration API для экранов блокировки.
- ⚡ **SQLite + SQLAlchemy**: Легковесная и надежная база данных без необходимости во внешних сервисах.
- 🐳 **Docker & GHCR CI/CD**: Автоматический деплой на VPS через GitHub Actions.

---

## 🛠️ Стек технологий

- **Backend**: Python 3.11 / Flask / Flask-SQLAlchemy / Flask-SocketIO / Gevent
- **Database**: SQLite
- **Frontend**: Vanilla JS (ES6+), HTML5, Modern CSS (Glassmorphism & 3D Transforms)
- **Real-time**: WebSockets (Socket.IO + Gevent-WebSocket)
- **Audio & Haptics**: Web Audio API, Vibration API, Web Notifications API
- **Deployment**: Docker, Nginx Reverse Proxy, Let's Encrypt SSL, GitHub Actions CI/CD

---

## 💻 Локальный запуск

```bash
# 1. Клонировать репозиторий
git clone https://github.com/HighL0ad/Mafia_Game.git
cd Mafia_Game

# 2. Создать виртуальное окружение
python3 -m venv venv
source venv/bin/activate

# 3. Установить зависимости
pip install -r requirements.txt

# 4. Запустить тесты
pytest

# 5. Запустить сервер
python app.py
```

Сервер будет доступен по адресу: `http://localhost:8000`

---

## 🚢 Деплой на VPS

Проект использует автоматизированный CI/CD Pipeline (`.github/workflows/deploy.yml`):

1. При пуше в `master` запускаются unit-тесты (`pytest`).
2. Собирается Docker-образ и публикуется в **GitHub Container Registry (`ghcr.io/highl0ad/mafia_game`)**.
3. Файл `compose.yml` копируется на VPS, и контейнер перезапускается в фоне.
4. Системный Nginx на VPS проксирует `mafia.abil.online` на локальный порт `127.0.0.1:18000`.

---

## 📄 Лицензия

MIT License
