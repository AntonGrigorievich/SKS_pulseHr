"""add notification queue metadata

Revision ID: 20260609_0003
Revises: 20260608_0002
Create Date: 2026-06-09 00:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260609_0003"
down_revision = "20260608_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE delivery_status ADD VALUE IF NOT EXISTS 'SENDING'")
        op.execute("ALTER TYPE delivery_status ADD VALUE IF NOT EXISTS 'SKIPPED'")
        op.execute("ALTER TYPE delivery_status ADD VALUE IF NOT EXISTS 'CANCELLED'")

    op.add_column(
        "notifications",
        sa.Column("stop_on_success", sa.Boolean(), server_default=sa.text("true"), nullable=False),
    )
    op.add_column(
        "notifications",
        sa.Column(
            "step_delay_seconds",
            sa.Integer(),
            server_default=sa.text("900"),
            nullable=False,
        ),
    )

    op.add_column(
        "notification_deliveries",
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "notification_deliveries",
        sa.Column("attempt_order", sa.Integer(), nullable=True),
    )
    op.add_column(
        "notification_deliveries",
        sa.Column("destination", sa.String(length=512), nullable=True),
    )
    op.add_column(
        "notification_deliveries",
        sa.Column("provider_message_id", sa.String(length=255), nullable=True),
    )

    op.execute(
        """
        UPDATE notification_deliveries
        SET scheduled_at = COALESCE(sent_at, created_at, now())
        WHERE scheduled_at IS NULL
        """
    )
    op.execute("UPDATE notification_deliveries SET attempt_order = 1 WHERE attempt_order IS NULL")
    op.execute("UPDATE notification_deliveries SET destination = '' WHERE destination IS NULL")

    op.alter_column("notification_deliveries", "scheduled_at", nullable=False)
    op.alter_column("notification_deliveries", "attempt_order", nullable=False)
    op.alter_column("notification_deliveries", "destination", nullable=False)

    op.create_index(
        "ix_notification_deliveries_status_scheduled_at",
        "notification_deliveries",
        ["status", "scheduled_at"],
    )
    op.create_index(
        "ix_notification_deliveries_notification_user_status",
        "notification_deliveries",
        ["notification_id", "user_id", "status"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_notification_deliveries_notification_user_status",
        table_name="notification_deliveries",
    )
    op.drop_index(
        "ix_notification_deliveries_status_scheduled_at",
        table_name="notification_deliveries",
    )

    op.execute(
        """
        UPDATE notification_deliveries
        SET status = 'FAILED'
        WHERE status IN ('SENDING', 'SKIPPED', 'CANCELLED')
        """
    )
    op.execute("ALTER TABLE notification_deliveries ALTER COLUMN status DROP DEFAULT")
    op.execute("ALTER TYPE delivery_status RENAME TO delivery_status_old")
    op.execute("CREATE TYPE delivery_status AS ENUM ('PENDING', 'SENT', 'FAILED')")
    op.execute(
        """
        ALTER TABLE notification_deliveries
        ALTER COLUMN status TYPE delivery_status
        USING status::text::delivery_status
        """
    )
    op.execute("ALTER TABLE notification_deliveries ALTER COLUMN status SET DEFAULT 'PENDING'")
    op.execute("DROP TYPE delivery_status_old")

    op.drop_column("notification_deliveries", "provider_message_id")
    op.drop_column("notification_deliveries", "destination")
    op.drop_column("notification_deliveries", "attempt_order")
    op.drop_column("notification_deliveries", "scheduled_at")

    op.drop_column("notifications", "step_delay_seconds")
    op.drop_column("notifications", "stop_on_success")
