# PulseHR Backend MVP

PulseHR is a FastAPI backend for corporate employee surveys with OTP login, JWT auth,
roles, anonymous survey responses, analytics, notifications, and CSV/XLSX exports.

## Stack

- Python 3.12
- FastAPI
- SQLAlchemy 2.0 Async
- SQLAdmin
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

Admin panel:

```text
http://localhost:8000/admin
```

The SQLAdmin panel uses the same OTP flow as the API. Request an OTP for an existing
HR user, then log in to `/admin` with the phone as the username and OTP as the password.

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

`POST /notifications/send` creates the notification and due delivery records only.
`app.workers.notification_worker` sends due records through configured Telegram,
Email, and SMS providers. Delivery scheduling is database-backed, supports ordered
channel escalation/cascading, and cancels remaining survey reminders when the
employee has already submitted the survey.

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
