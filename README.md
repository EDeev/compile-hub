# 🚀 CompileHub

**Online Code Compilation Platform** — Backend сервер для веб-приложения онлайн компиляции и выполнения кода.

> 🔧 **Статус проекта:** В активной разработке

## 📋 Описание

CompileHub — это высокопроизводительный backend-сервис для онлайн IDE, поддерживающий компиляцию и выполнение кода на нескольких языках программирования. Проект реализует асинхронную архитектуру обработки запросов с системой очередей, rate limiting и детальной метрикой производительности.

## 🛠️ Технологический стек

### Core Framework
- **FastAPI** — современный асинхронный веб-фреймворк
- **Python 3.8+** — основной язык разработки
- **SQLite** — встроенная база данных

### Компиляторы
- **GCC (g++)** — компиляция C++17
- **Python 3** — интерпретация Python кода
- **Node.js** — выполнение JavaScript

### Дополнительные технологии
- **asyncio** — асинхронная обработка задач
- **Pydantic** — валидация данных
- **Uvicorn** — ASGI сервер

## ⚡ Ключевые возможности

- ✅ **Multi-language Support** — C++, Python, JavaScript
- ✅ **Асинхронная компиляция** — queue-based worker system
- ✅ **User Management** — регистрация, аутентификация, файловая система
- ✅ **Rate Limiting** — защита от перегрузки (30 req/min)
- ✅ **Metrics & Monitoring** — статистика компиляций в реальном времени
- ✅ **Security** — sanitization кода, защита от опасных операций
- ✅ **Timeout Control** — ограничение времени выполнения (5s)

## 📦 Установка и запуск

### Требования
```bash
Python 3.8+
Node.js (для JavaScript)
GCC/G++ (для C++)
```

### Установка зависимостей
```bash
pip install -r requirements.txt
```

### Запуск сервера
```bash
python main.py
```

Сервер запустится на `http://192.168.3.29:9999`

## 🏗️ Архитектура

```
compile-hub/
├── main.py                 # FastAPI application, endpoints, worker
├── database.py             # SQLite ORM, модели данных
├── compilers/
│   ├── base.py            # Базовый класс компилятора
│   ├── cpp.py             # C++ compiler wrapper
│   ├── python.py          # Python interpreter wrapper
│   └── javascript.py      # Node.js wrapper
├── requirements.txt        # Python dependencies
└── README.md
```

### Основные компоненты

#### 1. Compilation System
- **Queue-based processing** — асинхронная очередь задач (max 100)
- **Worker pattern** — dedicated background worker
- **Multi-compiler support** — абстрактный интерфейс компиляторов

#### 2. User Management
- Регистрация и аутентификация
- Персональная файловая система
- Контроль лимитов (количество файлов, длина кода)

#### 3. API Endpoints

**Authentication:**
- `POST /api/auth/register` — регистрация
- `POST /api/auth/login` — вход
- `GET /api/auth/check-username` — проверка доступности username

**File Management:**
- `GET /api/files` — список файлов пользователя
- `DELETE /api/files/{id}` — удаление файла
- `PATCH /api/files/{id}/move` — перемещение в папку
- `POST /api/files/migrate` — миграция файлов

**Compilation:**
- `POST /api/compile/` — компиляция кода (с input)
- `GET /api/compile/` — компиляция кода (query params)
- `GET /api/code?fileId={id}` — получение кода файла

**Monitoring:**
- `GET /api/metrics` — метрики системы

## 🔐 Безопасность

- **Code Sanitization** — фильтрация опасных операций (`system`, `exec`, `eval`)
- **Timeout Protection** — автоматическое прерывание (5 секунд)
- **Output Limiting** — максимум 1MB вывода
- **Rate Limiting** — 30 запросов в минуту на IP
- **Password Hashing** — SHA-256

## 📊 Метрики производительности

Система собирает следующие метрики:
- Общее количество компиляций
- Количество неудачных компиляций
- Success rate (%)
- Среднее время компиляции
- Активные пользователи
- Размер очереди

## 📄 Лицензия

Этот проект является некоммерческим и распространяется под лицензией MIT.

## 👨‍💻 Автор

**Деев Егор Викторович** - Backend Developer  
- GitHub: [@EDeev](https://github.com/EDeev)
- Email: egor@deev.space
- Telegram: [@Egor_Deev](https://t.me/Egor_Deev)

---

<div align="center">
  <sub>⭐ Если проект оказался полезным, поставьте звездочку на GitHub!</sub>
  <p><sub>Создано с ❤️ от вашего дорогого - deev.space ©</sub></p>
</div>
