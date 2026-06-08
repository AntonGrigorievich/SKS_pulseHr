# PulseHR Full Code

## Project Tree

```text
.
.env
.env.example
.gitignore
Dockerfile
README.md
alembic.ini
    env.py
    script.py.mako
        20260608_0001_create_users_and_refresh_tokens.py
        20260608_0002_create_survey_domain.py
    __init__.py
        __init__.py
        analytics.py
        auth.py
        exports.py
        notifications.py
        questions.py
        responses.py
        router.py
        survey_logic.py
        surveys.py
        users.py
        __init__.py
        config.py
        dependencies.py
        security.py
        __init__.py
        base.py
        redis.py
        session.py
    main.py
        __init__.py
        auth.py
        export.py
        notification.py
        question.py
        response.py
        survey.py
        survey_logic.py
        user.py
        __init__.py
        auth_repository.py
        notification_repository.py
        response_repository.py
        survey_repository.py
        user_repository.py
        __init__.py
        analytics.py
        auth.py
        export.py
        notification.py
        question.py
        response.py
        survey.py
        survey_logic.py
        user.py
        __init__.py
        analytics_service.py
        auth_service.py
        export_service.py
        notification_service.py
        question_service.py
        response_service.py
        survey_logic_service.py
        survey_service.py
        user_service.py
docker-compose.yml
    index.html
    package.json
            client.ts
            types.ts
            QuestionRenderer.tsx
                evaluateRules.ts
        main.tsx
            LoginPage.tsx
                EmployeeDashboardPage.tsx
                NotificationSettingsPage.tsx
                SurveyListPage.tsx
                SurveyPassPage.tsx
                AnalyticsPage.tsx
                HrDashboardPage.tsx
                SurveyBuilderPage.tsx
                SurveyManagementPage.tsx
            AppRouter.tsx
            authStore.ts
        styles.css
        vite-env.d.ts
    tsconfig.json
    vite.config.ts
pyproject.toml
requirements.txt
```

## .env

```text
APP_NAME=PulseHR
APP_ENV=local
DEBUG=true
API_PREFIX=

POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=pulsehr
POSTGRES_USER=pulsehr
POSTGRES_PASSWORD=pulsehr_password

REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

JWT_SECRET_KEY=change-me-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30

OTP_TTL_SECONDS=300
OTP_RATE_LIMIT_SECONDS=60
OTP_MAX_VERIFY_ATTEMPTS=5

```

## .env.example

```text
APP_NAME=PulseHR
APP_ENV=local
DEBUG=true
API_PREFIX=

POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=pulsehr
POSTGRES_USER=pulsehr
POSTGRES_PASSWORD=pulsehr_password

REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

JWT_SECRET_KEY=change-me-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30

OTP_TTL_SECONDS=300
OTP_RATE_LIMIT_SECONDS=60
OTP_MAX_VERIFY_ATTEMPTS=5

```

## .gitignore

```text
__pycache__/
.DS_Store
*.py[cod]
.pytest_cache/
.ruff_cache/
.mypy_cache/
.venv/
venv/
.env.local
postgres_data/
redis_data/

```

## Dockerfile

```dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]


```

## README.md

```markdown
# PulseHR Backend MVP

PulseHR is a FastAPI backend for corporate employee surveys with OTP login, JWT auth,
roles, anonymous survey responses, analytics, notifications, and CSV/XLSX exports.

## Stack

- Python 3.12
- FastAPI
- SQLAlchemy 2.0 Async
- PostgreSQL
- Alembic
- Redis
- Pydantic v2
- Docker Compose

## Quickstart

```bash
cp .env.example .env
docker compose up --build
```

The API will be available at:

```text
http://localhost:8000
```

OpenAPI docs:

```text
http://localhost:8000/docs
```

Health check:

```bash
curl http://localhost:8000/health
```

Docker starts PostgreSQL and Redis, runs `alembic upgrade head`, then starts Uvicorn.

## Migrations

Run migrations inside the API container:

```bash
docker compose exec api alembic upgrade head
```

Create a new migration:

```bash
docker compose exec api alembic revision --autogenerate -m "message"
```

Reset local MVP data:

```bash
docker compose down -v
docker compose up --build
```

`down -v` deletes PostgreSQL and Redis volumes.

## Auth Flow

Send OTP:

```bash
curl -X POST http://localhost:8000/auth/send-code \
  -H "Content-Type: application/json" \
  -d '{"phone":"+79991234567"}'
```

For MVP the OTP is printed to API container logs.

Verify OTP:

```bash
curl -X POST http://localhost:8000/auth/verify-code \
  -H "Content-Type: application/json" \
  -d '{"phone":"+79991234567","code":"123456"}'
```

Use the returned access token:

```bash
curl http://localhost:8000/employee/dashboard \
  -H "Authorization: Bearer ACCESS_TOKEN"
```

Refresh tokens:

```bash
curl -X POST http://localhost:8000/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"REFRESH_TOKEN"}'
```

## Roles

Existing roles:

- `HR`
- `EMPLOYEE`

HR endpoints require a user with `role = HR`. Employee endpoints require a valid active user.

For local testing, update a user role in PostgreSQL:

```sql
UPDATE users SET role = 'HR' WHERE phone = '+79991234567';
```

## Anonymous Surveys

If `survey.is_anonymous = true`:

- `survey_responses.user_id` is stored as `NULL`
- `survey_responses.anonymous_session_id` is generated
- answers are linked only to the anonymous response
- employee UI must show: `Этот опрос анонимный. HR не сможет определить автора ответа.`

If `survey.is_anonymous = false`:

- `survey_responses.user_id` stores the employee id
- employee UI must show: `Ваши ответы будут доступны HR.`

## Endpoint Map

### System

- `GET /health`

### Auth

- `POST /auth/send-code`
- `POST /auth/verify-code`
- `POST /auth/refresh`

### Users

- `POST /users`
- `GET /users`
- `GET /users/{user_id}`
- `PATCH /users/{user_id}`
- `DELETE /users/{user_id}`

### HR Surveys

- `POST /surveys`
- `GET /surveys`
- `GET /surveys/{survey_id}`
- `PATCH /surveys/{survey_id}`
- `POST /surveys/{survey_id}/publish`
- `POST /surveys/{survey_id}/close`
- `POST /surveys/{survey_id}/archive`
- `POST /surveys/{survey_id}/assignments`

### Survey Builder

- `POST /surveys/{survey_id}/questions`
- `PATCH /questions/{question_id}`
- `DELETE /questions/{question_id}`
- `POST /surveys/{survey_id}/questions/reorder`

Supported question types:

- `SINGLE_CHOICE`
- `MULTIPLE_CHOICE`
- `RATING`
- `TEXT`
- `MATRIX`

### Survey Logic

- `POST /surveys/{survey_id}/rules`
- `PATCH /rules/{rule_id}`
- `DELETE /rules/{rule_id}`

Rule conditions are stored as JSON for the frontend visual Rule Builder.

Example:

```json
{
  "op": "AND",
  "conditions": [
    {"field": "user.position", "operator": "equals", "value": "Manager"},
    {"field": "answers.question_uuid.score", "operator": "lte", "value": 2}
  ]
}
```

### Employee Surveys

- `GET /employee/dashboard`
- `GET /employee/surveys`
- `GET /employee/surveys/{survey_id}`
- `POST /employee/surveys/{survey_id}/start`

### Responses

- `GET /responses/{response_id}`
- `POST /responses/{response_id}/answers`
- `POST /responses/{response_id}/submit`

Answer payload examples:

```json
{"question_id":"uuid","value":{"option":"yes"}}
```

```json
{"question_id":"uuid","value":{"options":["a","b"]}}
```

```json
{"question_id":"uuid","value":{"score":9}}
```

```json
{"question_id":"uuid","value":{"text":"Free-form answer"}}
```

```json
{"question_id":"uuid","value":{"rows":{"leadership":"5","communication":"4"}}}
```

### Analytics

- `GET /analytics/overview`
- `GET /analytics/surveys/{survey_id}`
- `GET /analytics/surveys/{survey_id}/enps`
- `GET /analytics/surveys/{survey_id}/departments`
- `GET /analytics/surveys/{survey_id}/timeline`
- `GET /analytics/notifications`

eNPS is calculated from rating answers where question settings contain:

```json
{"enps": true}
```

### Notifications

- `GET /notifications/settings`
- `PATCH /notifications/settings`
- `GET /notifications/subscriptions`
- `POST /notifications/subscriptions`
- `POST /notifications/send`

MVP notification sending writes delivery records and logs the delivery instead of calling
real SMS, Telegram, Email, or Push providers.

### Exports

- `POST /exports/surveys/{survey_id}`
- `GET /exports/{export_id}`
- `GET /exports/{export_id}/download`

Supported formats:

- `CSV`
- `XLSX`

## Backend Module Map

```text
app/api            FastAPI routers
app/core           settings, JWT helpers, auth dependencies
app/db             async SQLAlchemy session and Redis client
app/models         SQLAlchemy models
app/repositories   database access objects
app/schemas        Pydantic API contracts
app/services       business logic
alembic/versions   database migrations
```

## Frontend Recommendation

Recommended stack:

- React 19
- TypeScript
- Vite
- React Router
- TanStack Query
- Zustand
- React Hook Form
- Zod
- Ant Design
- dnd-kit
- Recharts

Ant Design is the better fit for PulseHR because HR screens need dense tables, dashboards,
forms, modals, filters, and enterprise workflows.

## Frontend Quickstart

```bash
cd frontend
npm install
npm run dev
```

Frontend URL:

```text
http://localhost:5173
```

The Vite dev server proxies API calls to `http://localhost:8000`.

Frontend routes:

- `/login`
- `/employee`
- `/employee/surveys`
- `/employee/surveys/:surveyId`
- `/notifications`
- `/hr`
- `/hr/surveys`
- `/hr/surveys/:surveyId/builder`
- `/hr/analytics`

```

## alembic.ini

```ini
[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os
sqlalchemy.url = postgresql+asyncpg://pulsehr:pulsehr_password@postgres:5432/pulsehr

[post_write_hooks]

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S


```

## alembic/env.py

```python
from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.core.config import settings
from app.db.base import Base
import app.models  # noqa: F401

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

```

## alembic/script.py.mako

```python
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}


