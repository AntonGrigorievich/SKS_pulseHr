# Технический обзор PulseHR

PulseHR - веб-приложение для корпоративных HR-опросов. Проект состоит из FastAPI backend, React frontend, PostgreSQL, Redis и Docker Compose окружения. MVP покрывает вход по OTP, JWT-авторизацию, роли HR/EMPLOYEE, создание и публикацию опросов, назначение опросов сотрудникам, прохождение анонимных и неанонимных опросов, правила ветвления вопросов, базовую аналитику, MVP-уведомления и экспорт ответов в CSV/XLSX.

Документ описывает фактическое устройство проекта: какие технологии используются, в каких файлах они находятся и как данные проходят через систему.

## 1. Назначение проекта

Главная доменная сущность проекта - HR-опрос. HR-пользователь создает структуру опроса, добавляет вопросы, настраивает правила показа/скрытия вопросов, публикует опрос и назначает его сотрудникам. Сотрудник авторизуется по телефону, видит доступные опубликованные опросы, начинает прохождение, отправляет ответы и завершает опрос. Backend хранит результаты, учитывает анонимность, проверяет обязательные видимые вопросы на сервере и отдает агрегаты для аналитики.

Основные сценарии:

- OTP-вход по телефону и выпуск JWT access/refresh токенов.
- Управление пользователями и ролями.
- CRUD для опросов со статусами `DRAFT`, `PUBLISHED`, `CLOSED`, `ARCHIVED`.
- Создание вопросов типов `SINGLE_CHOICE`, `MULTIPLE_CHOICE`, `RATING`, `TEXT`, `MATRIX`.
- Сортировка вопросов и хранение позиции вопроса в опросе.
- Визуальное ветвление вопросов через правила `SHOW_QUESTION` и `HIDE_QUESTION`.
- Прохождение опросов сотрудником с пошаговым сохранением ответов.
- Анонимные ответы через `anonymous_session_id` без привязки `user_id`.
- HR-аналитика по completion rate, response rate, eNPS, отделам, timeline и уведомлениям.
- MVP-уведомления с записью доставок в БД без реальных внешних провайдеров.
- Синхронный экспорт ответов в локальную директорию `exports/`.

## 2. Общая архитектура

Проект разделен на две основные части:

- `app/` - backend на FastAPI.
- `frontend/` - SPA на React/Vite.

Backend построен слоями:

- `app/main.py` - точка входа FastAPI, регистрация health check и общего роутера.
- `app/api/` - HTTP-роутеры FastAPI. Здесь находятся URL, зависимости ролей и Pydantic request/response модели.
- `app/services/` - бизнес-логика. Сервисы создают сущности, проверяют статусы, выполняют вычисления, коммитят транзакции.
- `app/repositories/` - низкоуровневый доступ к БД через SQLAlchemy select/insert/update и eager-loading.
- `app/models/` - SQLAlchemy ORM модели и enum-типы домена.
- `app/schemas/` - Pydantic v2 схемы API-контрактов.
- `app/core/` - настройки, JWT, зависимости авторизации.
- `app/db/` - async SQLAlchemy engine/session и Redis client.
- `alembic/` - миграции PostgreSQL.

Frontend построен как SPA:

- `frontend/src/main.tsx` - инициализация React, Ant Design locale, TanStack Query.
- `frontend/src/router/AppRouter.tsx` - маршруты, shell с боковым меню, защита страниц по наличию access token.
- `frontend/src/api/client.ts` - единый `fetch`-клиент с подстановкой `Authorization: Bearer`.
- `frontend/src/stores/authStore.ts` - Zustand store с persist-хранением JWT.
- `frontend/src/pages/` - страницы логина, employee-потока и HR-потока.
- `frontend/src/components/QuestionRenderer.tsx` - рендер типов вопросов при прохождении.
- `frontend/src/features/surveyLogic/evaluateRules.ts` - клиентская версия движка видимости вопросов.

Инфраструктура:

- `docker-compose.yml` поднимает `api`, `postgres`, `redis`, `frontend`.
- `Dockerfile` собирает backend на `python:3.12-slim`.
- `frontend/Dockerfile` собирает frontend на `node:22-alpine`.
- Alembic миграции запускаются перед стартом Uvicorn в `api` контейнере.

## 3. Технологии и где они используются

Backend:

- Python 3.12 - версия runtime backend.
- FastAPI 0.115 - HTTP API, зависимости, OpenAPI, роутеры в `app/api/`.
- Uvicorn - ASGI-сервер, запускается как `uvicorn app.main:app`.
- SQLAlchemy 2.0 Async - ORM и запросы к PostgreSQL, модели в `app/models/`, сессии в `app/db/session.py`.
- asyncpg - async-драйвер PostgreSQL, используется в `postgresql+asyncpg://...`.
- PostgreSQL 16 - основное постоянное хранилище.
- Alembic - миграции схемы БД в `alembic/versions/`.
- Redis 7 - временное хранилище OTP-кодов, rate-limit и счетчиков попыток.
- Pydantic v2 - request/response схемы в `app/schemas/`.
- pydantic-settings - загрузка `.env` и построение `database_url`/`redis_url`.
- PyJWT - выпуск и проверка JWT access/refresh токенов.
- openpyxl - генерация XLSX-экспортов.
- Ruff - dev-инструмент линтинга, настроен в `pyproject.toml`.

