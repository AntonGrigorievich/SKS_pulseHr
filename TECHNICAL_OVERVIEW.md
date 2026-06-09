# Техническое описание PulseHR

PulseHR - веб-приложение для корпоративных HR-опросов. Проект позволяет HR создавать и публиковать опросы, назначать их сотрудникам, собирать ответы, учитывать анонимность, строить базовую аналитику, отправлять MVP-уведомления и выгружать результаты в CSV/XLSX.

## Технологический стек

Backend:
- Python 3.12
- FastAPI
- SQLAlchemy 2.0 Async
- PostgreSQL 16
- Redis 7
- Alembic
- Pydantic v2
- PyJWT
- Uvicorn
- openpyxl для XLSX-экспорта

Frontend:
- React 19
- TypeScript
- Vite
- React Router
- TanStack Query
- Zustand
- Ant Design
- dnd-kit
- React Flow (`@xyflow/react`)
- Recharts

Инфраструктура:
- Dockerfile для backend
- Dockerfile для frontend
- `docker-compose.yml` поднимает API, PostgreSQL, Redis и frontend
- Alembic-миграции применяются при старте API-контейнера

## Общая архитектура

Проект разделен на backend и frontend.

Backend находится в `app/` и построен слоями:
- `app/api` - FastAPI-роутеры и HTTP-контракты.
- `app/services` - бизнес-логика: авторизация, опросы, вопросы, ответы, аналитика, уведомления, экспорт.
- `app/repositories` - доступ к базе данных.
- `app/models` - SQLAlchemy-модели.
- `app/schemas` - Pydantic-схемы запросов и ответов.
- `app/core` - настройки, JWT, зависимости авторизации.
- `app/db` - async-сессия SQLAlchemy и Redis-клиент.

Frontend находится в `frontend/`. Он использует Vite dev server, проксирует API-запросы на backend и хранит JWT-токены в Zustand store с persist-механизмом.

## Хранение данных

Основное постоянное хранилище - PostgreSQL. В нем хранятся:
- пользователи и роли (`HR`, `EMPLOYEE`);
- refresh-токены;
- опросы и их статусы (`DRAFT`, `PUBLISHED`, `CLOSED`, `ARCHIVED`);
- назначения опросов сотрудникам;
- вопросы, варианты ответов и настройки вопросов;
- правила ветвления опросов;
- прохождения опросов и ответы;
- настройки уведомлений, подписки, уведомления и доставки;
- задания на экспорт.

Redis используется для временных OTP-кодов:
- код подтверждения телефона;
- rate limit повторной отправки;
- счетчик попыток проверки кода.

JSONB используется там, где структура гибкая: настройки вопросов, условия правил, значения ответов, payload уведомлений.

## Авторизация

Авторизация реализована через OTP по телефону и JWT.

1. Клиент вызывает `POST /auth/send-code`.
2. Backend генерирует 6-значный OTP, сохраняет его в Redis с TTL и печатает код в логи контейнера.
3. Клиент вызывает `POST /auth/verify-code`.
4. Если код верный, backend находит пользователя по телефону или создает нового с ролью `EMPLOYEE`.
5. Backend выдает access token и refresh token.
6. Refresh token сохраняется в PostgreSQL по `jti`; при обновлении старый refresh token отзывается и выпускается новая пара токенов.

Access token проверяется через FastAPI dependency. HR-эндпоинты требуют роль `HR`, employee-эндпоинты требуют активного пользователя.

## Работа с опросами

HR-сценарий:
1. HR создает опрос через `/surveys`.
2. В конструкторе добавляет вопросы через `/surveys/{survey_id}/questions`.
3. Может менять порядок вопросов через `/surveys/{survey_id}/questions/reorder`.
4. Может создавать правила ветвления через `/surveys/{survey_id}/rules`.
5. Публикует опрос через `/surveys/{survey_id}/publish`.
6. Назначает опрос пользователям через `/surveys/{survey_id}/assignments`.

