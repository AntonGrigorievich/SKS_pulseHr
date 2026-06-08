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