Frontend:

- React 19 - UI-приложение.
- TypeScript 5.6 - типизация frontend-контрактов.
- Vite 5 - dev server, сборка и proxy backend-маршрутов.
- React Router 6 - маршрутизация SPA.
- TanStack Query 5 - загрузка, кэширование и инвалидирование серверных данных.
- Zustand 5 - auth-store с persist-хранением токенов.
- Ant Design 5 - основная UI-библиотека, формы, таблицы, карточки, layout, меню, уведомления.
- `@ant-design/v5-patch-for-react-19` - совместимость Ant Design с React 19.
- react-hook-form + zod - форма логина и валидация телефона/OTP.
- dnd-kit - drag-and-drop сортировка вопросов в конструкторе.
- `@xyflow/react` - граф правил ветвления в Blueprint-режиме.
- Recharts - графики HR-аналитики.

Dev/infra:

- Docker Compose - локальная сборка и запуск всех сервисов.
- PostgreSQL volume `postgres_data` - хранение БД между перезапусками.
- Redis volume `redis_data` - хранение Redis-данных между перезапусками.
- Vite proxy - проксирование `/auth`, `/users`, `/surveys`, `/employee`, `/responses`, `/analytics`, `/notifications`, `/exports` на backend.

## 4. Backend: точка входа и конфигурация

Backend-приложение создается в `app/main.py`.

`FastAPI` получает:

- `title=settings.app_name`;
- `debug=settings.debug`;
- lifespan handler, который при завершении закрывает Redis client через `close_redis()`.

Роуты:

- `GET /health` возвращает `{"status": "ok"}`.
- `api_router` подключается с префиксом `settings.api_prefix`.

По умолчанию `api_prefix = ""`, поэтому endpoint-ы доступны напрямую: `/auth/send-code`, `/surveys`, `/employee/dashboard` и так далее.

Настройки находятся в `app/core/config.py`. Класс `Settings` наследуется от `BaseSettings`, читает `.env` и игнорирует лишние переменные. В нем описаны:

- параметры приложения: `app_name`, `app_env`, `debug`, `api_prefix`;
- PostgreSQL: host, port, db, user, password;
- Redis: host, port, db;
- JWT: secret, algorithm, TTL access/refresh;
- OTP: TTL, rate-limit, максимум попыток проверки.

`database_url` и `redis_url` вычисляются через `cached_property`, чтобы все остальные слои использовали готовые connection string.

## 5. Backend: база данных и транзакции

SQLAlchemy async-сессия настроена в `app/db/session.py`.

Особенности:

- `create_async_engine(settings.database_url, pool_pre_ping=True, pool_size=10, max_overflow=20)`;
- `async_sessionmaker(..., expire_on_commit=False, autoflush=False)`;
- dependency `AsyncSessionDep` отдает `AsyncSession` в роутеры и сервисы.

Транзакционная модель проекта простая: сервисы сами вызывают `session.commit()` после успешной операции. Repository-слой обычно делает `session.add()`, `flush()`, `refresh()` или `select()`, но не коммитит. Это видно в `SurveyService`, `QuestionService`, `ResponseService`, `AuthService`, `NotificationService`, `ExportService`.

Redis находится в `app/db/redis.py`.

Особенности Redis-клиента:

- lazy singleton через `_redis`;
- `Redis.from_url(settings.redis_url, decode_responses=True)`;
- dependency `RedisDep`;
- закрытие соединения в lifespan FastAPI.

## 6. Backend: слои API, service, repository

Роутеры подключаются в `app/api/router.py`.

Модули API:

- `app/api/auth.py` - OTP и refresh.
- `app/api/users.py` - управление пользователями.
- `app/api/surveys.py` - HR-опросы и employee dashboard/list/detail.
- `app/api/questions.py` - вопросы и сортировка.
- `app/api/survey_logic.py` - правила ветвления.
- `app/api/responses.py` - старт прохождения, ответы, submit.
- `app/api/analytics.py` - HR-аналитика.
- `app/api/notifications.py` - настройки, подписки, отправка MVP-уведомлений.
- `app/api/exports.py` - создание и скачивание экспортов.

Роутеры обычно делают три вещи:

- принимают Pydantic payload;
- требуют dependency роли (`HRUser`, `EmployeeUser`) и session/redis;
- вызывают метод сервиса.

Сервисы содержат бизнес-правила:

- `AuthService` - OTP, создание пользователя, выпуск и rotation refresh token.
- `SurveyService` - жизненный цикл опросов, назначения, employee dashboard.
- `QuestionService` - создание/изменение вопросов, замена options, reorder.
- `SurveyLogicService` - проверка принадлежности target question к опросу и CRUD правил.
- `ResponseService` - старт ответа, upsert ответов, проверка обязательных видимых вопросов, submit.
- `AnalyticsService` - агрегаты по ответам, назначениям, eNPS и доставкам.
- `NotificationService` - настройки, подписки, MVP-доставки.
- `ExportService` - сбор строк ответа и запись CSV/XLSX.