Поддерживаемые типы вопросов:
- `SINGLE_CHOICE`
- `MULTIPLE_CHOICE`
- `RATING`
- `TEXT`
- `MATRIX`

Для вопросов есть `settings`: например, максимальная шкала рейтинга, строки/колонки матрицы, координаты узла в визуальном конструкторе.

## Ветвление и видимость вопросов

Правила опроса хранятся в таблице `survey_rules`. Каждое правило содержит:
- целевой вопрос;
- действие `SHOW_QUESTION` или `HIDE_QUESTION`;
- приоритет;
- JSON-условие.

Условия поддерживают логические операции `AND`, `OR`, `NOT`, режим `always`, а также сравнения `equals`, `lte`, `gte`, `in`.

Логика видимости реализована в двух местах:
- на frontend в `frontend/src/features/surveyLogic/evaluateRules.ts`, чтобы сразу показывать сотруднику актуальный набор вопросов;
- на backend в `app/services/response_service.py`, чтобы при отправке проверить обязательные видимые вопросы на сервере.

Так UI остается удобным, а сервер сохраняет контроль над корректностью финального ответа.

## Прохождение опроса сотрудником

Сотрудник видит назначенные опубликованные опросы через `/employee/surveys` и dashboard через `/employee/dashboard`.

Процесс прохождения:
1. Сотрудник открывает опрос.
2. Frontend получает структуру опроса, вопросы и правила.
3. При старте вызывается `POST /employee/surveys/{survey_id}/start`.
4. Backend создает `SurveyResponse` со статусом `IN_PROGRESS`.
5. Ответы сохраняются через `POST /responses/{response_id}/answers`.
6. При завершении вызывается `POST /responses/{response_id}/submit`.
7. Backend проверяет обязательные видимые вопросы, переводит ответ в `SUBMITTED` и обновляет назначение до `SUBMITTED`.

Если опрос анонимный, `user_id` в `survey_responses` сохраняется как `NULL`, а вместо него генерируется `anonymous_session_id`. Если опрос не анонимный, ответ связывается с пользователем.

## Аналитика, уведомления и экспорт

Аналитика доступна HR через `/analytics`:
- общий обзор;
- completion rate;
- response rate;
- eNPS;
- аналитика по отделам;
- timeline отправленных ответов;
- эффективность уведомлений.

eNPS считается по rating-вопросам, у которых в `settings` указан флаг `enps: true`.

Уведомления в MVP не интегрированы с реальными SMS, Telegram, Email или Push-провайдерами. Сервис создает записи доставок, помечает их как `SENT` и пишет информацию в логи.

Экспорт доступен HR через `/exports/surveys/{survey_id}`. Backend синхронно формирует файл в директории `exports/`, сохраняет `ExportJob` со статусом `READY` и позволяет скачать файл через `/exports/{export_id}/download`.

## Frontend-часть

Frontend использует единую оболочку с боковым меню и маршрутами:
- `/login`
- `/employee`
- `/employee/surveys`
- `/employee/surveys/:surveyId`
- `/notifications`
- `/hr`
- `/hr/surveys`
- `/hr/surveys/:surveyId/builder`
- `/hr/analytics`

Запросы выполняются через общий `apiRequest`, который автоматически добавляет `Authorization: Bearer <token>`. Данные загружаются и инвалидируются через TanStack Query.

Конструктор опросов поддерживает два способа работы:
- список вопросов с drag-and-drop сортировкой через dnd-kit;
- визуальный граф правил через React Flow, где вопросы представлены узлами, а связи превращаются в правила ветвления.

## Запуск

Локальный запуск всего проекта:

```bash
docker compose up --build
```

После старта:
- API: `http://localhost:8000`
- Swagger/OpenAPI: `http://localhost:8000/docs`
- Frontend: `http://localhost:5173`

Docker Compose поднимает PostgreSQL и Redis, применяет Alembic-миграции и запускает Uvicorn с reload-режимом.

Для отдельного запуска frontend:

```bash
cd frontend
npm install
npm run dev
```

