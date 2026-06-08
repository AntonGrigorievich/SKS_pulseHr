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