Repository-слой изолирует запросы:

- `SurveyRepository.get(..., with_details=True)` грузит вопросы, options, rules и responses через `selectinload`.
- `SurveyRepository.list_published_for_user()` возвращает опубликованные опросы, которые назначены пользователю или не имеют назначений вообще.
- `QuestionRepository.replace_options()` очищает старые options и добавляет новые.
- `ResponseRepository.upsert_answer()` обновляет существующий ответ по `(response_id, question_id)` или создает новый.
- `RefreshTokenRepository.get_active_by_jti()` достает только неотозванный refresh token.

## 7. Доменная модель PostgreSQL

Модели находятся в `app/models/`, миграции - в `alembic/versions/`.

Все ключевые сущности используют UUID primary key. В большинстве таблиц используется `TimestampMixin` с `created_at` и `updated_at`.

### Пользователи и авторизация

`users`:

- `id`;
- `phone` - уникальный и индексированный;
- `full_name`;
- `role` - enum `HR` или `EMPLOYEE`;
- `department`;
- `position`;
- `is_active`.

`refresh_tokens`:

- `user_id`;
- `jti` - уникальный идентификатор refresh token;
- `expires_at`;
- `revoked_at`;
- `created_at`.

Refresh token хранится в БД не целиком, а как `jti`, связанный с пользователем. При refresh старый токен отзывается через `revoked_at`, затем создается новая пара access/refresh.

### Опросы

`surveys`:

- `title`, `description`;
- `status`: `DRAFT`, `PUBLISHED`, `CLOSED`, `ARCHIVED`;
- `is_anonymous`;
- `estimated_minutes`;
- `starts_at`, `ends_at`;
- `created_by_id`.

`survey_assignments`:

- `survey_id`;
- `user_id`;
- `status`: `PENDING`, `STARTED`, `SUBMITTED`;
- `submitted_at`;
- unique constraint `(survey_id, user_id)`.

Если у опубликованного опроса нет назначений, он считается доступным всем сотрудникам. Если назначения есть, сотрудник видит только свои assigned-опросы.

### Вопросы

`questions`:

- `survey_id`;
- `title`, `description`;
- `type`: `SINGLE_CHOICE`, `MULTIPLE_CHOICE`, `RATING`, `TEXT`, `MATRIX`;
- `position`;
- `is_required`;
- `settings` JSONB.

`question_options`:

- `question_id`;
- `label`;
- `value`;
- `position`.

`settings` используется для динамических настроек:

- `max` для rating-вопросов;
- `rows` и `columns` для matrix-вопросов;
- `enps: true` для eNPS-вопросов;
- `blueprint.position` для координат узла в React Flow конструкторе.

### Правила ветвления

`survey_rules`:

- `survey_id`;
- `target_question_id`;
- `name`;
- `priority`;
- `action`: `SHOW_QUESTION` или `HIDE_QUESTION`;
- `condition` JSONB.

Условие правила хранится как JSON, чтобы frontend-конструктор мог сериализовать визуальные связи без изменения SQL-схемы.

Пример обычного условия:

```json
{
  "op": "AND",
  "conditions": [
    {
      "field": "answers.QUESTION_UUID.score",
      "operator": "gte",
      "value": 8
    }
  ]
}
```

Пример always-условия, которое frontend использует для связи без проверки значения ответа:

```json
{
  "op": "AND",
  "mode": "always",
  "source_question_id": "QUESTION_UUID",
  "conditions": []
}
```

### Ответы

`survey_responses`:

- `survey_id`;
- `user_id` - `NULL` для анонимных опросов;
- `anonymous_session_id` - случайный идентификатор для анонимного прохождения;
- `status`: `IN_PROGRESS` или `SUBMITTED`;
- `started_at`;
- `submitted_at`.

`answers`:

- `response_id`;
- `question_id`;
- `value` JSONB;
- unique constraint `(response_id, question_id)`.

Примеры `value`:

```json
{"option": "yes"}
```

```json
{"options": ["a", "b"]}
```

```json
{"score": 9}
```

```json
{"text": "Свободный ответ"}
```

```json
{"rows": {"leadership": "5", "communication": "4"}}
```

### Уведомления

`notification_settings` хранит настройки каналов пользователя:

- push;
- telegram;
- email;
- sms;
- `telegram_chat_id`;
- `email`.

`notification_subscriptions` хранит активные подписки по каналам и destination.

`notifications` хранит сообщение и payload.

`notification_deliveries` хранит доставки по пользователям и каналам со статусами `PENDING`, `SENT`, `FAILED`.

В MVP отправка не вызывает реальные SMS/Telegram/Email/Push provider API. Сервис создает delivery-записи, сразу ставит `SENT`, заполняет `sent_at` и пишет событие в логи.

