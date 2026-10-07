# CompileHub

Онлайн-компилятор: код пишется в браузере, сервер компилирует и выполняет его в песочнице
и потоком отдаёт вывод, с интерактивным вводом. Аккаунты, файлы и папки, гостевой режим.

**Статус:** в разработке, переписывается на новый стек.

**Стек:** Python 3.12 · FastAPI · PostgreSQL · Redis Streams · nsjail · React · TypeScript · Vite · CodeMirror · xterm.js

## Структура

| Папка | Что |
|---|---|
| `api/` | API на FastAPI: аккаунты, файлы, запуски, поток вывода по WebSocket |
| `worker/` | воркер: задачи из очереди Redis → компиляция и запуск в nsjail |
| `protocol/` | общие модели API и воркера: задачи, события, вердикты |
| `frontend/` | веб-интерфейс на React |
| `deploy/` | docker compose и конфиги nginx |

## Разработка

```sh
uv sync --all-packages        # Python-пакеты в .venv
uv run pytest -q              # тесты
uv run ruff check . && uv run ruff format --check .

cd frontend && npm ci && npm run dev
```

## Авторы

- **Пётр Сапрыкин** ([@PetrSaprykin](https://github.com/PetrSaprykin)) — дизайн и исходный фронтенд
- **Егор Деев** ([@EDeev](https://github.com/EDeev)) — бэкенд, песочница, фронтенд, деплой