```

## alembic/versions/20260608_0001_create_users_and_refresh_tokens.py

```python
"""create users and refresh tokens

Revision ID: 20260608_0001
Revises:
Create Date: 2026-06-08 00:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260608_0001"
down_revision = None
branch_labels = None
depends_on = None

role_enum = postgresql.ENUM("HR", "EMPLOYEE", name="role", create_type=False)


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            CREATE TYPE role AS ENUM ('HR', 'EMPLOYEE');
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END
        $$;
        """
    )

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("phone", sa.String(length=32), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("role", role_enum, nullable=False, server_default=sa.text("'EMPLOYEE'")),
        sa.Column("department", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("phone", name="uq_users_phone"),
    )
    op.create_index("ix_users_phone", "users", ["phone"])

    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("jti", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("jti", name="uq_refresh_tokens_jti"),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_refresh_tokens_user_id", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")
    op.drop_index("ix_users_phone", table_name="users")
    op.drop_table("users")
    role_enum.drop(op.get_bind(), checkfirst=True)

```

## alembic/versions/20260608_0002_create_survey_domain.py

```python
"""create survey domain

Revision ID: 20260608_0002
Revises: 20260608_0001
Create Date: 2026-06-08 00:10:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260608_0002"
down_revision = "20260608_0001"
branch_labels = None
depends_on = None

survey_status = postgresql.ENUM("DRAFT", "PUBLISHED", "CLOSED", "ARCHIVED", name="survey_status", create_type=False)
assignment_status = postgresql.ENUM("PENDING", "STARTED", "SUBMITTED", name="assignment_status", create_type=False)
question_type = postgresql.ENUM(
    "SINGLE_CHOICE",
    "MULTIPLE_CHOICE",
    "RATING",
    "TEXT",
    "MATRIX",
    name="question_type",
    create_type=False,
)
rule_action = postgresql.ENUM("SHOW_QUESTION", "HIDE_QUESTION", name="rule_action", create_type=False)
response_status = postgresql.ENUM("IN_PROGRESS", "SUBMITTED", name="response_status", create_type=False)
notification_channel = postgresql.ENUM("PUSH", "TELEGRAM", "EMAIL", "SMS", name="notification_channel", create_type=False)
delivery_status = postgresql.ENUM("PENDING", "SENT", "FAILED", name="delivery_status", create_type=False)
export_format = postgresql.ENUM("CSV", "XLSX", name="export_format", create_type=False)
export_status = postgresql.ENUM("PENDING", "READY", "FAILED", name="export_status", create_type=False)


def _create_enum(name: str, values: tuple[str, ...]) -> None:
    labels = ", ".join(f"'{value}'" for value in values)
    op.execute(
        f"""
        DO $$
        BEGIN
            CREATE TYPE {name} AS ENUM ({labels});
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END
        $$;
        """
    )


def upgrade() -> None:
    _create_enum("survey_status", ("DRAFT", "PUBLISHED", "CLOSED", "ARCHIVED"))
    _create_enum("assignment_status", ("PENDING", "STARTED", "SUBMITTED"))
    _create_enum("question_type", ("SINGLE_CHOICE", "MULTIPLE_CHOICE", "RATING", "TEXT", "MATRIX"))
    _create_enum("rule_action", ("SHOW_QUESTION", "HIDE_QUESTION"))
    _create_enum("response_status", ("IN_PROGRESS", "SUBMITTED"))
    _create_enum("notification_channel", ("PUSH", "TELEGRAM", "EMAIL", "SMS"))
    _create_enum("delivery_status", ("PENDING", "SENT", "FAILED"))
    _create_enum("export_format", ("CSV", "XLSX"))
    _create_enum("export_status", ("PENDING", "READY", "FAILED"))

    op.add_column("users", sa.Column("position", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False))

    op.create_table(
        "surveys",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", survey_status, server_default=sa.text("'DRAFT'"), nullable=False),
        sa.Column("is_anonymous", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("estimated_minutes", sa.Integer(), server_default=sa.text("5"), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "questions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("survey_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("type", question_type, nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("is_required", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("settings", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["survey_id"], ["surveys.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "survey_assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("survey_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", assignment_status, server_default=sa.text("'PENDING'"), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["survey_id"], ["surveys.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("survey_id", "user_id", name="uq_survey_assignments_survey_user"),
    )

    op.create_table(
        "question_options",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("question_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("value", sa.String(length=255), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "survey_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("survey_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("target_question_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("priority", sa.Integer(), server_default=sa.text("100"), nullable=False),
        sa.Column("action", rule_action, nullable=False),
        sa.Column("condition", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["survey_id"], ["surveys.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_question_id"], ["questions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "survey_responses",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("survey_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("anonymous_session_id", sa.String(length=64), nullable=True),
        sa.Column("status", response_status, server_default=sa.text("'IN_PROGRESS'"), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["survey_id"], ["surveys.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "answers",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("response_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("question_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("value", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["response_id"], ["survey_responses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("response_id", "question_id", name="uq_answers_response_question"),
    )

    op.create_table(
        "notification_settings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("push_enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("telegram_enabled", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("email_enabled", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("sms_enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("telegram_chat_id", sa.String(length=128), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_notification_settings_user_id"),
    )

    op.create_table(
        "notification_subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("channel", notification_channel, nullable=False),
        sa.Column("device_name", sa.String(length=255), nullable=True),
        sa.Column("destination", sa.String(length=512), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("survey_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["survey_id"], ["surveys.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "notification_deliveries",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("notification_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("channel", notification_channel, nullable=False),
        sa.Column("status", delivery_status, server_default=sa.text("'PENDING'"), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["notification_id"], ["notifications.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "export_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("survey_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("requested_by_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("format", export_format, nullable=False),
        sa.Column("status", export_status, server_default=sa.text("'PENDING'"), nullable=False),
        sa.Column("file_path", sa.String(length=1024), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["requested_by_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["survey_id"], ["surveys.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    for table, columns in {
        "surveys": ["created_by_id", "status"],
        "questions": ["survey_id"],
        "question_options": ["question_id"],
        "survey_rules": ["survey_id", "target_question_id"],
        "survey_assignments": ["survey_id", "user_id", "status"],
        "survey_responses": ["survey_id", "user_id", "anonymous_session_id", "status"],
        "answers": ["response_id", "question_id"],
        "notification_subscriptions": ["user_id"],
        "notifications": ["survey_id"],
        "notification_deliveries": ["notification_id", "user_id"],
        "export_jobs": ["survey_id"],
    }.items():
        for column in columns:
            op.create_index(f"ix_{table}_{column}", table, [column])


def downgrade() -> None:
    for table, columns in {
        "export_jobs": ["survey_id"],
        "notification_deliveries": ["notification_id", "user_id"],
        "notifications": ["survey_id"],
        "notification_subscriptions": ["user_id"],
        "answers": ["response_id", "question_id"],
        "survey_responses": ["survey_id", "user_id", "anonymous_session_id", "status"],
        "survey_assignments": ["survey_id", "user_id", "status"],
        "survey_rules": ["survey_id", "target_question_id"],
        "question_options": ["question_id"],
        "questions": ["survey_id"],
        "surveys": ["created_by_id", "status"],
    }.items():
        for column in columns:
            op.drop_index(f"ix_{table}_{column}", table_name=table)

    op.drop_table("export_jobs")
    op.drop_table("notification_deliveries")
    op.drop_table("notifications")
    op.drop_table("notification_subscriptions")
    op.drop_table("notification_settings")
    op.drop_table("answers")
    op.drop_table("survey_responses")
    op.drop_table("survey_rules")
    op.drop_table("question_options")
    op.drop_table("survey_assignments")
    op.drop_table("questions")
    op.drop_table("surveys")
    op.drop_column("users", "is_active")
    op.drop_column("users", "position")

    export_status.drop(op.get_bind(), checkfirst=True)
    export_format.drop(op.get_bind(), checkfirst=True)
    delivery_status.drop(op.get_bind(), checkfirst=True)
    notification_channel.drop(op.get_bind(), checkfirst=True)
    response_status.drop(op.get_bind(), checkfirst=True)
    rule_action.drop(op.get_bind(), checkfirst=True)
    question_type.drop(op.get_bind(), checkfirst=True)
    assignment_status.drop(op.get_bind(), checkfirst=True)
    survey_status.drop(op.get_bind(), checkfirst=True)


```

## app/__init__.py

```python


```

## app/api/__init__.py

```python


```

## app/api/analytics.py

```python
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends

from app.core.dependencies import HRUser
from app.db.session import AsyncSessionDep
from app.schemas.analytics import AnalyticsOverview, MetricPoint, SurveyAnalytics, TimelinePoint
from app.services.analytics_service import AnalyticsService, get_analytics_service

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview", response_model=AnalyticsOverview)
async def overview(
    session: AsyncSessionDep,
    current_user: HRUser,
    service: AnalyticsService = Depends(get_analytics_service),
):
    return await service.overview(session)


@router.get("/surveys/{survey_id}", response_model=SurveyAnalytics)
async def survey_analytics(
    survey_id: UUID,
    session: AsyncSessionDep,
    current_user: HRUser,
    service: AnalyticsService = Depends(get_analytics_service),
):
    return await service.survey(session, survey_id)


@router.get("/surveys/{survey_id}/enps", response_model=dict)
async def survey_enps(
    survey_id: UUID,
    session: AsyncSessionDep,
    current_user: HRUser,
    service: AnalyticsService = Depends(get_analytics_service),
):
    data = await service.survey(session, survey_id)
    return {"survey_id": survey_id, "enps": data["enps"]}


@router.get("/surveys/{survey_id}/departments", response_model=list[MetricPoint])
async def departments(
    survey_id: UUID,
    session: AsyncSessionDep,
    current_user: HRUser,
    service: AnalyticsService = Depends(get_analytics_service),
):
    return await service.department_analytics(session, survey_id)


@router.get("/surveys/{survey_id}/timeline", response_model=list[TimelinePoint])
async def timeline(
    survey_id: UUID,
    session: AsyncSessionDep,
    current_user: HRUser,
    service: AnalyticsService = Depends(get_analytics_service),
):
    return await service.timeline(session, survey_id)


@router.get("/notifications", response_model=dict)
async def notifications(
    session: AsyncSessionDep,
    current_user: HRUser,
    service: AnalyticsService = Depends(get_analytics_service),
):
    return await service.notification_efficiency(session)


```

## app/api/auth.py

```python
from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.db.redis import RedisDep
from app.db.session import AsyncSessionDep
from app.schemas.auth import (
    RefreshTokenRequest,
    SendCodeRequest,
    SendCodeResponse,
    TokenPair,
    VerifyCodeRequest,
)
from app.services.auth_service import AuthService, get_auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/send-code", response_model=SendCodeResponse, status_code=status.HTTP_202_ACCEPTED)
async def send_code(
    payload: SendCodeRequest,
    redis: RedisDep,
    service: AuthService = Depends(get_auth_service),
) -> SendCodeResponse:
    return await service.send_code(redis, payload)


@router.post("/verify-code", response_model=TokenPair)
async def verify_code(
    payload: VerifyCodeRequest,
    session: AsyncSessionDep,
    redis: RedisDep,
    service: AuthService = Depends(get_auth_service),
) -> TokenPair:
    return await service.verify_code(session, redis, payload)


@router.post("/refresh", response_model=TokenPair)
async def refresh(
    payload: RefreshTokenRequest,
    session: AsyncSessionDep,
    service: AuthService = Depends(get_auth_service),
) -> TokenPair:
    return await service.refresh(session, payload.refresh_token)


```

## app/api/exports.py

```python
from __future__ import annotations

from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse

from app.core.dependencies import HRUser
from app.db.session import AsyncSessionDep
from app.models.export import ExportStatus
from app.schemas.export import ExportCreate, ExportJobRead
from app.services.export_service import ExportService, get_export_service

router = APIRouter(prefix="/exports", tags=["exports"])


@router.post("/surveys/{survey_id}", response_model=ExportJobRead, status_code=status.HTTP_201_CREATED)
async def create_export(
    survey_id: UUID,
    payload: ExportCreate,
    session: AsyncSessionDep,
    current_user: HRUser,
    service: ExportService = Depends(get_export_service),
):
    return await service.create(session, survey_id, payload, current_user)


@router.get("/{export_id}", response_model=ExportJobRead)
async def get_export(
    export_id: UUID,
    session: AsyncSessionDep,
    current_user: HRUser,
    service: ExportService = Depends(get_export_service),
):
    return await service.get(session, export_id)


@router.get("/{export_id}/download")
async def download_export(
    export_id: UUID,
    session: AsyncSessionDep,
    current_user: HRUser,
    service: ExportService = Depends(get_export_service),
):
    job = await service.get(session, export_id)
    if job.status != ExportStatus.READY or job.file_path is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Export is not ready")
    path = Path(job.file_path)
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Export file not found")
    return FileResponse(path=path, filename=path.name)


```

## app/api/notifications.py

```python
from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.core.dependencies import EmployeeUser, HRUser
from app.db.session import AsyncSessionDep
from app.schemas.notification import (
    NotificationCreate,
    NotificationDeliveryRead,
    NotificationSettingsRead,
    NotificationSettingsUpdate,
    NotificationSubscriptionCreate,
    NotificationSubscriptionRead,
)
from app.services.notification_service import NotificationService, get_notification_service

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/settings", response_model=NotificationSettingsRead)
async def get_settings(
    session: AsyncSessionDep,
    current_user: EmployeeUser,
    service: NotificationService = Depends(get_notification_service),
):
    return await service.get_settings(session, current_user)


@router.patch("/settings", response_model=NotificationSettingsRead)
async def update_settings(
    payload: NotificationSettingsUpdate,
    session: AsyncSessionDep,
    current_user: EmployeeUser,
    service: NotificationService = Depends(get_notification_service),
):
    return await service.update_settings(session, current_user, payload)


@router.get("/subscriptions", response_model=list[NotificationSubscriptionRead])
async def list_subscriptions(
    session: AsyncSessionDep,
    current_user: EmployeeUser,
    service: NotificationService = Depends(get_notification_service),
):
    return await service.list_subscriptions(session, current_user)


@router.post("/subscriptions", response_model=NotificationSubscriptionRead, status_code=status.HTTP_201_CREATED)
async def create_subscription(
    payload: NotificationSubscriptionCreate,
    session: AsyncSessionDep,
    current_user: EmployeeUser,
    service: NotificationService = Depends(get_notification_service),
):
    return await service.create_subscription(session, current_user, payload)


@router.post("/send", response_model=list[NotificationDeliveryRead])
async def send_notification(
    payload: NotificationCreate,
    session: AsyncSessionDep,
    current_user: HRUser,
    service: NotificationService = Depends(get_notification_service),
):
    return await service.send(session, payload)


```

## app/api/questions.py

```python
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.core.dependencies import HRUser
from app.db.session import AsyncSessionDep
from app.schemas.question import QuestionCreate, QuestionRead, QuestionReorderRequest, QuestionUpdate
from app.services.question_service import QuestionService, get_question_service

router = APIRouter(tags=["questions"])


@router.post("/surveys/{survey_id}/questions", response_model=QuestionRead, status_code=status.HTTP_201_CREATED)
async def create_question(
    survey_id: UUID,
    payload: QuestionCreate,
    session: AsyncSessionDep,
    current_user: HRUser,
    service: QuestionService = Depends(get_question_service),
):
    return await service.create(session, survey_id, payload)


@router.patch("/questions/{question_id}", response_model=QuestionRead)
async def update_question(
    question_id: UUID,
    payload: QuestionUpdate,
    session: AsyncSessionDep,
    current_user: HRUser,
    service: QuestionService = Depends(get_question_service),
):
    return await service.update(session, question_id, payload)


@router.delete("/questions/{question_id}")
async def delete_question(
    question_id: UUID,
    session: AsyncSessionDep,
    current_user: HRUser,
    service: QuestionService = Depends(get_question_service),
) -> None:
    await service.delete(session, question_id)


@router.post("/surveys/{survey_id}/questions/reorder")
async def reorder_questions(
    survey_id: UUID,
    payload: QuestionReorderRequest,
    session: AsyncSessionDep,
    current_user: HRUser,
    service: QuestionService = Depends(get_question_service),
) -> None:
    await service.reorder(session, survey_id, payload)


```

## app/api/responses.py

```python
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends

from app.core.dependencies import EmployeeUser
from app.db.session import AsyncSessionDep
from app.schemas.response import AnswerRead, AnswerUpsert, StartSurveyResponse, SurveyResponseRead
from app.services.response_service import ResponseService, get_response_service

router = APIRouter(tags=["responses"])


@router.post("/employee/surveys/{survey_id}/start", response_model=StartSurveyResponse)
async def start_survey(
    survey_id: UUID,
    session: AsyncSessionDep,
    current_user: EmployeeUser,
    service: ResponseService = Depends(get_response_service),
):
    return await service.start(session, survey_id, current_user)


@router.get("/responses/{response_id}", response_model=SurveyResponseRead)
async def get_response(
    response_id: UUID,
    session: AsyncSessionDep,
    current_user: EmployeeUser,
    service: ResponseService = Depends(get_response_service),
):
    return await service.get(session, response_id, current_user)


@router.post("/responses/{response_id}/answers", response_model=AnswerRead)
async def upsert_answer(
    response_id: UUID,
    payload: AnswerUpsert,
    session: AsyncSessionDep,
    current_user: EmployeeUser,
    service: ResponseService = Depends(get_response_service),
):
    return await service.upsert_answer(session, response_id, payload, current_user)


@router.post("/responses/{response_id}/submit", response_model=SurveyResponseRead)
async def submit_response(
    response_id: UUID,
    session: AsyncSessionDep,
    current_user: EmployeeUser,
    service: ResponseService = Depends(get_response_service),
):
    return await service.submit(session, response_id, current_user)


```

## app/api/router.py

```python
from __future__ import annotations

from fastapi import APIRouter

from app.api import analytics, auth, exports, notifications, questions, responses, survey_logic, surveys, users

api_router = APIRouter()
api_router.include_router(users.router)
api_router.include_router(auth.router)
api_router.include_router(surveys.router)
api_router.include_router(questions.router)
api_router.include_router(survey_logic.router)
api_router.include_router(responses.router)
api_router.include_router(analytics.router)
api_router.include_router(notifications.router)
api_router.include_router(exports.router)

```

## app/api/survey_logic.py

```python
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.core.dependencies import HRUser
from app.db.session import AsyncSessionDep
from app.schemas.survey_logic import SurveyRuleCreate, SurveyRuleRead, SurveyRuleUpdate
from app.services.survey_logic_service import SurveyLogicService, get_survey_logic_service

router = APIRouter(tags=["survey_logic"])


@router.post("/surveys/{survey_id}/rules", response_model=SurveyRuleRead, status_code=status.HTTP_201_CREATED)
async def create_rule(
    survey_id: UUID,
    payload: SurveyRuleCreate,
    session: AsyncSessionDep,
    current_user: HRUser,
    service: SurveyLogicService = Depends(get_survey_logic_service),
):
    return await service.create(session, survey_id, payload)


@router.patch("/rules/{rule_id}", response_model=SurveyRuleRead)
async def update_rule(
    rule_id: UUID,
    payload: SurveyRuleUpdate,
    session: AsyncSessionDep,
    current_user: HRUser,
    service: SurveyLogicService = Depends(get_survey_logic_service),
):
    return await service.update(session, rule_id, payload)


@router.delete("/rules/{rule_id}")
async def delete_rule(
    rule_id: UUID,
    session: AsyncSessionDep,
    current_user: HRUser,
    service: SurveyLogicService = Depends(get_survey_logic_service),
) -> None:
    await service.delete(session, rule_id)


```

## app/api/surveys.py

```python
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.core.dependencies import EmployeeUser, HRUser
from app.db.session import AsyncSessionDep
from app.schemas.survey import (
    EmployeeDashboard,
    EmployeeSurveyCard,
    SurveyAssignmentCreate,
    SurveyAssignmentRead,
    SurveyCreate,
    SurveyDetail,
    SurveyRead,
    SurveyUpdate,
)
from app.services.survey_service import SurveyService, get_survey_service

router = APIRouter(tags=["surveys"])


@router.post("/surveys", response_model=SurveyRead, status_code=status.HTTP_201_CREATED)
async def create_survey(
    payload: SurveyCreate,
    session: AsyncSessionDep,
    current_user: HRUser,
    service: SurveyService = Depends(get_survey_service),
):
    return await service.create(session, payload, current_user)


@router.get("/surveys", response_model=list[SurveyRead])
async def list_surveys(
    session: AsyncSessionDep,
    current_user: HRUser,
    limit: int = 100,
    offset: int = 0,
    service: SurveyService = Depends(get_survey_service),
):
    return await service.list(session, limit=limit, offset=offset)


@router.get("/surveys/{survey_id}", response_model=SurveyDetail)
async def get_survey(
    survey_id: UUID,
    session: AsyncSessionDep,
    current_user: HRUser,
    service: SurveyService = Depends(get_survey_service),
):
    return await service.get(session, survey_id)


@router.patch("/surveys/{survey_id}", response_model=SurveyRead)
async def update_survey(
    survey_id: UUID,
    payload: SurveyUpdate,
    session: AsyncSessionDep,
    current_user: HRUser,
    service: SurveyService = Depends(get_survey_service),
):
    return await service.update(session, survey_id, payload)


@router.post("/surveys/{survey_id}/publish", response_model=SurveyRead)
async def publish_survey(
    survey_id: UUID,
    session: AsyncSessionDep,
    current_user: HRUser,
    service: SurveyService = Depends(get_survey_service),
):
    return await service.publish(session, survey_id)


@router.post("/surveys/{survey_id}/close", response_model=SurveyRead)
async def close_survey(
    survey_id: UUID,
    session: AsyncSessionDep,
    current_user: HRUser,
    service: SurveyService = Depends(get_survey_service),
):
    return await service.close(session, survey_id)


@router.post("/surveys/{survey_id}/archive", response_model=SurveyRead)
async def archive_survey(
    survey_id: UUID,
    session: AsyncSessionDep,
    current_user: HRUser,
    service: SurveyService = Depends(get_survey_service),
):
    return await service.archive(session, survey_id)


@router.post("/surveys/{survey_id}/assignments", response_model=list[SurveyAssignmentRead])
async def assign_survey(
    survey_id: UUID,
    payload: SurveyAssignmentCreate,
    session: AsyncSessionDep,
    current_user: HRUser,
    service: SurveyService = Depends(get_survey_service),
):
    return await service.assign(session, survey_id, payload)


@router.get("/employee/dashboard", response_model=EmployeeDashboard)
async def employee_dashboard(
    session: AsyncSessionDep,
    current_user: EmployeeUser,
    service: SurveyService = Depends(get_survey_service),
):
    return await service.employee_dashboard(session, current_user)


@router.get("/employee/surveys", response_model=list[EmployeeSurveyCard])
async def employee_surveys(
    session: AsyncSessionDep,
    current_user: EmployeeUser,
    service: SurveyService = Depends(get_survey_service),
):
    return await service.employee_surveys(session, current_user)


@router.get("/employee/surveys/{survey_id}", response_model=SurveyDetail)
async def employee_survey_detail(
    survey_id: UUID,
    session: AsyncSessionDep,
    current_user: EmployeeUser,
    service: SurveyService = Depends(get_survey_service),
):
    return await service.get(session, survey_id)


```

## app/api/users.py

```python
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.db.session import AsyncSessionDep
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.services.user_service import UserService, get_user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    session: AsyncSessionDep,
    service: UserService = Depends(get_user_service),
) -> UserRead:
    return await service.create(session, payload)


@router.get("", response_model=list[UserRead])
async def list_users(
    session: AsyncSessionDep,
    limit: int = 100,
    offset: int = 0,
    service: UserService = Depends(get_user_service),
) -> list[UserRead]:
    return await service.list(session, limit=limit, offset=offset)


@router.get("/{user_id}", response_model=UserRead)
async def get_user(
    user_id: UUID,
    session: AsyncSessionDep,
    service: UserService = Depends(get_user_service),
) -> UserRead:
    return await service.get(session, user_id)


@router.patch("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: UUID,
    payload: UserUpdate,
    session: AsyncSessionDep,
    service: UserService = Depends(get_user_service),
) -> UserRead:
    return await service.update(session, user_id, payload)


@router.delete("/{user_id}")
async def delete_user(
    user_id: UUID,
    session: AsyncSessionDep,
    service: UserService = Depends(get_user_service),
) -> None:
    await service.delete(session, user_id)


```

## app/core/__init__.py

```python


```

## app/core/config.py

```python
from __future__ import annotations

from functools import cached_property

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "PulseHR"
    app_env: str = "local"
    debug: bool = False
    api_prefix: str = ""

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "pulsehr"
    postgres_user: str = "pulsehr"
    postgres_password: str = "pulsehr_password"

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    jwt_secret_key: str = Field(min_length=16)
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 30

    otp_ttl_seconds: int = 300
    otp_rate_limit_seconds: int = 60
    otp_max_verify_attempts: int = 5

    @cached_property
    def database_url(self) -> str:
        return (
            "postgresql+asyncpg://"
            f"{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @cached_property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"


settings = Settings()

```

## app/core/dependencies.py

```python
from __future__ import annotations

from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import decode_jwt_token
from app.db.session import AsyncSessionDep
from app.models.user import Role, User
from app.repositories.user_repository import UserRepository

bearer_scheme = HTTPBearer(auto_error=True)


async def get_current_user(
    session: AsyncSessionDep,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> User:
    try:
        payload = decode_jwt_token(credentials.credentials)
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token") from exc

    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    subject = payload.get("sub")
    if not isinstance(subject, str):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token")

    user = await UserRepository().get_by_id(session, UUID(subject))
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive or missing user")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def require_hr(current_user: CurrentUser) -> User:
    if current_user.role != Role.HR:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="HR role required")
    return current_user


async def require_employee(current_user: CurrentUser) -> User:
    return current_user


HRUser = Annotated[User, Depends(require_hr)]
EmployeeUser = Annotated[User, Depends(require_employee)]


```

## app/core/security.py

```python
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt

from app.core.config import settings


def utcnow() -> datetime:
    return datetime.now(UTC)


def create_jwt_token(
    *,
    subject: UUID,
    token_type: str,
    expires_delta: timedelta,
    jti: str | None = None,
) -> tuple[str, datetime]:
    expires_at = utcnow() + expires_delta
    payload: dict[str, str | int] = {
        "sub": str(subject),
        "type": token_type,
        "exp": int(expires_at.timestamp()),
        "iat": int(utcnow().timestamp()),
    }
    if jti is not None:
        payload["jti"] = jti

    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, expires_at


def decode_jwt_token(token: str) -> dict[str, str | int]:
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])


```

## app/db/__init__.py

```python


```

## app/db/base.py

```python
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


```

## app/db/redis.py

```python
from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from redis.asyncio import Redis

from app.core.config import settings

_redis: Redis | None = None


async def get_redis_client() -> Redis:
    global _redis
    if _redis is None:
        _redis = Redis.from_url(settings.redis_url, decode_responses=True)
    return _redis


async def get_redis() -> AsyncIterator[Redis]:
    yield await get_redis_client()


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None


RedisDep = Annotated[Redis, Depends(get_redis)]


```

## app/db/session.py

```python
from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

engine = create_async_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
    autoflush=False,
)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        yield session


AsyncSessionDep = Annotated[AsyncSession, Depends(get_session)]


```

## app/main.py

```python
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import settings
from app.db.redis import close_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await close_redis()


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,
)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(api_router, prefix=settings.api_prefix)


```

## app/models/__init__.py

```python
from app.models.export import ExportFormat, ExportJob, ExportStatus
from app.models.auth import RefreshToken
from app.models.notification import (
    DeliveryStatus,
    Notification,
    NotificationChannel,
    NotificationDelivery,
    NotificationSettings,
    NotificationSubscription,
)
from app.models.question import Question, QuestionOption, QuestionType
from app.models.response import Answer, ResponseStatus, SurveyResponse
from app.models.survey import AssignmentStatus, Survey, SurveyAssignment, SurveyStatus
from app.models.survey_logic import RuleAction, SurveyRule
from app.models.user import Role, User

__all__ = [
    "Answer",
    "AssignmentStatus",
    "DeliveryStatus",
    "ExportFormat",
    "ExportJob",
    "ExportStatus",
    "Notification",
    "NotificationChannel",
    "NotificationDelivery",
    "NotificationSettings",
    "NotificationSubscription",
    "Question",
    "QuestionOption",
    "QuestionType",
    "RefreshToken",
    "ResponseStatus",
    "Role",
    "RuleAction",
    "Survey",
    "SurveyAssignment",
    "SurveyResponse",
    "SurveyRule",
    "SurveyStatus",
    "User",
]

```

## app/models/auth.py

```python
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    jti: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user = relationship("User", back_populates="refresh_tokens")


```

## app/models/export.py

```python
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class ExportFormat(str, enum.Enum):
    CSV = "CSV"
    XLSX = "XLSX"


class ExportStatus(str, enum.Enum):
    PENDING = "PENDING"
    READY = "READY"
    FAILED = "FAILED"


class ExportJob(TimestampMixin, Base):
    __tablename__ = "export_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    survey_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("surveys.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    requested_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    format: Mapped[ExportFormat] = mapped_column(Enum(ExportFormat, name="export_format"), nullable=False)
    status: Mapped[ExportStatus] = mapped_column(
        Enum(ExportStatus, name="export_status"),
        default=ExportStatus.PENDING,
        nullable=False,
    )
    file_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    survey = relationship("Survey")
    requested_by = relationship("User")


```

## app/models/notification.py

```python
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class NotificationChannel(str, enum.Enum):
    PUSH = "PUSH"
    TELEGRAM = "TELEGRAM"
    EMAIL = "EMAIL"
    SMS = "SMS"


class DeliveryStatus(str, enum.Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"


class NotificationSettings(TimestampMixin, Base):
    __tablename__ = "notification_settings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    push_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    telegram_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    email_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sms_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    telegram_chat_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    user = relationship("User", back_populates="notification_settings")


class NotificationSubscription(TimestampMixin, Base):
    __tablename__ = "notification_subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    channel: Mapped[NotificationChannel] = mapped_column(
        Enum(NotificationChannel, name="notification_channel"),
        nullable=False,
    )
    device_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    destination: Mapped[str] = mapped_column(String(512), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    user = relationship("User")


class Notification(TimestampMixin, Base):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    survey_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("surveys.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    deliveries = relationship("NotificationDelivery", back_populates="notification")


class NotificationDelivery(TimestampMixin, Base):
    __tablename__ = "notification_deliveries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    notification_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("notifications.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    channel: Mapped[NotificationChannel] = mapped_column(
        Enum(NotificationChannel, name="notification_channel", create_type=False),
        nullable=False,
    )
    status: Mapped[DeliveryStatus] = mapped_column(
        Enum(DeliveryStatus, name="delivery_status"),
        default=DeliveryStatus.PENDING,
        nullable=False,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    notification = relationship("Notification", back_populates="deliveries")
    user = relationship("User")


```

## app/models/question.py

```python
from __future__ import annotations

import enum
import uuid

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class QuestionType(str, enum.Enum):
    SINGLE_CHOICE = "SINGLE_CHOICE"
    MULTIPLE_CHOICE = "MULTIPLE_CHOICE"
    RATING = "RATING"
    TEXT = "TEXT"
    MATRIX = "MATRIX"


class Question(TimestampMixin, Base):
    __tablename__ = "questions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    survey_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("surveys.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    type: Mapped[QuestionType] = mapped_column(Enum(QuestionType, name="question_type"), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    settings: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    survey = relationship("Survey", back_populates="questions")
    options = relationship(
        "QuestionOption",
        back_populates="question",
        cascade="all, delete-orphan",
        order_by="QuestionOption.position",
    )
    answers = relationship("Answer", back_populates="question")


class QuestionOption(TimestampMixin, Base):
    __tablename__ = "question_options"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("questions.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    value: Mapped[str] = mapped_column(String(255), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)

    question = relationship("Question", back_populates="options")


```

## app/models/response.py

```python
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class ResponseStatus(str, enum.Enum):
    IN_PROGRESS = "IN_PROGRESS"
    SUBMITTED = "SUBMITTED"


class SurveyResponse(TimestampMixin, Base):
    __tablename__ = "survey_responses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    survey_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("surveys.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    anonymous_session_id: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    status: Mapped[ResponseStatus] = mapped_column(
        Enum(ResponseStatus, name="response_status"),
        default=ResponseStatus.IN_PROGRESS,
        nullable=False,
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    survey = relationship("Survey", back_populates="responses")
    user = relationship("User", back_populates="survey_responses")
    answers = relationship("Answer", back_populates="response", cascade="all, delete-orphan")


class Answer(TimestampMixin, Base):
    __tablename__ = "answers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    response_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("survey_responses.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("questions.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    value: Mapped[dict] = mapped_column(JSONB, nullable=False)

    response = relationship("SurveyResponse", back_populates="answers")
    question = relationship("Question", back_populates="answers")


```

## app/models/survey.py

```python
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class SurveyStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    CLOSED = "CLOSED"
    ARCHIVED = "ARCHIVED"


class AssignmentStatus(str, enum.Enum):
    PENDING = "PENDING"
    STARTED = "STARTED"
    SUBMITTED = "SUBMITTED"


class Survey(TimestampMixin, Base):
    __tablename__ = "surveys"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[SurveyStatus] = mapped_column(
        Enum(SurveyStatus, name="survey_status"),
        default=SurveyStatus.DRAFT,
        nullable=False,
    )
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    estimated_minutes: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    created_by = relationship("User", back_populates="created_surveys")
    questions = relationship(
        "Question",
        back_populates="survey",
        cascade="all, delete-orphan",
        order_by="Question.position",
    )
    rules = relationship(
        "SurveyRule",
        back_populates="survey",
        cascade="all, delete-orphan",
        order_by="SurveyRule.priority",
    )
    assignments = relationship("SurveyAssignment", back_populates="survey", cascade="all, delete-orphan")
    responses = relationship("SurveyResponse", back_populates="survey", cascade="all, delete-orphan")


class SurveyAssignment(TimestampMixin, Base):
    __tablename__ = "survey_assignments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    survey_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("surveys.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    status: Mapped[AssignmentStatus] = mapped_column(
        Enum(AssignmentStatus, name="assignment_status"),
        default=AssignmentStatus.PENDING,
        nullable=False,
    )
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    survey = relationship("Survey", back_populates="assignments")
    user = relationship("User", back_populates="survey_assignments")

```

## app/models/survey_logic.py

```python
from __future__ import annotations

import enum
import uuid

from sqlalchemy import Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class RuleAction(str, enum.Enum):
    SHOW_QUESTION = "SHOW_QUESTION"
    HIDE_QUESTION = "HIDE_QUESTION"


class SurveyRule(TimestampMixin, Base):
    __tablename__ = "survey_rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    survey_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("surveys.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    target_question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("questions.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    action: Mapped[RuleAction] = mapped_column(Enum(RuleAction, name="rule_action"), nullable=False)
    condition: Mapped[dict] = mapped_column(JSONB, nullable=False)

    survey = relationship("Survey", back_populates="rules")
    target_question = relationship("Question")

```

## app/models/user.py

```python
from __future__ import annotations

import enum
import uuid

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Role(str, enum.Enum):
    HR = "HR"
    EMPLOYEE = "EMPLOYEE"


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[Role] = mapped_column(Enum(Role, name="role"), default=Role.EMPLOYEE, nullable=False)
    department: Mapped[str | None] = mapped_column(String(255), nullable=True)
    position: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    refresh_tokens = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    created_surveys = relationship("Survey", back_populates="created_by")
    survey_assignments = relationship("SurveyAssignment", back_populates="user")
    survey_responses = relationship("SurveyResponse", back_populates="user")
    notification_settings = relationship("NotificationSettings", back_populates="user", uselist=False)

```

## app/repositories/__init__.py

```python


```

## app/repositories/auth_repository.py

```python
from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth import RefreshToken


class RefreshTokenRepository:
    async def create(
        self,
        session: AsyncSession,
        *,
        user_id,
        jti: str,
        expires_at: datetime,
        created_at: datetime,
    ) -> RefreshToken:
        refresh_token = RefreshToken(
            user_id=user_id,
            jti=jti,
            expires_at=expires_at,
            created_at=created_at,
        )
        session.add(refresh_token)
        await session.flush()
        return refresh_token

    async def get_active_by_jti(self, session: AsyncSession, jti: str) -> RefreshToken | None:
        result = await session.execute(
            select(RefreshToken).where(
                RefreshToken.jti == jti,
                RefreshToken.revoked_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def revoke(self, session: AsyncSession, refresh_token: RefreshToken, revoked_at: datetime) -> None:
        refresh_token.revoked_at = revoked_at
        await session.flush()


```

## app/repositories/notification_repository.py

```python
from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import (
    Notification,
    NotificationDelivery,
    NotificationSettings,
    NotificationSubscription,
)


class NotificationRepository:
    async def get_settings(self, session: AsyncSession, user_id: UUID) -> NotificationSettings | None:
        result = await session.execute(select(NotificationSettings).where(NotificationSettings.user_id == user_id))
        return result.scalar_one_or_none()

    async def list_subscriptions(self, session: AsyncSession, user_id: UUID) -> list[NotificationSubscription]:
        result = await session.execute(
            select(NotificationSubscription)
            .where(NotificationSubscription.user_id == user_id)
            .order_by(NotificationSubscription.created_at.desc())
        )
        return list(result.scalars().all())

    async def create_notification(self, session: AsyncSession, notification: Notification) -> Notification:
        session.add(notification)
        await session.flush()
        await session.refresh(notification)
        return notification

    async def create_delivery(self, session: AsyncSession, delivery: NotificationDelivery) -> NotificationDelivery:
        session.add(delivery)
        await session.flush()
        return delivery


```

## app/repositories/response_repository.py

```python
from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.response import Answer, SurveyResponse


class ResponseRepository:
    async def get(self, session: AsyncSession, response_id: UUID) -> SurveyResponse | None:
        result = await session.execute(
            select(SurveyResponse)
            .where(SurveyResponse.id == response_id)
            .options(selectinload(SurveyResponse.answers), selectinload(SurveyResponse.survey))
        )
        return result.scalar_one_or_none()

    async def create(self, session: AsyncSession, response: SurveyResponse) -> SurveyResponse:
        session.add(response)
        await session.flush()
        await session.refresh(response)
        return response

    async def get_answer(
        self,
        session: AsyncSession,
        response_id: UUID,
        question_id: UUID,
    ) -> Answer | None:
        result = await session.execute(
            select(Answer).where(Answer.response_id == response_id, Answer.question_id == question_id)
        )
        return result.scalar_one_or_none()

    async def upsert_answer(
        self,
        session: AsyncSession,
        *,
        response_id: UUID,
        question_id: UUID,
        value: dict,
    ) -> Answer:
        answer = await self.get_answer(session, response_id, question_id)
        if answer is None:
            answer = Answer(response_id=response_id, question_id=question_id, value=value)
            session.add(answer)
        else:
            answer.value = value
        await session.flush()
        await session.refresh(answer)
        return answer


```

## app/repositories/survey_repository.py

```python
from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select, exists, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.question import Question, QuestionOption
from app.models.survey import Survey, SurveyAssignment, SurveyStatus
from app.models.survey_logic import SurveyRule


class SurveyRepository:
    async def create(self, session: AsyncSession, survey: Survey) -> Survey:
        session.add(survey)
        await session.flush()
        await session.refresh(survey)
        return survey

    async def get(self, session: AsyncSession, survey_id: UUID, *, with_details: bool = False) -> Survey | None:
        stmt: Select = select(Survey).where(Survey.id == survey_id)
        if with_details:
            stmt = stmt.options(
                selectinload(Survey.questions).selectinload(Question.options),
                selectinload(Survey.rules),
                selectinload(Survey.responses),
            )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(self, session: AsyncSession, *, limit: int, offset: int) -> list[Survey]:
        result = await session.execute(
            select(Survey).order_by(Survey.created_at.desc()).limit(limit).offset(offset)
        )
        return list(result.scalars().all())

    async def list_published_for_user(self, session: AsyncSession, user_id: UUID) -> list[Survey]:
        assigned_to_user = exists().where(
            SurveyAssignment.survey_id == Survey.id,
            SurveyAssignment.user_id == user_id,
        )
        has_assignments = exists().where(SurveyAssignment.survey_id == Survey.id)
        result = await session.execute(
            select(Survey)
            .where(
                Survey.status == SurveyStatus.PUBLISHED,
                or_(assigned_to_user, ~has_assignments),
            )
            .options(selectinload(Survey.assignments), selectinload(Survey.questions))
            .order_by(Survey.created_at.desc())
        )
        return list(result.scalars().unique().all())

    async def list_rules(self, session: AsyncSession, survey_id: UUID) -> list[SurveyRule]:
        result = await session.execute(
            select(SurveyRule).where(SurveyRule.survey_id == survey_id).order_by(SurveyRule.priority.asc())
        )
        return list(result.scalars().all())


class QuestionRepository:
    async def get(self, session: AsyncSession, question_id: UUID) -> Question | None:
        result = await session.execute(
            select(Question).where(Question.id == question_id).options(selectinload(Question.options))
        )
        return result.scalar_one_or_none()

    async def create(self, session: AsyncSession, question: Question) -> Question:
        session.add(question)
        await session.flush()
        await session.refresh(question)
        return question

    async def replace_options(
        self,
        session: AsyncSession,
        question: Question,
        options: list[QuestionOption],
    ) -> None:
        question.options.clear()
        await session.flush()
        question.options.extend(options)


class SurveyRuleRepository:
    async def get(self, session: AsyncSession, rule_id: UUID) -> SurveyRule | None:
        return await session.get(SurveyRule, rule_id)

    async def create(self, session: AsyncSession, rule: SurveyRule) -> SurveyRule:
        session.add(rule)
        await session.flush()
        await session.refresh(rule)
        return rule

```

## app/repositories/user_repository.py

```python
from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class UserRepository:
    async def create(self, session: AsyncSession, payload: UserCreate) -> User:
        user = User(**payload.model_dump())
        session.add(user)
        await session.flush()
        await session.refresh(user)
        return user

    async def get_by_id(self, session: AsyncSession, user_id: UUID) -> User | None:
        return await session.get(User, user_id)

    async def get_by_phone(self, session: AsyncSession, phone: str) -> User | None:
        result = await session.execute(select(User).where(User.phone == phone))
        return result.scalar_one_or_none()

    async def list(self, session: AsyncSession, *, limit: int, offset: int) -> list[User]:
        result = await session.execute(
            select(User).order_by(User.created_at.desc()).limit(limit).offset(offset)
        )
        return list(result.scalars().all())

    async def update(self, session: AsyncSession, user: User, payload: UserUpdate) -> User:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(user, field, value)
        await session.flush()
        await session.refresh(user)
        return user

    async def delete(self, session: AsyncSession, user: User) -> None:
        await session.delete(user)
        await session.flush()


```

## app/schemas/__init__.py

```python


```

## app/schemas/analytics.py

```python
from __future__ import annotations

from datetime import date
from uuid import UUID

from pydantic import BaseModel


class MetricPoint(BaseModel):
    label: str
    value: float


class TimelinePoint(BaseModel):
    date: date
    responses: int


class AnalyticsOverview(BaseModel):
    active_surveys: int
    completion_rate: float
    response_rate: float
    enps: float | None
    latest_responses: list[dict]
    notification_efficiency: dict


class SurveyAnalytics(BaseModel):
    survey_id: UUID
    completion_rate: float
    response_rate: float
    enps: float | None
    department_analytics: list[MetricPoint]
    timeline: list[TimelinePoint]


```

## app/schemas/auth.py

```python
from __future__ import annotations

from pydantic import BaseModel, Field


class SendCodeRequest(BaseModel):
    phone: str = Field(min_length=5, max_length=32, examples=["+79991234567"])


class SendCodeResponse(BaseModel):
    message: str
    expires_in_seconds: int


class VerifyCodeRequest(BaseModel):
    phone: str = Field(min_length=5, max_length=32)
    code: str = Field(pattern=r"^\d{6}$", examples=["123456"])


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


```

## app/schemas/export.py

```python
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.export import ExportFormat, ExportStatus


class ExportCreate(BaseModel):
    format: ExportFormat


class ExportJobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    survey_id: UUID
    requested_by_id: UUID
    format: ExportFormat
    status: ExportStatus
    file_path: str | None
    error_message: str | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime


```

## app/schemas/notification.py

```python
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.notification import DeliveryStatus, NotificationChannel


class NotificationSettingsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    push_enabled: bool
    telegram_enabled: bool
    email_enabled: bool
    sms_enabled: bool
    telegram_chat_id: str | None
    email: str | None
    created_at: datetime
    updated_at: datetime


class NotificationSettingsUpdate(BaseModel):
    push_enabled: bool | None = None
    telegram_enabled: bool | None = None
    email_enabled: bool | None = None
    sms_enabled: bool | None = None
    telegram_chat_id: str | None = Field(default=None, max_length=128)
    email: str | None = Field(default=None, max_length=255)


class NotificationSubscriptionCreate(BaseModel):
    channel: NotificationChannel
    device_name: str | None = Field(default=None, max_length=255)
    destination: str = Field(min_length=1, max_length=512)


class NotificationSubscriptionRead(NotificationSubscriptionCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime


class NotificationCreate(BaseModel):
    survey_id: UUID | None = None
    title: str = Field(min_length=1, max_length=255)
    body: str = Field(min_length=1)
    user_ids: list[UUID]
    channels: list[NotificationChannel]
    payload: dict = Field(default_factory=dict)


class NotificationDeliveryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    notification_id: UUID
    user_id: UUID
    channel: NotificationChannel
    status: DeliveryStatus
    error_message: str | None
    sent_at: datetime | None
    created_at: datetime
    updated_at: datetime

```

## app/schemas/question.py

```python
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.question import QuestionType


class QuestionOptionCreate(BaseModel):
    label: str = Field(min_length=1, max_length=255)
    value: str = Field(min_length=1, max_length=255)
    position: int = Field(ge=0)


class QuestionOptionRead(QuestionOptionCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime


class QuestionCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    description: str | None = None
    type: QuestionType
    position: int = Field(ge=0)
    is_required: bool = True
    settings: dict = Field(default_factory=dict)
    options: list[QuestionOptionCreate] = Field(default_factory=list)


class QuestionUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    description: str | None = None
    type: QuestionType | None = None
    position: int | None = Field(default=None, ge=0)
    is_required: bool | None = None
    settings: dict | None = None
    options: list[QuestionOptionCreate] | None = None


class QuestionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    survey_id: UUID
    title: str
    description: str | None
    type: QuestionType
    position: int
    is_required: bool
    settings: dict
    options: list[QuestionOptionRead] = []
    created_at: datetime
    updated_at: datetime


class QuestionReorderItem(BaseModel):
    id: UUID
    position: int = Field(ge=0)


class QuestionReorderRequest(BaseModel):
    items: list[QuestionReorderItem]


```

## app/schemas/response.py

```python
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.response import ResponseStatus


class StartSurveyResponse(BaseModel):
    response_id: UUID
    survey_id: UUID
    is_anonymous: bool
    anonymous_session_id: str | None
    warning: str


class AnswerUpsert(BaseModel):
    question_id: UUID
    value: dict


class AnswerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    response_id: UUID
    question_id: UUID
    value: dict
    created_at: datetime
    updated_at: datetime


class SurveyResponseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    survey_id: UUID
    user_id: UUID | None
    anonymous_session_id: str | None
    status: ResponseStatus
    started_at: datetime
    submitted_at: datetime | None
    answers: list[AnswerRead] = []


```

## app/schemas/survey.py

```python
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.survey import AssignmentStatus, SurveyStatus
from app.schemas.question import QuestionRead
from app.schemas.survey_logic import SurveyRuleRead


class SurveyCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    is_anonymous: bool = False
    estimated_minutes: int = Field(default=5, ge=1, le=240)
    starts_at: datetime | None = None
    ends_at: datetime | None = None


class SurveyUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    is_anonymous: bool | None = None
    estimated_minutes: int | None = Field(default=None, ge=1, le=240)
    starts_at: datetime | None = None
    ends_at: datetime | None = None


class SurveyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str | None
    status: SurveyStatus
    is_anonymous: bool
    estimated_minutes: int
    starts_at: datetime | None
    ends_at: datetime | None
    created_by_id: UUID
    created_at: datetime
    updated_at: datetime


class SurveyDetail(SurveyRead):
    questions: list[QuestionRead] = []
    rules: list[SurveyRuleRead] = []


class SurveyAssignmentCreate(BaseModel):
    user_ids: list[UUID] = Field(min_length=1)


class SurveyAssignmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    survey_id: UUID
    user_id: UUID
    status: AssignmentStatus
    submitted_at: datetime | None
    created_at: datetime
    updated_at: datetime


class EmployeeSurveyCard(BaseModel):
    id: UUID
    title: str
    description: str | None
    status: SurveyStatus
    assignment_status: AssignmentStatus | None = None
    is_anonymous: bool
    anonymity_notice: str
    ends_at: datetime | None
    estimated_minutes: int
    completion_percent: int


class EmployeeDashboard(BaseModel):
    active_surveys: int
    completed_surveys: int
    completion_percent: int
    surveys: list[EmployeeSurveyCard]


```

## app/schemas/survey_logic.py

```python
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.survey_logic import RuleAction


class SurveyRuleCreate(BaseModel):
    target_question_id: UUID
    name: str = Field(min_length=1, max_length=255)
    priority: int = Field(default=100, ge=0)
    action: RuleAction
    condition: dict


class SurveyRuleUpdate(BaseModel):
    target_question_id: UUID | None = None
    name: str | None = Field(default=None, min_length=1, max_length=255)
    priority: int | None = Field(default=None, ge=0)
    action: RuleAction | None = None
    condition: dict | None = None


class SurveyRuleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    survey_id: UUID
    target_question_id: UUID
    name: str
    priority: int
    action: RuleAction
    condition: dict
    created_at: datetime
    updated_at: datetime


```

## app/schemas/user.py

```python
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.user import Role


class UserBase(BaseModel):
    phone: str = Field(min_length=5, max_length=32, examples=["+79991234567"])
    full_name: str | None = Field(default=None, max_length=255, examples=["Ivan Petrov"])
    role: Role = Role.EMPLOYEE
    department: str | None = Field(default=None, max_length=255, examples=["Engineering"])
    position: str | None = Field(default=None, max_length=255, examples=["Team Lead"])
    is_active: bool = True


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    phone: str | None = Field(default=None, min_length=5, max_length=32)
    full_name: str | None = Field(default=None, max_length=255)
    role: Role | None = None
    department: str | None = Field(default=None, max_length=255)
    position: str | None = Field(default=None, max_length=255)
    is_active: bool | None = None


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime

```

## app/services/__init__.py

```python


```

## app/services/analytics_service.py

```python
from __future__ import annotations

from collections import Counter, defaultdict
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import DeliveryStatus, NotificationDelivery
from app.models.question import Question
from app.models.response import Answer, ResponseStatus, SurveyResponse
from app.models.survey import AssignmentStatus, Survey, SurveyAssignment, SurveyStatus
from app.models.user import User


class AnalyticsService:
    async def overview(self, session: AsyncSession) -> dict:
        active_surveys = await session.scalar(
            select(func.count()).select_from(Survey).where(Survey.status == SurveyStatus.PUBLISHED)
        )
        completion_rate = await self._global_completion_rate(session)
        response_rate = await self._global_response_rate(session)
        enps = await self._enps(session)
        latest = await self._latest_responses(session)
        notification_efficiency = await self.notification_efficiency(session)
        return {
            "active_surveys": active_surveys or 0,
            "completion_rate": completion_rate,
            "response_rate": response_rate,
            "enps": enps,
            "latest_responses": latest,
            "notification_efficiency": notification_efficiency,
        }

    async def survey(self, session: AsyncSession, survey_id: UUID) -> dict:
        return {
            "survey_id": survey_id,
            "completion_rate": await self._survey_completion_rate(session, survey_id),
            "response_rate": await self._survey_response_rate(session, survey_id),
            "enps": await self._enps(session, survey_id),
            "department_analytics": await self.department_analytics(session, survey_id),
            "timeline": await self.timeline(session, survey_id),
        }

    async def department_analytics(self, session: AsyncSession, survey_id: UUID) -> list[dict]:
        result = await session.execute(
            select(User.department, func.count(SurveyResponse.id))
            .join(SurveyResponse, SurveyResponse.user_id == User.id)
            .where(SurveyResponse.survey_id == survey_id, SurveyResponse.status == ResponseStatus.SUBMITTED)
            .group_by(User.department)
        )
        return [{"label": department or "Unknown", "value": float(count)} for department, count in result.all()]

    async def timeline(self, session: AsyncSession, survey_id: UUID) -> list[dict]:
        result = await session.execute(
            select(func.date(SurveyResponse.submitted_at), func.count(SurveyResponse.id))
            .where(SurveyResponse.survey_id == survey_id, SurveyResponse.status == ResponseStatus.SUBMITTED)
            .group_by(func.date(SurveyResponse.submitted_at))
            .order_by(func.date(SurveyResponse.submitted_at))
        )
        return [{"date": day, "responses": count} for day, count in result.all()]

    async def notification_efficiency(self, session: AsyncSession) -> dict:
        result = await session.execute(
            select(NotificationDelivery.channel, NotificationDelivery.status, func.count(NotificationDelivery.id))
            .group_by(NotificationDelivery.channel, NotificationDelivery.status)
        )
        data: dict[str, Counter] = defaultdict(Counter)
        for channel, delivery_status, count in result.all():
            data[channel.value][delivery_status.value] = count
        return {
            channel: {
                "sent": counts[DeliveryStatus.SENT.value],
                "failed": counts[DeliveryStatus.FAILED.value],
                "pending": counts[DeliveryStatus.PENDING.value],
            }
            for channel, counts in data.items()
        }

    async def _global_completion_rate(self, session: AsyncSession) -> float:
        total = await session.scalar(select(func.count()).select_from(SurveyAssignment))
        submitted = await session.scalar(
            select(func.count()).select_from(SurveyAssignment).where(SurveyAssignment.status == AssignmentStatus.SUBMITTED)
        )
        return round(((submitted or 0) / total) * 100, 2) if total else 0.0

    async def _global_response_rate(self, session: AsyncSession) -> float:
        total = await session.scalar(select(func.count()).select_from(SurveyResponse))
        submitted = await session.scalar(
            select(func.count()).select_from(SurveyResponse).where(SurveyResponse.status == ResponseStatus.SUBMITTED)
        )
        return round(((submitted or 0) / total) * 100, 2) if total else 0.0

    async def _survey_completion_rate(self, session: AsyncSession, survey_id: UUID) -> float:
        total = await session.scalar(
            select(func.count()).select_from(SurveyAssignment).where(SurveyAssignment.survey_id == survey_id)
        )
        submitted = await session.scalar(
            select(func.count())
            .select_from(SurveyAssignment)
            .where(SurveyAssignment.survey_id == survey_id, SurveyAssignment.status == AssignmentStatus.SUBMITTED)
        )
        return round(((submitted or 0) / total) * 100, 2) if total else 0.0

    async def _survey_response_rate(self, session: AsyncSession, survey_id: UUID) -> float:
        total = await session.scalar(
            select(func.count()).select_from(SurveyResponse).where(SurveyResponse.survey_id == survey_id)
        )
        submitted = await session.scalar(
            select(func.count())
            .select_from(SurveyResponse)
            .where(SurveyResponse.survey_id == survey_id, SurveyResponse.status == ResponseStatus.SUBMITTED)
        )
        return round(((submitted or 0) / total) * 100, 2) if total else 0.0

    async def _enps(self, session: AsyncSession, survey_id: UUID | None = None) -> float | None:
        stmt = (
            select(Answer.value)
            .join(Question, Question.id == Answer.question_id)
            .join(SurveyResponse, SurveyResponse.id == Answer.response_id)
            .where(Question.settings["enps"].as_boolean().is_(True), SurveyResponse.status == ResponseStatus.SUBMITTED)
        )
        if survey_id is not None:
            stmt = stmt.where(SurveyResponse.survey_id == survey_id)
        result = await session.execute(stmt)
        scores = []
        for (value,) in result.all():
            score = value.get("score") if isinstance(value, dict) else None
            if isinstance(score, (int, float)):
                scores.append(score)
        if not scores:
            return None
        promoters = sum(1 for score in scores if score >= 9)
        detractors = sum(1 for score in scores if score <= 6)
        return round(((promoters - detractors) / len(scores)) * 100, 2)

    async def _latest_responses(self, session: AsyncSession) -> list[dict]:
        result = await session.execute(
            select(SurveyResponse, Survey.title)
            .join(Survey, Survey.id == SurveyResponse.survey_id)
            .where(SurveyResponse.status == ResponseStatus.SUBMITTED)
            .order_by(SurveyResponse.submitted_at.desc())
            .limit(10)
        )
        return [
            {
                "response_id": response.id,
                "survey_id": response.survey_id,
                "survey_title": title,
                "submitted_at": response.submitted_at,
                "anonymous": response.user_id is None,
            }
            for response, title in result.all()
        ]


def get_analytics_service() -> AnalyticsService:
    return AnalyticsService()

```

## app/services/auth_service.py

```python
from __future__ import annotations

import logging
import secrets
from datetime import timedelta
from uuid import UUID

import jwt
from fastapi import HTTPException, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_jwt_token, decode_jwt_token, utcnow
from app.models.user import Role
from app.repositories.auth_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import SendCodeRequest, SendCodeResponse, TokenPair, VerifyCodeRequest
from app.schemas.user import UserCreate

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(
        self,
        user_repository: UserRepository,
        refresh_token_repository: RefreshTokenRepository,
    ) -> None:
        self.user_repository = user_repository
        self.refresh_token_repository = refresh_token_repository

    async def send_code(self, redis: Redis, payload: SendCodeRequest) -> SendCodeResponse:
        rate_key = self._rate_key(payload.phone)
        allowed = await redis.set(rate_key, "1", ex=settings.otp_rate_limit_seconds, nx=True)
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="OTP was requested too recently",
            )

        code = f"{secrets.randbelow(1_000_000):06d}"
        await redis.set(self._code_key(payload.phone), code, ex=settings.otp_ttl_seconds)
        await redis.delete(self._attempts_key(payload.phone))

        logger.info("PulseHR OTP code for %s: %s", payload.phone, code)
        print(f"PulseHR OTP code for {payload.phone}: {code}", flush=True)

        return SendCodeResponse(
            message="OTP code generated",
            expires_in_seconds=settings.otp_ttl_seconds,
        )

    async def verify_code(
        self,
        session: AsyncSession,
        redis: Redis,
        payload: VerifyCodeRequest,
    ) -> TokenPair:
        stored_code = await redis.get(self._code_key(payload.phone))
        if stored_code is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OTP expired or not found")

        attempts_key = self._attempts_key(payload.phone)
        attempts = await redis.incr(attempts_key)
        if attempts == 1:
            await redis.expire(attempts_key, settings.otp_ttl_seconds)
        if attempts > settings.otp_max_verify_attempts:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many OTP verification attempts",
            )

        if payload.code != stored_code:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP code")

        await redis.delete(self._code_key(payload.phone), attempts_key, self._rate_key(payload.phone))

        user = await self.user_repository.get_by_phone(session, payload.phone)
        if user is None:
            user = await self.user_repository.create(
                session,
                UserCreate(phone=payload.phone, role=Role.EMPLOYEE),
            )

        token_pair = await self._issue_token_pair(session, user.id)
        await session.commit()
        return token_pair

    async def refresh(self, session: AsyncSession, refresh_token: str) -> TokenPair:
        try:
            payload = decode_jwt_token(refresh_token)
        except jwt.PyJWTError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token") from exc

        if payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

        jti = payload.get("jti")
        subject = payload.get("sub")
        if not isinstance(jti, str) or not isinstance(subject, str):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

        persisted_token = await self.refresh_token_repository.get_active_by_jti(session, jti)
        if persisted_token is None or persisted_token.expires_at <= utcnow():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token is inactive")

        await self.refresh_token_repository.revoke(session, persisted_token, utcnow())
        token_pair = await self._issue_token_pair(session, UUID(subject))
        await session.commit()
        return token_pair

    async def _issue_token_pair(self, session: AsyncSession, user_id: UUID) -> TokenPair:
        access_token, _ = create_jwt_token(
            subject=user_id,
            token_type="access",
            expires_delta=timedelta(minutes=settings.jwt_access_token_expire_minutes),
        )

        refresh_jti = secrets.token_hex(16)
        refresh_token, refresh_expires_at = create_jwt_token(
            subject=user_id,
            token_type="refresh",
            expires_delta=timedelta(days=settings.jwt_refresh_token_expire_days),
            jti=refresh_jti,
        )
        await self.refresh_token_repository.create(
            session,
            user_id=user_id,
            jti=refresh_jti,
            expires_at=refresh_expires_at,
            created_at=utcnow(),
        )

        return TokenPair(access_token=access_token, refresh_token=refresh_token)

    @staticmethod
    def _code_key(phone: str) -> str:
        return f"otp:code:{phone}"

    @staticmethod
    def _rate_key(phone: str) -> str:
        return f"otp:rate:{phone}"

    @staticmethod
    def _attempts_key(phone: str) -> str:
        return f"otp:attempts:{phone}"


def get_auth_service() -> AuthService:
    return AuthService(UserRepository(), RefreshTokenRepository())


```

## app/services/export_service.py

```python
from __future__ import annotations

import csv
from pathlib import Path
from uuid import UUID

from fastapi import HTTPException, status
from openpyxl import Workbook
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import utcnow
from app.models.export import ExportFormat, ExportJob, ExportStatus
from app.models.question import Question
from app.models.response import Answer, SurveyResponse
from app.models.survey import Survey
from app.models.user import User
from app.schemas.export import ExportCreate

EXPORT_DIR = Path("exports")


class ExportService:
    async def create(self, session: AsyncSession, survey_id: UUID, payload: ExportCreate, current_user: User) -> ExportJob:
        survey = await session.get(Survey, survey_id)
        if survey is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found")

        job = ExportJob(
            survey_id=survey_id,
            requested_by_id=current_user.id,
            format=payload.format,
            status=ExportStatus.PENDING,
        )
        session.add(job)
        await session.flush()

        rows = await self._rows(session, survey_id)
        EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        suffix = "csv" if payload.format == ExportFormat.CSV else "xlsx"
        path = EXPORT_DIR / f"survey_{survey_id}_{job.id}.{suffix}"
        if payload.format == ExportFormat.CSV:
            self._write_csv(path, rows)
        else:
            self._write_xlsx(path, rows)

        job.status = ExportStatus.READY
        job.file_path = str(path)
        job.completed_at = utcnow()
        await session.commit()
        await session.refresh(job)
        return job

    async def get(self, session: AsyncSession, export_id: UUID) -> ExportJob:
        job = await session.get(ExportJob, export_id)
        if job is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Export job not found")
        return job

    async def _rows(self, session: AsyncSession, survey_id: UUID) -> list[dict]:
        result = await session.execute(
            select(SurveyResponse, Question.title, Answer.value)
            .join(Answer, Answer.response_id == SurveyResponse.id)
            .join(Question, Question.id == Answer.question_id)
            .where(SurveyResponse.survey_id == survey_id)
            .order_by(SurveyResponse.submitted_at.desc().nullslast(), Question.position.asc())
        )
        rows = []
        for response, question_title, value in result.all():
            rows.append(
                {
                    "response_id": str(response.id),
                    "submitted_at": response.submitted_at.isoformat() if response.submitted_at else "",
                    "anonymous_session_id": response.anonymous_session_id or "",
                    "user_id": str(response.user_id) if response.user_id else "",
                    "question": question_title,
                    "answer": value,
                }
            )
        return rows

    @staticmethod
    def _write_csv(path: Path, rows: list[dict]) -> None:
        fieldnames = ["response_id", "submitted_at", "anonymous_session_id", "user_id", "question", "answer"]
        with path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    @staticmethod
    def _write_xlsx(path: Path, rows: list[dict]) -> None:
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Survey Responses"
        fieldnames = ["response_id", "submitted_at", "anonymous_session_id", "user_id", "question", "answer"]
        sheet.append(fieldnames)
        for row in rows:
            sheet.append([str(row[field]) for field in fieldnames])
        workbook.save(path)


def get_export_service() -> ExportService:
    return ExportService()


```

## app/services/notification_service.py

```python
from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import utcnow
from app.models.notification import (
    DeliveryStatus,
    Notification,
    NotificationDelivery,
    NotificationSettings,
    NotificationSubscription,
)
from app.models.user import User
from app.repositories.notification_repository import NotificationRepository
from app.schemas.notification import (
    NotificationCreate,
    NotificationSettingsUpdate,
    NotificationSubscriptionCreate,
)

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self, repository: NotificationRepository) -> None:
        self.repository = repository

    async def get_settings(self, session: AsyncSession, current_user: User) -> NotificationSettings:
        settings = await self.repository.get_settings(session, current_user.id)
        if settings is None:
            settings = NotificationSettings(user_id=current_user.id)
            session.add(settings)
            await session.commit()
            await session.refresh(settings)
        return settings

    async def update_settings(
        self,
        session: AsyncSession,
        current_user: User,
        payload: NotificationSettingsUpdate,
    ) -> NotificationSettings:
        settings = await self.get_settings(session, current_user)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(settings, field, value)
        await session.commit()
        await session.refresh(settings)
        return settings

    async def list_subscriptions(self, session: AsyncSession, current_user: User) -> list[NotificationSubscription]:
        return await self.repository.list_subscriptions(session, current_user.id)

    async def create_subscription(
        self,
        session: AsyncSession,
        current_user: User,
        payload: NotificationSubscriptionCreate,
    ) -> NotificationSubscription:
        subscription = NotificationSubscription(user_id=current_user.id, **payload.model_dump())
        session.add(subscription)
        await session.commit()
        await session.refresh(subscription)
        return subscription

    async def send(self, session: AsyncSession, payload: NotificationCreate) -> list[NotificationDelivery]:
        notification = await self.repository.create_notification(
            session,
            Notification(
                survey_id=payload.survey_id,
                title=payload.title,
                body=payload.body,
                payload=payload.payload,
            ),
        )
        deliveries: list[NotificationDelivery] = []
        for user_id in payload.user_ids:
            for channel in payload.channels:
                logger.info("PulseHR notification via %s to %s: %s", channel.value, user_id, payload.title)
                delivery = await self.repository.create_delivery(
                    session,
                    NotificationDelivery(
                        notification_id=notification.id,
                        user_id=user_id,
                        channel=channel,
                        status=DeliveryStatus.SENT,
                        sent_at=utcnow(),
                    ),
                )
                deliveries.append(delivery)
        await session.commit()
        return deliveries


def get_notification_service() -> NotificationService:
    return NotificationService(NotificationRepository())


```

## app/services/question_service.py

```python
from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.question import Question, QuestionOption
from app.models.survey import SurveyStatus
from app.repositories.survey_repository import QuestionRepository, SurveyRepository
from app.schemas.question import QuestionCreate, QuestionReorderRequest, QuestionUpdate


class QuestionService:
    def __init__(self, survey_repository: SurveyRepository, question_repository: QuestionRepository) -> None:
        self.survey_repository = survey_repository
        self.question_repository = question_repository

    async def create(self, session: AsyncSession, survey_id: UUID, payload: QuestionCreate) -> Question:
        survey = await self.survey_repository.get(session, survey_id)
        if survey is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found")
        if survey.status == SurveyStatus.ARCHIVED:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Archived survey cannot be edited")

        data = payload.model_dump(exclude={"options"})
        question = Question(survey_id=survey_id, **data)
        question.options = [QuestionOption(**option.model_dump()) for option in payload.options]
        created = await self.question_repository.create(session, question)
        await session.commit()
        return created

    async def update(self, session: AsyncSession, question_id: UUID, payload: QuestionUpdate) -> Question:
        question = await self.question_repository.get(session, question_id)
        if question is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")

        data = payload.model_dump(exclude_unset=True, exclude={"options"})
        for field, value in data.items():
            setattr(question, field, value)
        if payload.options is not None:
            await self.question_repository.replace_options(
                session,
                question,
                [QuestionOption(**option.model_dump()) for option in payload.options],
            )
        await session.commit()
        await session.refresh(question)
        return question

    async def delete(self, session: AsyncSession, question_id: UUID) -> None:
        question = await self.question_repository.get(session, question_id)
        if question is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")
        await session.delete(question)
        await session.commit()

    async def reorder(self, session: AsyncSession, survey_id: UUID, payload: QuestionReorderRequest) -> None:
        survey = await self.survey_repository.get(session, survey_id, with_details=True)
        if survey is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found")
        by_id = {question.id: question for question in survey.questions}
        for item in payload.items:
            if item.id not in by_id:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found in survey")
            by_id[item.id].position = item.position
        await session.commit()


def get_question_service() -> QuestionService:
    return QuestionService(SurveyRepository(), QuestionRepository())


```

## app/services/response_service.py

```python
from __future__ import annotations

import secrets
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import utcnow
from app.models.response import ResponseStatus, SurveyResponse
from app.models.survey import AssignmentStatus, SurveyAssignment, SurveyStatus
from app.models.user import User
from app.repositories.response_repository import ResponseRepository
from app.repositories.survey_repository import QuestionRepository, SurveyRepository
from app.schemas.response import AnswerUpsert


class ResponseService:
    def __init__(
        self,
        survey_repository: SurveyRepository,
        question_repository: QuestionRepository,
        response_repository: ResponseRepository,
    ) -> None:
        self.survey_repository = survey_repository
        self.question_repository = question_repository
        self.response_repository = response_repository

    async def start(self, session: AsyncSession, survey_id: UUID, current_user: User) -> dict:
        survey = await self.survey_repository.get(session, survey_id, with_details=True)
        if survey is None or survey.status != SurveyStatus.PUBLISHED:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Published survey not found")

        anonymous_session_id = secrets.token_urlsafe(32) if survey.is_anonymous else None
        response = SurveyResponse(
            survey_id=survey_id,
            user_id=None if survey.is_anonymous else current_user.id,
            anonymous_session_id=anonymous_session_id,
            status=ResponseStatus.IN_PROGRESS,
            started_at=utcnow(),
        )
        created = await self.response_repository.create(session, response)
        await self._mark_assignment(session, survey_id, current_user.id, AssignmentStatus.STARTED)
        await session.commit()
        return {
            "response_id": created.id,
            "survey_id": survey_id,
            "is_anonymous": survey.is_anonymous,
            "anonymous_session_id": anonymous_session_id,
            "warning": (
                "Этот опрос анонимный. HR не сможет определить автора ответа."
                if survey.is_anonymous
                else "Ваши ответы будут доступны HR."
            ),
        }

    async def upsert_answer(
        self,
        session: AsyncSession,
        response_id: UUID,
        payload: AnswerUpsert,
        current_user: User,
    ):
        response = await self._get_owned_response(session, response_id, current_user)
        if response.status == ResponseStatus.SUBMITTED:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Response already submitted")
        question = await self.question_repository.get(session, payload.question_id)
        if question is None or question.survey_id != response.survey_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found in survey")
        answer = await self.response_repository.upsert_answer(
            session,
            response_id=response_id,
            question_id=payload.question_id,
            value=payload.value,
        )
        await session.commit()
        return answer

    async def submit(self, session: AsyncSession, response_id: UUID, current_user: User) -> SurveyResponse:
        response = await self._get_owned_response(session, response_id, current_user)
        if response.status == ResponseStatus.SUBMITTED:
            return response

        survey = await self.survey_repository.get(session, response.survey_id, with_details=True)
        answered_question_ids = {answer.question_id for answer in response.answers}
        missing = [
            str(question.id)
            for question in survey.questions
            if question.is_required and question.id not in answered_question_ids
        ]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"message": "Required questions are missing", "question_ids": missing},
            )

        response.status = ResponseStatus.SUBMITTED
        response.submitted_at = utcnow()
        await self._mark_assignment(session, response.survey_id, current_user.id, AssignmentStatus.SUBMITTED)
        await session.commit()
        await session.refresh(response)
        return response

    async def get(self, session: AsyncSession, response_id: UUID, current_user: User) -> SurveyResponse:
        return await self._get_owned_response(session, response_id, current_user)

    async def _get_owned_response(
        self,
        session: AsyncSession,
        response_id: UUID,
        current_user: User,
    ) -> SurveyResponse:
        response = await self.response_repository.get(session, response_id)
        if response is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Response not found")
        if response.user_id is not None and response.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Response belongs to another user")
        return response

    @staticmethod
    async def _mark_assignment(
        session: AsyncSession,
        survey_id: UUID,
        user_id: UUID,
        assignment_status: AssignmentStatus,
    ) -> None:
        result = await session.execute(
            select(SurveyAssignment).where(
                SurveyAssignment.survey_id == survey_id,
                SurveyAssignment.user_id == user_id,
            )
        )
        assignment = result.scalar_one_or_none()
        if assignment is None:
            assignment = SurveyAssignment(survey_id=survey_id, user_id=user_id)
            session.add(assignment)
        assignment.status = assignment_status
        if assignment_status == AssignmentStatus.SUBMITTED:
            assignment.submitted_at = utcnow()


def get_response_service() -> ResponseService:
    return ResponseService(SurveyRepository(), QuestionRepository(), ResponseRepository())


```

## app/services/survey_logic_service.py

```python
from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.survey_logic import SurveyRule
from app.repositories.survey_repository import QuestionRepository, SurveyRepository, SurveyRuleRepository
from app.schemas.survey_logic import SurveyRuleCreate, SurveyRuleUpdate


class SurveyLogicService:
    def __init__(
        self,
        survey_repository: SurveyRepository,
        question_repository: QuestionRepository,
        rule_repository: SurveyRuleRepository,
    ) -> None:
        self.survey_repository = survey_repository
        self.question_repository = question_repository
        self.rule_repository = rule_repository

    async def create(self, session: AsyncSession, survey_id: UUID, payload: SurveyRuleCreate) -> SurveyRule:
        survey = await self.survey_repository.get(session, survey_id)
        question = await self.question_repository.get(session, payload.target_question_id)
        if survey is None or question is None or question.survey_id != survey_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey or target question not found")
        rule = SurveyRule(survey_id=survey_id, **payload.model_dump())
        created = await self.rule_repository.create(session, rule)
        await session.commit()
        return created

    async def update(self, session: AsyncSession, rule_id: UUID, payload: SurveyRuleUpdate) -> SurveyRule:
        rule = await self.rule_repository.get(session, rule_id)
        if rule is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(rule, field, value)
        await session.commit()
        await session.refresh(rule)
        return rule

    async def delete(self, session: AsyncSession, rule_id: UUID) -> None:
        rule = await self.rule_repository.get(session, rule_id)
        if rule is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")
        await session.delete(rule)
        await session.commit()


def get_survey_logic_service() -> SurveyLogicService:
    return SurveyLogicService(SurveyRepository(), QuestionRepository(), SurveyRuleRepository())


```

## app/services/survey_service.py

```python
from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.survey import AssignmentStatus, Survey, SurveyAssignment, SurveyStatus
from app.models.user import User
from app.repositories.survey_repository import SurveyRepository
from app.schemas.survey import SurveyAssignmentCreate, SurveyCreate, SurveyUpdate


class SurveyService:
    def __init__(self, repository: SurveyRepository) -> None:
        self.repository = repository

    async def create(self, session: AsyncSession, payload: SurveyCreate, current_user: User) -> Survey:
        survey = Survey(**payload.model_dump(), created_by_id=current_user.id)
        created = await self.repository.create(session, survey)
        await session.commit()
        return created

    async def list(self, session: AsyncSession, *, limit: int, offset: int) -> list[Survey]:
        return await self.repository.list(session, limit=limit, offset=offset)

    async def get(self, session: AsyncSession, survey_id: UUID) -> Survey:
        survey = await self.repository.get(session, survey_id, with_details=True)
        if survey is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found")
        return survey

    async def update(self, session: AsyncSession, survey_id: UUID, payload: SurveyUpdate) -> Survey:
        survey = await self.get(session, survey_id)
        if survey.status not in {SurveyStatus.DRAFT, SurveyStatus.PUBLISHED}:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Survey cannot be edited")
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(survey, field, value)
        await session.commit()
        await session.refresh(survey)
        return survey

    async def publish(self, session: AsyncSession, survey_id: UUID) -> Survey:
        survey = await self.get(session, survey_id)
        if not survey.questions:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Survey has no questions")
        survey.status = SurveyStatus.PUBLISHED
        await session.commit()
        await session.refresh(survey)
        return survey

    async def close(self, session: AsyncSession, survey_id: UUID) -> Survey:
        survey = await self.get(session, survey_id)
        survey.status = SurveyStatus.CLOSED
        await session.commit()
        await session.refresh(survey)
        return survey

    async def archive(self, session: AsyncSession, survey_id: UUID) -> Survey:
        survey = await self.get(session, survey_id)
        survey.status = SurveyStatus.ARCHIVED
        await session.commit()
        await session.refresh(survey)
        return survey

    async def assign(
        self,
        session: AsyncSession,
        survey_id: UUID,
        payload: SurveyAssignmentCreate,
    ) -> list[SurveyAssignment]:
        await self.get(session, survey_id)
        existing_result = await session.execute(
            select(SurveyAssignment).where(
                SurveyAssignment.survey_id == survey_id,
                SurveyAssignment.user_id.in_(payload.user_ids),
            )
        )
        existing_user_ids = {assignment.user_id for assignment in existing_result.scalars().all()}
        assignments = [
            SurveyAssignment(survey_id=survey_id, user_id=user_id, status=AssignmentStatus.PENDING)
            for user_id in payload.user_ids
            if user_id not in existing_user_ids
        ]
        session.add_all(assignments)
        await session.commit()
        return assignments

    async def employee_dashboard(self, session: AsyncSession, current_user: User):
        surveys = await self.repository.list_published_for_user(session, current_user.id)
        cards = [self._employee_card(survey, current_user.id) for survey in surveys]
        completed = sum(1 for card in cards if card["completion_percent"] == 100)
        completion_percent = round((completed / len(cards)) * 100) if cards else 0
        return {
            "active_surveys": len(cards) - completed,
            "completed_surveys": completed,
            "completion_percent": completion_percent,
            "surveys": cards,
        }

    async def employee_surveys(self, session: AsyncSession, current_user: User):
        surveys = await self.repository.list_published_for_user(session, current_user.id)
        return [self._employee_card(survey, current_user.id) for survey in surveys]

    @staticmethod
    def _employee_card(survey: Survey, user_id: UUID) -> dict:
        assignment = next((item for item in survey.assignments if item.user_id == user_id), None)
        completion_percent = 100 if assignment and assignment.status == AssignmentStatus.SUBMITTED else 0
        return {
            "id": survey.id,
            "title": survey.title,
            "description": survey.description,
            "status": survey.status,
            "assignment_status": assignment.status if assignment else None,
            "is_anonymous": survey.is_anonymous,
            "anonymity_notice": (
                "Этот опрос анонимный. HR не сможет определить автора ответа."
                if survey.is_anonymous
                else "Ваши ответы будут доступны HR."
            ),
            "ends_at": survey.ends_at,
            "estimated_minutes": survey.estimated_minutes,
            "completion_percent": completion_percent,
        }


def get_survey_service() -> SurveyService:
    return SurveyService(SurveyRepository())


```

## app/services/user_service.py

```python
from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    def __init__(self, repository: UserRepository) -> None:
        self.repository = repository

    async def create(self, session: AsyncSession, payload: UserCreate):
        existing = await self.repository.get_by_phone(session, payload.phone)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this phone already exists",
            )

        try:
            user = await self.repository.create(session, payload)
            await session.commit()
            return user
        except IntegrityError as exc:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this phone already exists",
            ) from exc

    async def get(self, session: AsyncSession, user_id: UUID):
        user = await self.repository.get_by_id(session, user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return user

    async def list(self, session: AsyncSession, *, limit: int = 100, offset: int = 0):
        if limit < 1 or limit > 500:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid limit")
        if offset < 0:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid offset")
        return await self.repository.list(session, limit=limit, offset=offset)

    async def update(self, session: AsyncSession, user_id: UUID, payload: UserUpdate):
        user = await self.get(session, user_id)
        if payload.phone is not None:
            existing = await self.repository.get_by_phone(session, payload.phone)
            if existing is not None and existing.id != user.id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="User with this phone already exists",
                )

        try:
            updated = await self.repository.update(session, user, payload)
            await session.commit()
            return updated
        except IntegrityError as exc:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this phone already exists",
            ) from exc

    async def delete(self, session: AsyncSession, user_id: UUID) -> None:
        user = await self.get(session, user_id)
        await self.repository.delete(session, user)
        await session.commit()


def get_user_service() -> UserService:
    return UserService(UserRepository())


```

## docker-compose.yml

```yaml
services:
  api:
    build: .
    container_name: pulsehr-api
    env_file:
      - .env
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    command: >
      sh -c "alembic upgrade head &&
             uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
    volumes:
      - .:/app

  postgres:
    image: postgres:16-alpine
    container_name: pulsehr-postgres
    environment:
      POSTGRES_DB: pulsehr
      POSTGRES_USER: pulsehr
      POSTGRES_PASSWORD: pulsehr_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U pulsehr -d pulsehr"]
      interval: 5s
      timeout: 5s
      retries: 10

  redis:
    image: redis:7-alpine
    container_name: pulsehr-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 10

volumes:
  postgres_data:
  redis_data:


```

## frontend/index.html

```html
<!doctype html>
<html lang="ru">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>PulseHR</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>


```

## frontend/package.json

```json
{
  "name": "pulsehr-frontend",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "@ant-design/icons": "^5.5.1",
    "@dnd-kit/core": "^6.1.0",
    "@dnd-kit/sortable": "^8.0.0",
    "@dnd-kit/utilities": "^3.2.2",
    "@hookform/resolvers": "^3.9.0",
    "@tanstack/react-query": "^5.59.0",
    "antd": "^5.21.1",
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "react-hook-form": "^7.53.0",
    "react-router-dom": "^6.26.2",
    "recharts": "^2.12.7",
    "zod": "^3.23.8",
    "zustand": "^5.0.0"
  },
  "devDependencies": {
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "@vitejs/plugin-react": "^4.3.1",
    "typescript": "^5.6.2",
    "vite": "^5.4.8"
  }
}


```

## frontend/src/api/client.ts

```ts
import { useAuthStore } from "../stores/authStore";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

export async function apiRequest<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = useAuthStore.getState().accessToken;
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers
    }
  });

  if (!response.ok) {
    const detail = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(typeof detail.detail === "string" ? detail.detail : JSON.stringify(detail.detail));
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}


```

## frontend/src/api/types.ts

```ts
export type Role = "HR" | "EMPLOYEE";
export type SurveyStatus = "DRAFT" | "PUBLISHED" | "CLOSED" | "ARCHIVED";
export type QuestionType = "SINGLE_CHOICE" | "MULTIPLE_CHOICE" | "RATING" | "TEXT" | "MATRIX";

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
}

export interface Survey {
  id: string;
  title: string;
  description: string | null;
  status: SurveyStatus;
  is_anonymous: boolean;
  estimated_minutes: number;
  ends_at: string | null;
}

export interface QuestionOption {
  id?: string;
  label: string;
  value: string;
  position: number;
}

export interface Question {
  id: string;
  survey_id: string;
  title: string;
  description: string | null;
  type: QuestionType;
  position: number;
  is_required: boolean;
  settings: Record<string, unknown>;
  options: QuestionOption[];
}

export interface SurveyDetail extends Survey {
  questions: Question[];
  rules: SurveyRule[];
}

export interface SurveyRule {
  id: string;
  target_question_id: string;
  name: string;
  priority: number;
  action: "SHOW_QUESTION" | "HIDE_QUESTION";
  condition: Record<string, unknown>;
}

export interface EmployeeSurveyCard extends Survey {
  assignment_status: "PENDING" | "STARTED" | "SUBMITTED" | null;
  anonymity_notice: string;
  completion_percent: number;
}


```

## frontend/src/components/QuestionRenderer.tsx

```tsx
import { Checkbox, Form, Input, Radio, Rate, Table } from "antd";
import { Question } from "../api/types";

interface Props {
  question: Question;
  value?: Record<string, unknown>;
  onChange: (value: Record<string, unknown>) => void;
}

export function QuestionRenderer({ question, value, onChange }: Props) {
  if (question.type === "SINGLE_CHOICE") {
    return (
      <Radio.Group value={value?.option} onChange={(event) => onChange({ option: event.target.value })}>
        {question.options.map((option) => (
          <Radio key={option.value} value={option.value}>
            {option.label}
          </Radio>
        ))}
      </Radio.Group>
    );
  }

  if (question.type === "MULTIPLE_CHOICE") {
    return (
      <Checkbox.Group
        value={(value?.options as string[]) ?? []}
        options={question.options.map((option) => ({ label: option.label, value: option.value }))}
        onChange={(options) => onChange({ options })}
      />
    );
  }

  if (question.type === "RATING") {
    return <Rate count={Number(question.settings.max ?? 10)} value={Number(value?.score ?? 0)} onChange={(score) => onChange({ score })} />;
  }

  if (question.type === "MATRIX") {
    const rows = (question.settings.rows as string[]) ?? [];
    const columns = (question.settings.columns as string[]) ?? ["1", "2", "3", "4", "5"];
    return (
      <Table
        pagination={false}
        rowKey="row"
        dataSource={rows.map((row) => ({ row }))}
        columns={[
          { title: "", dataIndex: "row" },
          ...columns.map((column) => ({
            title: column,
            render: (_: unknown, record: { row: string }) => (
              <Radio
                checked={(value?.rows as Record<string, string> | undefined)?.[record.row] === column}
                onChange={() => onChange({ rows: { ...((value?.rows as object) ?? {}), [record.row]: column } })}
              />
            )
          }))
        ]}
      />
    );
  }

  return (
    <Form.Item>
      <Input.TextArea value={(value?.text as string) ?? ""} rows={4} onChange={(event) => onChange({ text: event.target.value })} />
    </Form.Item>
  );
}


```

## frontend/src/features/surveyLogic/evaluateRules.ts

```ts
import { Question, SurveyRule } from "../../api/types";

type Answers = Record<string, Record<string, unknown>>;

function readPath(source: Record<string, unknown>, path: string): unknown {
  return path.split(".").reduce<unknown>((value, key) => {
    if (value && typeof value === "object") {
      return (value as Record<string, unknown>)[key];
    }
    return undefined;
  }, source);
}

function compare(actual: unknown, operator: string, expected: unknown): boolean {
  if (operator === "equals") return actual === expected;
  if (operator === "lte") return Number(actual) <= Number(expected);
  if (operator === "gte") return Number(actual) >= Number(expected);
  if (operator === "in") return Array.isArray(expected) && expected.includes(actual);
  return false;
}

function evaluate(condition: Record<string, unknown>, context: Record<string, unknown>): boolean {
  const op = condition.op;
  const conditions = (condition.conditions as Record<string, unknown>[] | undefined) ?? [];
  if (op === "AND") return conditions.every((item) => evaluate(item, context));
  if (op === "OR") return conditions.some((item) => evaluate(item, context));
  if (op === "NOT") return !evaluate(conditions[0] ?? {}, context);

  const field = condition.field;
  const operator = condition.operator;
  if (typeof field !== "string" || typeof operator !== "string") return false;
  return compare(readPath(context, field), operator, condition.value);
}

export function visibleQuestions(questions: Question[], rules: SurveyRule[], answers: Answers): Question[] {
  const hidden = new Set<string>();
  const explicitlyShown = new Set<string>();
  const context = { answers };

  for (const rule of [...rules].sort((a, b) => a.priority - b.priority)) {
    if (!evaluate(rule.condition, context)) continue;
    if (rule.action === "HIDE_QUESTION") hidden.add(rule.target_question_id);
    if (rule.action === "SHOW_QUESTION") explicitlyShown.add(rule.target_question_id);
  }

  return questions
    .filter((question) => !hidden.has(question.id))
    .filter((question) => {
      const showRules = rules.filter((rule) => rule.action === "SHOW_QUESTION" && rule.target_question_id === question.id);
      return showRules.length === 0 || explicitlyShown.has(question.id);
    })
    .sort((a, b) => a.position - b.position);
}


```

## frontend/src/main.tsx

```tsx
import "@ant-design/v5-patch-for-react-19";
import "antd/dist/reset.css";
import "./styles.css";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ConfigProvider } from "antd";
import ruRU from "antd/locale/ru_RU";
import React from "react";
import ReactDOM from "react-dom/client";
import { AppRouter } from "./router/AppRouter";

const queryClient = new QueryClient();

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ConfigProvider locale={ruRU}>
      <QueryClientProvider client={queryClient}>
        <AppRouter />
      </QueryClientProvider>
    </ConfigProvider>
  </React.StrictMode>
);


```

## frontend/src/pages/LoginPage.tsx

```tsx
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { Button, Card, Form, Input, Typography, message } from "antd";
import { Controller, useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import { z } from "zod";
import { apiRequest } from "../api/client";
import { TokenPair } from "../api/types";
import { useAuthStore } from "../stores/authStore";

const schema = z.object({
  phone: z.string().min(5),
  code: z.string().regex(/^\d{6}$/).optional()
});

type LoginForm = z.infer<typeof schema>;

export function LoginPage() {
  const navigate = useNavigate();
  const setTokens = useAuthStore((state) => state.setTokens);
  const form = useForm<LoginForm>({ resolver: zodResolver(schema), defaultValues: { phone: "" } });

  const sendCode = useMutation({
    mutationFn: (phone: string) =>
      apiRequest("/auth/send-code", { method: "POST", body: JSON.stringify({ phone }) }),
    onSuccess: () => message.success("OTP generated")
  });

  const verifyCode = useMutation({
    mutationFn: (payload: Required<LoginForm>) =>
      apiRequest<TokenPair>("/auth/verify-code", { method: "POST", body: JSON.stringify(payload) }),
    onSuccess: (tokens) => {
      setTokens(tokens.access_token, tokens.refresh_token);
      navigate("/employee");
    }
  });

  const phone = form.watch("phone");

  return (
    <div style={{ minHeight: "100vh", display: "grid", placeItems: "center", padding: 24 }}>
      <Card style={{ width: 420 }}>
        <Typography.Title level={2}>PulseHR</Typography.Title>
        <Form layout="vertical" onFinish={form.handleSubmit((values) => verifyCode.mutate(values as Required<LoginForm>))}>
          <Form.Item label="Phone">
            <Controller name="phone" control={form.control} render={({ field }) => <Input {...field} />} />
          </Form.Item>
          <Form.Item label="OTP">
            <Controller name="code" control={form.control} render={({ field }) => <Input {...field} maxLength={6} />} />
          </Form.Item>
          <Button block onClick={() => sendCode.mutate(phone)} loading={sendCode.isPending}>
            Send code
          </Button>
          <Button block type="primary" htmlType="submit" loading={verifyCode.isPending} style={{ marginTop: 12 }}>
            Login
          </Button>
        </Form>
      </Card>
    </div>
  );
}


```

## frontend/src/pages/employee/EmployeeDashboardPage.tsx

```tsx
import { useQuery } from "@tanstack/react-query";
import { Card, Progress, Statistic } from "antd";
import { apiRequest } from "../../api/client";

export function EmployeeDashboardPage() {
  const { data } = useQuery({
    queryKey: ["employee-dashboard"],
    queryFn: () => apiRequest<{ active_surveys: number; completed_surveys: number; completion_percent: number }>("/employee/dashboard")
  });

  return (
    <div className="grid">
      <Card><Statistic title="Active surveys" value={data?.active_surveys ?? 0} /></Card>
      <Card><Statistic title="Completed surveys" value={data?.completed_surveys ?? 0} /></Card>
      <Card><Progress type="dashboard" percent={data?.completion_percent ?? 0} /></Card>
    </div>
  );
}


```

## frontend/src/pages/employee/NotificationSettingsPage.tsx

```tsx
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Button, Card, Form, Input, Switch } from "antd";
import { apiRequest } from "../../api/client";

interface Settings {
  push_enabled: boolean;
  telegram_enabled: boolean;
  email_enabled: boolean;
  sms_enabled: boolean;
  telegram_chat_id: string | null;
  email: string | null;
}

export function NotificationSettingsPage() {
  const queryClient = useQueryClient();
  const { data } = useQuery({ queryKey: ["notification-settings"], queryFn: () => apiRequest<Settings>("/notifications/settings") });
  const mutation = useMutation({
    mutationFn: (payload: Partial<Settings>) =>
      apiRequest("/notifications/settings", { method: "PATCH", body: JSON.stringify(payload) }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notification-settings"] })
  });

  return (
    <Card title="Notification Settings">
      <Form layout="vertical" key={JSON.stringify(data)} initialValues={data} onFinish={(values) => mutation.mutate(values)}>
        <Form.Item name="push_enabled" label="Push" valuePropName="checked"><Switch /></Form.Item>
        <Form.Item name="telegram_enabled" label="Telegram" valuePropName="checked"><Switch /></Form.Item>
        <Form.Item name="telegram_chat_id" label="Telegram chat"><Input /></Form.Item>
        <Form.Item name="email_enabled" label="Email" valuePropName="checked"><Switch /></Form.Item>
        <Form.Item name="email" label="Email address"><Input /></Form.Item>
        <Form.Item name="sms_enabled" label="SMS" valuePropName="checked"><Switch /></Form.Item>
        <Button type="primary" htmlType="submit">Save</Button>
      </Form>
    </Card>
  );
}

```

## frontend/src/pages/employee/SurveyListPage.tsx

```tsx
import { ClockCircleOutlined } from "@ant-design/icons";
import { useQuery } from "@tanstack/react-query";
import { Button, Card, Progress, Space, Tag, Typography } from "antd";
import { Link } from "react-router-dom";
import { apiRequest } from "../../api/client";
import { EmployeeSurveyCard } from "../../api/types";

export function SurveyListPage() {
  const { data = [] } = useQuery({
    queryKey: ["employee-surveys"],
    queryFn: () => apiRequest<EmployeeSurveyCard[]>("/employee/surveys")
  });

  return (
    <div className="grid">
      {data.map((survey) => (
        <Card key={survey.id}>
          <Typography.Title level={4}>{survey.title}</Typography.Title>
          <Typography.Paragraph>{survey.description}</Typography.Paragraph>
          <Space wrap>
            <Tag>{survey.status}</Tag>
            <Tag icon={<ClockCircleOutlined />}>{survey.estimated_minutes} min</Tag>
          </Space>
          <Progress percent={survey.completion_percent} />
          <Button type="primary">
            <Link to={`/employee/surveys/${survey.id}`}>Open</Link>
          </Button>
        </Card>
      ))}
    </div>
  );
}


```

## frontend/src/pages/employee/SurveyPassPage.tsx

```tsx
import { useMutation, useQuery } from "@tanstack/react-query";
import { Alert, Button, Card, Space, Typography, message } from "antd";
import { useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { apiRequest } from "../../api/client";
import { SurveyDetail } from "../../api/types";
import { QuestionRenderer } from "../../components/QuestionRenderer";
import { visibleQuestions as evaluateVisibleQuestions } from "../../features/surveyLogic/evaluateRules";

export function SurveyPassPage() {
  const { surveyId } = useParams();
  const [responseId, setResponseId] = useState<string | null>(null);
  const [answers, setAnswers] = useState<Record<string, Record<string, unknown>>>({});

  const { data: survey } = useQuery({
    queryKey: ["employee-survey", surveyId],
    queryFn: () => apiRequest<SurveyDetail>(`/employee/surveys/${surveyId}`),
    enabled: Boolean(surveyId)
  });

  const start = useMutation({
    mutationFn: () => apiRequest<{ response_id: string; warning: string }>(`/employee/surveys/${surveyId}/start`, { method: "POST" }),
    onSuccess: (data) => {
      setResponseId(data.response_id);
      message.info(data.warning);
    }
  });

  const saveAnswer = useMutation({
    mutationFn: ({ questionId, value }: { questionId: string; value: Record<string, unknown> }) =>
      apiRequest(`/responses/${responseId}/answers`, {
        method: "POST",
        body: JSON.stringify({ question_id: questionId, value })
      })
  });

  const submit = useMutation({
    mutationFn: () => apiRequest(`/responses/${responseId}/submit`, { method: "POST" }),
    onSuccess: () => message.success("Submitted")
  });

  const visibleQuestions = useMemo(
    () => (survey ? evaluateVisibleQuestions(survey.questions, survey.rules, answers) : []),
    [answers, survey]
  );

  if (!survey) return null;

  return (
    <Card>
      <Typography.Title level={2}>{survey.title}</Typography.Title>
      <Alert
        type={survey.is_anonymous ? "success" : "warning"}
        message={
          survey.is_anonymous
            ? "Этот опрос анонимный. HR не сможет определить автора ответа."
            : "Ваши ответы будут доступны HR."
        }
        style={{ marginBottom: 16 }}
      />
      {!responseId && <Button type="primary" onClick={() => start.mutate()}>Start</Button>}
      {responseId && (
        <Space direction="vertical" style={{ width: "100%" }}>
          {visibleQuestions.map((question) => (
            <Card key={question.id} className="question-row">
              <Typography.Title level={5}>{question.title}</Typography.Title>
              <QuestionRenderer
                question={question}
                value={answers[question.id]}
                onChange={(value) => {
                  setAnswers((state) => ({ ...state, [question.id]: value }));
                  saveAnswer.mutate({ questionId: question.id, value });
                }}
              />
            </Card>
          ))}
          <Button type="primary" onClick={() => submit.mutate()} loading={submit.isPending}>Submit</Button>
        </Space>
      )}
    </Card>
  );
}

```

## frontend/src/pages/hr/AnalyticsPage.tsx

```tsx
import { useQuery } from "@tanstack/react-query";
import { Card } from "antd";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { apiRequest } from "../../api/client";

export function AnalyticsPage() {
  const { data } = useQuery({
    queryKey: ["analytics-overview"],
    queryFn: () => apiRequest<{ completion_rate: number; response_rate: number; enps: number | null }>("/analytics/overview")
  });

  const chartData = [
    { name: "Completion", value: data?.completion_rate ?? 0 },
    { name: "Response", value: data?.response_rate ?? 0 },
    { name: "eNPS", value: data?.enps ?? 0 }
  ];

  return (
    <Card title="Analytics">
      <ResponsiveContainer width="100%" height={320}>
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis />
          <Tooltip />
          <Bar dataKey="value" fill="#1677ff" />
        </BarChart>
      </ResponsiveContainer>
    </Card>
  );
}


```

## frontend/src/pages/hr/HrDashboardPage.tsx

```tsx
import { useQuery } from "@tanstack/react-query";
import { Card, Statistic } from "antd";
import { apiRequest } from "../../api/client";

export function HrDashboardPage() {
  const { data } = useQuery({
    queryKey: ["analytics-overview"],
    queryFn: () =>
      apiRequest<{
        active_surveys: number;
        completion_rate: number;
        response_rate: number;
        enps: number | null;
        notification_efficiency: Record<string, unknown>;
      }>("/analytics/overview")
  });

  return (
    <div className="grid">
      <Card><Statistic title="Active surveys" value={data?.active_surveys ?? 0} /></Card>
      <Card><Statistic title="Completion rate" value={data?.completion_rate ?? 0} suffix="%" /></Card>
      <Card><Statistic title="Response rate" value={data?.response_rate ?? 0} suffix="%" /></Card>
      <Card><Statistic title="eNPS" value={data?.enps ?? 0} /></Card>
    </div>
  );
}


```

## frontend/src/pages/hr/SurveyBuilderPage.tsx

```tsx
import { DndContext, DragEndEvent } from "@dnd-kit/core";
import { SortableContext, arrayMove, useSortable, verticalListSortingStrategy } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Button, Card, Form, Input, Modal, Select, Space, Switch, Tabs } from "antd";
import { useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { apiRequest } from "../../api/client";
import { Question, QuestionType, SurveyDetail } from "../../api/types";

function SortableQuestion({ question }: { question: Question }) {
  const { attributes, listeners, setNodeRef, transform, transition } = useSortable({ id: question.id });
  return (
    <Card ref={setNodeRef} style={{ transform: CSS.Transform.toString(transform), transition, marginBottom: 8 }} {...attributes} {...listeners}>
      <b>{question.position + 1}. {question.title}</b>
      <div>{question.type}</div>
    </Card>
  );
}

export function SurveyBuilderPage() {
  const { surveyId } = useParams();
  const [open, setOpen] = useState(false);
  const queryClient = useQueryClient();
  const { data } = useQuery({
    queryKey: ["survey-detail", surveyId],
    queryFn: () => apiRequest<SurveyDetail>(`/surveys/${surveyId}`),
    enabled: Boolean(surveyId)
  });
  const questions = useMemo(() => [...(data?.questions ?? [])].sort((a, b) => a.position - b.position), [data]);

  const createQuestion = useMutation({
    mutationFn: (payload: { title: string; type: QuestionType; is_required: boolean }) =>
      apiRequest(`/surveys/${surveyId}/questions`, {
        method: "POST",
        body: JSON.stringify({ ...payload, position: questions.length, settings: {}, options: [] })
      }),
    onSuccess: () => {
      setOpen(false);
      queryClient.invalidateQueries({ queryKey: ["survey-detail", surveyId] });
    }
  });
  const reorder = useMutation({
    mutationFn: (items: { id: string; position: number }[]) =>
      apiRequest(`/surveys/${surveyId}/questions/reorder`, { method: "POST", body: JSON.stringify({ items }) }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["survey-detail", surveyId] })
  });
  const createRule = useMutation({
    mutationFn: (payload: Record<string, unknown>) =>
      apiRequest(`/surveys/${surveyId}/rules`, { method: "POST", body: JSON.stringify(payload) }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["survey-detail", surveyId] })
  });

  function onDragEnd(event: DragEndEvent) {
    if (!event.over || event.active.id === event.over.id) return;
    const oldIndex = questions.findIndex((item) => item.id === event.active.id);
    const newIndex = questions.findIndex((item) => item.id === event.over?.id);
    const ordered = arrayMove(questions, oldIndex, newIndex).map((question, position) => ({ id: question.id, position }));
    reorder.mutate(ordered);
  }

  return (
    <>
      <div className="toolbar">
        <h2>{data?.title}</h2>
        <Button type="primary" onClick={() => setOpen(true)}>Add Question</Button>
      </div>
      <Tabs
        items={[
          {
            key: "questions",
            label: "Questions",
            children: (
              <DndContext onDragEnd={onDragEnd}>
                <SortableContext items={questions.map((item) => item.id)} strategy={verticalListSortingStrategy}>
                  {questions.map((question) => <SortableQuestion key={question.id} question={question} />)}
                </SortableContext>
              </DndContext>
            )
          },
          {
            key: "rules",
            label: "Rules",
            children: (
              <Space direction="vertical" style={{ width: "100%" }}>
                {(data?.rules ?? []).map((rule) => <Card key={rule.id}>{rule.name}</Card>)}
                <Form
                  layout="vertical"
                  onFinish={(values) =>
                    createRule.mutate({
                      ...values,
                      priority: Number(values.priority ?? 100),
                      condition: { op: "AND", conditions: [{ field: values.field, operator: values.operator, value: values.value }] }
                    })
                  }
                >
                  <Form.Item name="name" label="Name" rules={[{ required: true }]}><Input /></Form.Item>
                  <Form.Item name="target_question_id" label="Target" rules={[{ required: true }]}>
                    <Select options={questions.map((q) => ({ label: q.title, value: q.id }))} />
                  </Form.Item>
                  <Form.Item name="action" label="Action" initialValue="SHOW_QUESTION"><Select options={[{ value: "SHOW_QUESTION" }, { value: "HIDE_QUESTION" }]} /></Form.Item>
                  <Form.Item name="field" label="Field"><Input placeholder="user.position" /></Form.Item>
                  <Form.Item name="operator" label="Operator" initialValue="equals"><Select options={[{ value: "equals" }, { value: "lte" }, { value: "gte" }, { value: "in" }]} /></Form.Item>
                  <Form.Item name="value" label="Value"><Input /></Form.Item>
                  <Button htmlType="submit">Add rule</Button>
                </Form>
              </Space>
            )
          }
        ]}
      />
      <Modal title="Add question" open={open} onCancel={() => setOpen(false)} footer={null}>
        <Form layout="vertical" onFinish={(values) => createQuestion.mutate(values)}>
          <Form.Item name="title" label="Title" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="type" label="Type" initialValue="TEXT">
            <Select options={["SINGLE_CHOICE", "MULTIPLE_CHOICE", "RATING", "TEXT", "MATRIX"].map((value) => ({ value }))} />
          </Form.Item>
          <Form.Item name="is_required" label="Required" valuePropName="checked" initialValue><Switch /></Form.Item>
          <Button type="primary" htmlType="submit">Add</Button>
        </Form>
      </Modal>
    </>
  );
}


```

## frontend/src/pages/hr/SurveyManagementPage.tsx

```tsx
import { PlusOutlined } from "@ant-design/icons";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Button, Form, Input, Modal, Space, Table, Tag } from "antd";
import { useState } from "react";
import { Link } from "react-router-dom";
import { apiRequest } from "../../api/client";
import { Survey } from "../../api/types";

export function SurveyManagementPage() {
  const [open, setOpen] = useState(false);
  const queryClient = useQueryClient();
  const { data = [] } = useQuery({ queryKey: ["surveys"], queryFn: () => apiRequest<Survey[]>("/surveys") });
  const create = useMutation({
    mutationFn: (payload: Partial<Survey>) => apiRequest("/surveys", { method: "POST", body: JSON.stringify(payload) }),
    onSuccess: () => {
      setOpen(false);
      queryClient.invalidateQueries({ queryKey: ["surveys"] });
    }
  });
  const action = useMutation({
    mutationFn: ({ id, name }: { id: string; name: string }) => apiRequest(`/surveys/${id}/${name}`, { method: "POST" }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["surveys"] })
  });

  return (
    <>
      <div className="toolbar">
        <h2>Survey Management</h2>
        <Button icon={<PlusOutlined />} type="primary" onClick={() => setOpen(true)}>Create</Button>
      </div>
      <Table
        rowKey="id"
        dataSource={data}
        columns={[
          { title: "Title", dataIndex: "title" },
          { title: "Status", dataIndex: "status", render: (surveyStatus: Survey["status"]) => <Tag>{surveyStatus}</Tag> },
          { title: "Anonymous", dataIndex: "is_anonymous", render: (value) => (value ? "Yes" : "No") },
          {
            title: "Actions",
            render: (_value: unknown, record: Survey) => (
              <Space>
                <Link to={`/hr/surveys/${record.id}/builder`}>Builder</Link>
                <Button size="small" onClick={() => action.mutate({ id: record.id, name: "publish" })}>Publish</Button>
                <Button size="small" onClick={() => action.mutate({ id: record.id, name: "close" })}>Close</Button>
                <Button size="small" onClick={() => action.mutate({ id: record.id, name: "archive" })}>Archive</Button>
              </Space>
            )
          }
        ]}
      />
      <Modal title="Create survey" open={open} onCancel={() => setOpen(false)} footer={null}>
        <Form layout="vertical" onFinish={(values) => create.mutate(values)}>
          <Form.Item name="title" label="Title" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="description" label="Description"><Input.TextArea /></Form.Item>
          <Form.Item name="estimated_minutes" label="Minutes" initialValue={5}><Input type="number" /></Form.Item>
          <Button type="primary" htmlType="submit">Create</Button>
        </Form>
      </Modal>
    </>
  );
}

```

## frontend/src/router/AppRouter.tsx

```tsx
import { BarChartOutlined, BellOutlined, FormOutlined, HomeOutlined, LogoutOutlined } from "@ant-design/icons";
import { Button, Layout, Menu } from "antd";
import { BrowserRouter, Link, Navigate, Route, Routes, useNavigate } from "react-router-dom";
import { LoginPage } from "../pages/LoginPage";
import { AnalyticsPage } from "../pages/hr/AnalyticsPage";
import { HrDashboardPage } from "../pages/hr/HrDashboardPage";
import { SurveyBuilderPage } from "../pages/hr/SurveyBuilderPage";
import { SurveyManagementPage } from "../pages/hr/SurveyManagementPage";
import { EmployeeDashboardPage } from "../pages/employee/EmployeeDashboardPage";
import { NotificationSettingsPage } from "../pages/employee/NotificationSettingsPage";
import { SurveyListPage } from "../pages/employee/SurveyListPage";
import { SurveyPassPage } from "../pages/employee/SurveyPassPage";
import { useAuthStore } from "../stores/authStore";

function Shell() {
  const navigate = useNavigate();
  const { accessToken, logout } = useAuthStore();

  if (!accessToken) {
    return <Navigate to="/login" replace />;
  }

  return (
    <Layout className="app-shell">
      <Layout.Sider width={240}>
        <Menu
          theme="dark"
          mode="inline"
          defaultSelectedKeys={["employee-dashboard"]}
          items={[
            { key: "employee-dashboard", icon: <HomeOutlined />, label: <Link to="/employee">Dashboard</Link> },
            { key: "employee-surveys", icon: <FormOutlined />, label: <Link to="/employee/surveys">Surveys</Link> },
            { key: "notifications", icon: <BellOutlined />, label: <Link to="/notifications">Notifications</Link> },
            { key: "hr-dashboard", icon: <BarChartOutlined />, label: <Link to="/hr">HR Dashboard</Link> },
            { key: "hr-surveys", icon: <FormOutlined />, label: <Link to="/hr/surveys">Survey Management</Link> },
            { key: "analytics", icon: <BarChartOutlined />, label: <Link to="/hr/analytics">Analytics</Link> }
          ]}
        />
      </Layout.Sider>
      <Layout>
        <Layout.Header style={{ display: "flex", justifyContent: "flex-end", background: "#fff" }}>
          <Button
            icon={<LogoutOutlined />}
            onClick={() => {
              logout();
              navigate("/login");
            }}
          />
        </Layout.Header>
        <Layout.Content className="content">
          <Routes>
            <Route path="/employee" element={<EmployeeDashboardPage />} />
            <Route path="/employee/surveys" element={<SurveyListPage />} />
            <Route path="/employee/surveys/:surveyId" element={<SurveyPassPage />} />
            <Route path="/notifications" element={<NotificationSettingsPage />} />
            <Route path="/hr" element={<HrDashboardPage />} />
            <Route path="/hr/surveys" element={<SurveyManagementPage />} />
            <Route path="/hr/surveys/:surveyId/builder" element={<SurveyBuilderPage />} />
            <Route path="/hr/analytics" element={<AnalyticsPage />} />
            <Route path="*" element={<Navigate to="/employee" replace />} />
          </Routes>
        </Layout.Content>
      </Layout>
    </Layout>
  );
}

export function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/*" element={<Shell />} />
      </Routes>
    </BrowserRouter>
  );
}


```

## frontend/src/stores/authStore.ts

```ts
import { create } from "zustand";
import { persist } from "zustand/middleware";

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  setTokens: (accessToken: string, refreshToken: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      setTokens: (accessToken, refreshToken) => set({ accessToken, refreshToken }),
      logout: () => set({ accessToken: null, refreshToken: null })
    }),
    { name: "pulsehr-auth" }
  )
);


```

## frontend/src/styles.css

```css
body {
  margin: 0;
  background: #f5f7fb;
}

.app-shell {
  min-height: 100vh;
}

.content {
  padding: 24px;
}

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 16px;
}

.question-row {
  margin-bottom: 16px;
}


```

## frontend/src/vite-env.d.ts

```ts
/// <reference types="vite/client" />


```

## frontend/tsconfig.json

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "useDefineForClassFields": true,
    "lib": ["DOM", "DOM.Iterable", "ES2022"],
    "allowJs": false,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "module": "ESNext",
    "moduleResolution": "Node",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx"
  },
  "include": ["src"],
  "references": []
}


```

## frontend/vite.config.ts

```ts
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://localhost:8000",
      "/auth": "http://localhost:8000",
      "/users": "http://localhost:8000",
      "/surveys": "http://localhost:8000",
      "/employee": "http://localhost:8000",
      "/responses": "http://localhost:8000",
      "/analytics": "http://localhost:8000",
      "/notifications": "http://localhost:8000",
      "/exports": "http://localhost:8000"
    }
  }
});


```

## pyproject.toml

```toml
[project]
name = "pulsehr-backend"
version = "0.1.0"
description = "PulseHR backend MVP"
requires-python = ">=3.12"
dependencies = [
    "alembic==1.13.3",
    "asyncpg==0.29.0",
    "fastapi==0.115.0",
    "greenlet==3.1.1",
    "openpyxl==3.1.5",
    "pydantic==2.9.2",
    "pydantic-settings==2.5.2",
    "pyjwt==2.9.0",
    "python-dotenv==1.0.1",
    "redis==5.0.8",
    "sqlalchemy==2.0.35",
    "uvicorn[standard]==0.30.6"
]

[project.optional-dependencies]
dev = [
    "ruff==0.6.8"
]

[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]

```

## requirements.txt

```text
alembic==1.13.3
asyncpg==0.29.0
fastapi==0.115.0
greenlet==3.1.1
openpyxl==3.1.5
pydantic==2.9.2
pydantic-settings==2.5.2
pyjwt==2.9.0
python-dotenv==1.0.1
redis==5.0.8
sqlalchemy==2.0.35
uvicorn[standard]==0.30.6

```