### Экспорт

`export_jobs`:

- `survey_id`;
- `requested_by_id`;
- `format`: `CSV` или `XLSX`;
- `status`: `PENDING`, `READY`, `FAILED`;
- `file_path`;
- `error_message`;
- `completed_at`.

Файлы создаются локально в директории `exports/`. В Docker Compose backend-контейнер монтирует весь проект как volume, поэтому созданные файлы видны в рабочей директории.

## 8. Авторизация и роли

Авторизация реализована через OTP по телефону и JWT.

### OTP flow

1. Frontend вызывает `POST /auth/send-code` с телефоном.
2. `AuthService.send_code()` проверяет rate-limit через Redis key `otp:rate:<phone>`.
3. Если запрос разрешен, генерируется 6-значный код.
4. Код сохраняется в Redis key `otp:code:<phone>` с TTL `settings.otp_ttl_seconds`.
5. Счетчик попыток `otp:attempts:<phone>` очищается.
6. Код печатается в логи backend-контейнера.

### Verify flow

1. Frontend вызывает `POST /auth/verify-code`.
2. Backend читает `otp:code:<phone>`.
3. Увеличивает `otp:attempts:<phone>` и выставляет TTL при первой попытке.
4. Если попыток больше `settings.otp_max_verify_attempts`, возвращается `429`.
5. Если код неверный, возвращается `400`.
6. Если код верный, Redis-ключи OTP удаляются.
7. Пользователь ищется по `phone`.
8. Если пользователя нет, создается новый `EMPLOYEE`.
9. Выпускаются access token и refresh token.
10. Refresh token сохраняется в PostgreSQL по `jti`.

### JWT

JWT создается в `app/core/security.py`.

Payload access token:

- `sub` - UUID пользователя;
- `type` - `access`;
- `exp`;
- `iat`.

Payload refresh token:

- `sub`;
- `type` - `refresh`;
- `jti`;
- `exp`;
- `iat`.

Проверка access token находится в `app/core/dependencies.py`:

- `HTTPBearer` извлекает токен;
- `decode_jwt_token()` проверяет подпись и срок;
- `type` должен быть `access`;
- `sub` должен быть UUID пользователя;
- пользователь должен существовать и быть активным.

Роли:

- `HRUser` требует `current_user.role == Role.HR`;
- `EmployeeUser` требует только валидного активного пользователя.

HR-only endpoint-ы: управление опросами, вопросами, правилами, аналитикой, экспортом, пользователями, отправкой уведомлений.

Employee endpoint-ы: employee dashboard/list/detail, старт прохождения, ответы, submit, настройки уведомлений.

## 9. Жизненный цикл опроса

### Создание и редактирование

HR создает опрос через `POST /surveys`. `SurveyService.create()` создает `Survey` со статусом `DRAFT` и `created_by_id` текущего HR.

Редактирование `PATCH /surveys/{survey_id}` разрешено только для опросов в статусах:

- `DRAFT`;
- `PUBLISHED`.

Для `CLOSED` и `ARCHIVED` сервис возвращает конфликт.

Вопросы добавляются через `POST /surveys/{survey_id}/questions`. `QuestionService.create()` проверяет, что опрос существует и не архивирован. Вопрос создается вместе с options. Для choice-вопросов options обязательны с точки зрения UI, но backend-схема технически принимает пустой список.

Порядок вопросов меняется через `POST /surveys/{survey_id}/questions/reorder`. Payload содержит список `{id, position}`. Сервис проверяет, что каждый `id` принадлежит этому опросу.

### Публикация

`POST /surveys/{survey_id}/publish`:

- грузит опрос с деталями;
- проверяет, что в опросе есть хотя бы один вопрос;
- переводит статус в `PUBLISHED`.

`close` и `archive` просто меняют статус на `CLOSED` или `ARCHIVED`.

### Назначение

`POST /surveys/{survey_id}/assignments` принимает список `user_ids`.

Сервис:

- проверяет существование опроса;
- выбирает уже существующие назначения;
- создает только отсутствующие;
- ставит статус `PENDING`.

На уровне БД есть unique constraint `(survey_id, user_id)`, поэтому дублирующиеся назначения не должны появляться.

## 10. Правила ветвления и видимость вопросов

Видимость вопросов рассчитывается в двух местах:

- frontend: `frontend/src/features/surveyLogic/evaluateRules.ts`;
- backend: `app/services/response_service.py`.

Это сделано намеренно. Frontend мгновенно меняет список вопросов в интерфейсе прохождения, а backend повторно проверяет видимость при submit и не доверяет клиенту.

Поддерживаемые операции условия:

- `ALWAYS` или `mode: "always"`;
- `AND`;
- `OR`;
- `NOT`;
- `equals`;
- `lte`;
- `gte`;
- `in`.

Контекст вычисления:

```json
{
  "answers": {
    "QUESTION_UUID": {
      "score": 9
    }
  }
}
```

`read_path()` читает вложенные поля по строке вроде `answers.<question_id>.score`.

Алгоритм `visible_questions()`:

1. Сортирует правила по `priority`.
2. Для каждого сработавшего правила:
   - `HIDE_QUESTION` добавляет target question в `hidden`;
   - `SHOW_QUESTION` добавляет target question в `explicitly_shown`.
3. Сортирует вопросы по `position`.
4. Исключает hidden-вопросы.
5. Если у вопроса есть хотя бы одно `SHOW_QUESTION` правило, вопрос виден только если он попал в `explicitly_shown`.
6. Вопросы без show-правил видны по умолчанию, если не скрыты hide-правилом.

Важная особенность: `SHOW_QUESTION` работает как условное включение. Наличие show-правила делает вопрос скрытым по умолчанию до выполнения условия.

## 11. Прохождение опроса сотрудником

Employee dashboard:

- `GET /employee/dashboard` возвращает количество активных и завершенных опросов, общий процент завершения и карточки опросов.
- `GET /employee/surveys` возвращает список опубликованных доступных опросов.
- `GET /employee/surveys/{survey_id}` возвращает структуру опроса, вопросы и правила.

Старт прохождения:

1. Frontend открывает `SurveyPassPage`.
2. Пользователь нажимает Start.
3. Frontend вызывает `POST /employee/surveys/{survey_id}/start`.
4. `ResponseService.start()` проверяет, что опрос существует и опубликован.
5. Если `survey.is_anonymous = true`, создается `SurveyResponse` с `user_id = NULL` и `anonymous_session_id = secrets.token_urlsafe(32)`.
6. Если опрос не анонимный, `user_id` равен текущему пользователю.
7. Assignment переводится в `STARTED`.
8. Frontend получает `response_id` и предупреждение об анонимности.

Сохранение ответов:

1. Каждый ответ отправляется через `POST /responses/{response_id}/answers`.
2. Payload содержит `question_id` и `value`.
3. Backend проверяет, что response принадлежит пользователю или является анонимным.
4. Backend проверяет, что вопрос принадлежит тому же опросу.
5. `ResponseRepository.upsert_answer()` создает или обновляет ответ по `(response_id, question_id)`.

Завершение:

1. Frontend вызывает `POST /responses/{response_id}/submit`.
2. Backend получает response с answers.
3. Загружает опрос с questions/rules.
4. Рассчитывает видимые вопросы на сервере.
5. Проверяет, что все обязательные видимые вопросы имеют ответы.
6. Если есть пропуски, возвращает `422` с `question_ids`.
7. Если все корректно, переводит response в `SUBMITTED`.
8. Заполняет `submitted_at`.
9. Assignment переводится в `SUBMITTED`.

## 12. Анонимность

Анонимность задается флагом `surveys.is_anonymous`.

Для анонимного опроса:

- `survey_responses.user_id = NULL`;
- `anonymous_session_id` заполнен случайным token-safe значением;
- ответы связаны только с `survey_response`;
- employee UI показывает текст: `Этот опрос анонимный. HR не сможет определить автора ответа.`

Для неанонимного опроса:

- `survey_responses.user_id` хранит UUID сотрудника;
- employee UI показывает текст: `Ваши ответы будут доступны HR.`

Техническое ограничение текущего MVP: `_get_owned_response()` разрешает доступ к response, если `user_id` равен текущему пользователю, а для анонимного response `user_id` равен `NULL`. Поэтому анонимный response не привязан к пользователю на уровне ownership-проверки, а безопасность опирается на знание `response_id`. Для production-версии стоит связывать анонимный response с серверной сессией/одноразовым submit-токеном или хранить приватную привязку отдельно от HR-доступа.

## 13. Аналитика

HR-аналитика реализована в `app/services/analytics_service.py` и доступна через `/analytics`.

Endpoint-ы:

- `GET /analytics/overview`;
- `GET /analytics/surveys/{survey_id}`;
- `GET /analytics/surveys/{survey_id}/enps`;
- `GET /analytics/surveys/{survey_id}/departments`;
- `GET /analytics/surveys/{survey_id}/timeline`;
- `GET /analytics/notifications`.

Метрики:

- `active_surveys` - количество опубликованных опросов.
- `completion_rate` - доля assignment-ов со статусом `SUBMITTED`.
- `response_rate` - доля `survey_responses` со статусом `SUBMITTED`.
- `enps` - индекс eNPS по rating-ответам с `Question.settings["enps"] == true`.
- `latest_responses` - последние 10 отправленных ответов.
- `department_analytics` - количество submitted responses по `User.department`.
- `timeline` - количество submitted responses по датам.
- `notification_efficiency` - delivery counts по channel/status.

Формула eNPS:

```text
((promoters - detractors) / total_scores) * 100
```

Где:

- promoters - оценки `>= 9`;
- detractors - оценки `<= 6`;
- passive ответы `7-8` учитываются в denominator, но не входят в promoters/detractors.

Frontend-страница `frontend/src/pages/hr/AnalyticsPage.tsx` пока показывает overview-метрики в простом BarChart через Recharts.

## 14. Уведомления

Уведомления - MVP-реализация без внешних провайдеров.

Employee endpoint-ы:

- `GET /notifications/settings`;
- `PATCH /notifications/settings`;
- `GET /notifications/subscriptions`;
- `POST /notifications/subscriptions`.

HR endpoint:

- `POST /notifications/send`.

`NotificationService.get_settings()` лениво создает настройки пользователя, если их еще нет.

`NotificationService.send()`:

1. Создает запись `notifications`.
2. Для каждого `user_id` и каждого канала создает `notification_deliveries`.
3. Сразу ставит статус `SENT`.
4. Заполняет `sent_at`.
5. Пишет событие в logger.

Реальная интеграция с Telegram Bot API, SMTP, SMS-шлюзом или push-сервисом в проекте пока отсутствует.

## 15. Экспорт

Экспорт реализован в `app/services/export_service.py`.

Endpoint-ы:

- `POST /exports/surveys/{survey_id}` - создать export job;
- `GET /exports/{export_id}` - получить статус job;
- `GET /exports/{export_id}/download` - скачать готовый файл.

Процесс:

1. HR отправляет `ExportCreate` с форматом `CSV` или `XLSX`.
2. Backend проверяет существование опроса.
3. Создает `ExportJob` со статусом `PENDING`.
4. Синхронно собирает строки через join `SurveyResponse -> Answer -> Question`.
5. Создает директорию `exports/`, если ее нет.
6. Записывает файл:
   - CSV через стандартный модуль `csv`;
   - XLSX через `openpyxl.Workbook`.
7. Переводит job в `READY`.
8. Записывает `file_path` и `completed_at`.

Колонки экспорта:

- `response_id`;
- `submitted_at`;
- `anonymous_session_id`;
- `user_id`;
- `question`;
- `answer`.

Техническое ограничение: экспорт выполняется синхронно в HTTP-запросе. Для больших опросов стоит вынести генерацию в background worker или очередь задач.

## 16. Frontend: инициализация и routing

Инициализация находится в `frontend/src/main.tsx`.

Приложение оборачивается в:

- `React.StrictMode`;
- `ConfigProvider` Ant Design с русской локалью `ru_RU`;
- `QueryClientProvider` TanStack Query.

Маршруты находятся в `frontend/src/router/AppRouter.tsx`.

Публичный маршрут:

- `/login`.

Все остальные маршруты находятся внутри `Shell`. Если `accessToken` отсутствует, shell делает redirect на `/login`.

Employee routes:

- `/employee`;
- `/employee/surveys`;
- `/employee/surveys/:surveyId`;
- `/notifications`.

HR routes:

- `/hr`;
- `/hr/surveys`;
- `/hr/surveys/:surveyId/builder`;
- `/hr/analytics`.

В текущем frontend нет отдельной проверки роли в router. Доступ фактически ограничивается backend-ответами `403` для HR-only endpoint-ов.

## 17. Frontend: API-клиент и состояние авторизации

`frontend/src/api/client.ts` содержит функцию `apiRequest<T>()`.

Она:

- берет access token из `useAuthStore.getState()`;
- отправляет `Content-Type: application/json`;
- добавляет `Authorization: Bearer <token>`, если токен есть;
- при ошибке пытается прочитать JSON `detail`;
- возвращает typed JSON как `Promise<T>`.

`frontend/src/stores/authStore.ts` использует Zustand persist middleware.

Store хранит:

- `accessToken`;
- `refreshToken`;
- `setTokens()`;
- `logout()`.

Данные сохраняются под ключом `pulsehr-auth`, поэтому пользователь остается залогинен после reload страницы.

Техническое ограничение: frontend пока не делает автоматический refresh access token при `401`. Refresh endpoint есть на backend, но клиентский interceptor/повтор запроса не реализован.

## 18. Frontend: логин

Страница `frontend/src/pages/LoginPage.tsx` использует:

- react-hook-form;
- zod schema;
- Ant Design Form/Input/Button/Card;
- TanStack Query mutations.

Flow:

1. Пользователь вводит телефон.
2. Нажимает Send code.
3. Frontend вызывает `POST /auth/send-code`.
4. OTP печатается в логах backend.
5. Пользователь вводит 6-значный код.
6. Frontend вызывает `POST /auth/verify-code`.
7. Полученные `access_token` и `refresh_token` сохраняются в Zustand.
8. Router переводит пользователя на `/employee`.

## 19. Frontend: HR-управление опросами

`frontend/src/pages/hr/SurveyManagementPage.tsx`:

- грузит `/surveys` через `useQuery`;
- показывает таблицу Ant Design;
- создает опрос через modal form;
- вызывает actions `/publish`, `/close`, `/archive`;
- invalidates query `["surveys"]`;
- ведет в builder по `/hr/surveys/:surveyId/builder`.

`frontend/src/pages/hr/SurveyBuilderPage.tsx` - основная страница конструктора.

Режимы builder:

- `Blueprint` - визуальный граф вопросов и правил через React Flow.
- `Questions` - список вопросов с drag-and-drop сортировкой через dnd-kit.
- `Rules` - список правил в карточках.

Вопросы:

- создаются через `POST /surveys/{survey_id}/questions`;
- обновляются через `PATCH /questions/{question_id}`;
- удаляются через `DELETE /questions/{question_id}`;
- сортируются через `POST /surveys/{survey_id}/questions/reorder`.

Настройки вопроса формируются на клиенте:

- rating: `settings.max`;
- matrix: `settings.rows`, `settings.columns`;
- React Flow layout: `settings.blueprint.position`.

Граф правил:

- каждый вопрос становится node;
- выходы node строятся из типа вопроса:
  - single choice: `option`;
  - multiple choice: `options`;
  - rating: `score`;
  - text: `text`;
  - matrix: `rows.<row>`;
  - plus always-output;
- связь между node открывает modal создания правила;
- правило сохраняется через `POST /surveys/{survey_id}/rules`;
- редактирование идет через `PATCH /rules/{rule_id}`;
- удаление через `DELETE /rules/{rule_id}`.

Позиции node:

- при drag stop позиция округляется и сохраняется во временный `pendingNodePositions`;
- кнопка Save survey сохраняет позиции через `PATCH /questions/{id}` в `settings.blueprint.position`;
- unsaved-позиции показываются тегом в topbar.

Дубликаты правил фильтруются на клиенте: builder сравнивает source field, operator, value, target question и action.

## 20. Frontend: прохождение опроса

`frontend/src/pages/employee/SurveyPassPage.tsx`:

- загружает `/employee/surveys/{surveyId}`;
- хранит локально `responseId`;
- хранит локально answers как `Record<questionId, value>`;
- рассчитывает `visibleQuestions` через клиентский `evaluateRules`;
- вызывает `/start`, `/answers`, `/submit`.

`frontend/src/components/QuestionRenderer.tsx` рендерит типы вопросов:

- `SINGLE_CHOICE` - `Radio.Group`, value `{option}`;
- `MULTIPLE_CHOICE` - `Checkbox.Group`, value `{options}`;
- `RATING` - `Rate`, value `{score}`;
- `MATRIX` - Ant Design `Table` с radio-ячейками, value `{rows}`;
- `TEXT` - `Input.TextArea`, value `{text}`.

Ответ отправляется на backend сразу при изменении значения. Клиентская видимость обновляется по локальному состоянию answers, поэтому условные вопросы появляются/исчезают без дополнительного запроса.

## 21. Frontend: аналитика и уведомления

`frontend/src/pages/hr/AnalyticsPage.tsx`:

- грузит `/analytics/overview`;
- строит BarChart по `completion_rate`, `response_rate`, `enps`.

`frontend/src/pages/employee/NotificationSettingsPage.tsx`:

- использует endpoint-ы настроек и подписок уведомлений;
- работает с MVP-моделью каналов.

Визуальный слой в целом построен на Ant Design:

- `Layout.Sider` и `Menu` в shell;
- `Card`, `Table`, `Modal`, `Form`, `Input`, `Select`, `Switch`, `Tag`, `Space`, `Button`;
- `message` для результата mutations.

## 22. API map

System:

- `GET /health`

Auth:

- `POST /auth/send-code`
- `POST /auth/verify-code`
- `POST /auth/refresh`

Users:

- `POST /users`
- `GET /users`
- `GET /users/{user_id}`
- `PATCH /users/{user_id}`
- `DELETE /users/{user_id}`

HR surveys:

- `POST /surveys`
- `GET /surveys`
- `GET /surveys/{survey_id}`
- `PATCH /surveys/{survey_id}`
- `POST /surveys/{survey_id}/publish`
- `POST /surveys/{survey_id}/close`
- `POST /surveys/{survey_id}/archive`
- `POST /surveys/{survey_id}/assignments`

Questions:

- `POST /surveys/{survey_id}/questions`
- `PATCH /questions/{question_id}`
- `DELETE /questions/{question_id}`
- `POST /surveys/{survey_id}/questions/reorder`

Survey logic:

- `POST /surveys/{survey_id}/rules`
- `PATCH /rules/{rule_id}`
- `DELETE /rules/{rule_id}`

Employee surveys:

- `GET /employee/dashboard`
- `GET /employee/surveys`
- `GET /employee/surveys/{survey_id}`
- `POST /employee/surveys/{survey_id}/start`

Responses:

- `GET /responses/{response_id}`
- `POST /responses/{response_id}/answers`
- `POST /responses/{response_id}/submit`

Analytics:

- `GET /analytics/overview`
- `GET /analytics/surveys/{survey_id}`
- `GET /analytics/surveys/{survey_id}/enps`
- `GET /analytics/surveys/{survey_id}/departments`
- `GET /analytics/surveys/{survey_id}/timeline`
- `GET /analytics/notifications`

Notifications:

- `GET /notifications/settings`
- `PATCH /notifications/settings`
- `GET /notifications/subscriptions`
- `POST /notifications/subscriptions`
- `POST /notifications/send`

Exports:

- `POST /exports/surveys/{survey_id}`
- `GET /exports/{export_id}`
- `GET /exports/{export_id}/download`

## 23. Docker и локальный запуск

`docker-compose.yml` поднимает четыре сервиса.

`api`:

- build context: `.`.
- env: `.env`.
- port: `8000:8000`.
- depends on healthy PostgreSQL and Redis.
- command:

```bash
alembic upgrade head &&
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

- volume: `.:/app`.

`postgres`:

- image: `postgres:16-alpine`;
- db: `pulsehr`;
- user: `pulsehr`;
- password: `pulsehr_password`;
- port: `5432:5432`;
- healthcheck через `pg_isready`.

`redis`:

- image: `redis:7-alpine`;
- port: `6379:6379`;
- healthcheck через `redis-cli ping`.

`frontend`:

- build context: `./frontend`;
- port: `5173:5173`;
- env:
  - `CHOKIDAR_USEPOLLING=true`;
  - `VITE_PROXY_API_TARGET=http://pulsehr-api:8000`;
- volumes:
  - `./frontend:/app`;
  - `/app/node_modules`.

Полный запуск:

```bash
docker compose up --build
```

После старта:

- Backend: `http://localhost:8000`
- OpenAPI: `http://localhost:8000/docs`
- Frontend: `http://localhost:5173`

## 24. Миграции

Alembic настроен через `alembic.ini` и `alembic/env.py`.

Текущие миграции:

- `20260608_0001_create_users_and_refresh_tokens.py` - enum `role`, таблицы `users`, `refresh_tokens`.
- `20260608_0002_create_survey_domain.py` - весь survey domain: опросы, вопросы, правила, ответы, уведомления, экспорт, индексы и enum-типы.

Применить миграции внутри контейнера:

```bash
docker compose exec api alembic upgrade head
```

Создать новую миграцию:

```bash
docker compose exec api alembic revision --autogenerate -m "message"
```

Сбросить локальные данные:

```bash
docker compose down -v
docker compose up --build
```

`down -v` удаляет Docker volumes PostgreSQL и Redis.

## 25. Сборка и проверки

Backend зависимости описаны в:

- `requirements.txt`;
- `pyproject.toml`.

Frontend зависимости и scripts описаны в `frontend/package.json`.

Frontend scripts:

- `npm run dev` - Vite dev server;
- `npm run build` - `tsc -b && vite build`;
- `npm run preview` - preview собранного приложения.

Backend dev dependency:

- `ruff==0.6.8`.

В репозитории сейчас нет отдельного test suite. Для smoke-проверки используются:

- `GET /health`;
- OpenAPI в `/docs`;
- frontend build;
- ручной OTP flow через логи backend.

## 26. Текущие ограничения MVP

Проект функционален как MVP, но некоторые части намеренно упрощены:

- OTP не отправляется через внешний SMS provider, а печатается в логи.
- Frontend хранит JWT в persisted local storage через Zustand, без httpOnly cookie.
- Автоматический refresh access token на frontend не реализован.
- Frontend router не скрывает HR-разделы по роли, роль проверяет backend.
- Анонимный response не привязан к приватной клиентской сессии на backend ownership-уровне.
- Уведомления не интегрированы с реальными email/SMS/Telegram/push провайдерами.
- Экспорт выполняется синхронно внутри HTTP-запроса.
- Analytics считает базовые агрегаты напрямую SQL-запросами без materialized views/cache.
- Нет фоновых задач, очереди, scheduler-а и retry-механизма доставок.
- Нет автоматических backend/frontend тестов в текущей структуре репозитория.

## 27. Краткая схема потоков данных

Создание опроса:

```text
React HR UI
  -> apiRequest()
  -> FastAPI /surveys
  -> SurveyService
  -> SurveyRepository
  -> PostgreSQL surveys
```

Создание правила:

```text
React Flow connection
  -> rule modal
  -> JSON condition
  -> FastAPI /surveys/{id}/rules
  -> SurveyLogicService
  -> PostgreSQL survey_rules.condition JSONB
```

Прохождение опроса:

```text
Employee UI
  -> GET survey detail
  -> client-side visibleQuestions()
  -> POST /start
  -> SurveyResponse IN_PROGRESS
  -> POST /answers on change
  -> Answer.value JSONB upsert
  -> POST /submit
  -> backend visible_questions()
  -> required validation
  -> SurveyResponse SUBMITTED
  -> SurveyAssignment SUBMITTED
```

Аналитика:

```text
HR Analytics UI
  -> GET /analytics/overview
  -> AnalyticsService
  -> SQL агрегаты по surveys, assignments, responses, answers, deliveries
  -> Recharts BarChart
```

Экспорт:

```text
HR UI/API
  -> POST /exports/surveys/{id}
  -> ExportService
  -> SELECT responses + answers + questions
  -> CSV/openpyxl writer
  -> exports/survey_<survey_id>_<job_id>.<csv|xlsx>
  -> ExportJob READY
  -> GET /exports/{job_id}/download
```
