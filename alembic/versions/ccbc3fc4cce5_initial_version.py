"""Initial version

Revision ID: ccbc3fc4cce5
Revises: 
Create Date: 2022-08-29 11:21:07.831658

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "ccbc3fc4cce5"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "oauth2_client",
        sa.Column("client_id", sa.String(length=48), nullable=True),
        sa.Column("client_secret", sa.String(length=120), nullable=True),
        sa.Column("client_id_issued_at", sa.Integer(), nullable=False),
        sa.Column("client_secret_expires_at", sa.Integer(), nullable=False),
        sa.Column("client_metadata", sa.Text(), nullable=True),
        sa.Column("id", sa.INTEGER(), nullable=False),
        sa.Column("user_id", sa.Unicode(length=80), nullable=True),
        sa.Column("client_uri", sa.Unicode(length=255), nullable=True),
        sa.Column("client_name", sa.Unicode(length=120), nullable=True),
        sa.Column("client_logo_file", sa.Unicode(length=64), nullable=True),
        sa.Column("client_logo_mimetype", sa.Unicode(length=120), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.user_name"],
            name=op.f("fk_oauth2_client_user_id_user"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_oauth2_client")),
        sa.UniqueConstraint("client_uri", name=op.f("uq_oauth2_client_client_uri")),
    )
    op.create_index(
        op.f("ix_oauth2_client_client_id"), "oauth2_client", ["client_id"], unique=False
    )
    op.create_table(
        "oauth2_code",
        sa.Column("code", sa.String(length=120), nullable=False),
        sa.Column("client_id", sa.String(length=48), nullable=True),
        sa.Column("redirect_uri", sa.Text(), nullable=True),
        sa.Column("response_type", sa.Text(), nullable=True),
        sa.Column("scope", sa.Text(), nullable=True),
        sa.Column("nonce", sa.Text(), nullable=True),
        sa.Column("auth_time", sa.Integer(), nullable=False),
        sa.Column("code_challenge", sa.Text(), nullable=True),
        sa.Column("code_challenge_method", sa.String(length=48), nullable=True),
        sa.Column("id", sa.INTEGER(), nullable=False),
        sa.Column("user_id", sa.Unicode(length=80), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.user_name"],
            name=op.f("fk_oauth2_code_user_id_user"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_oauth2_code")),
        sa.UniqueConstraint("code", name=op.f("uq_oauth2_code_code")),
    )
    op.create_table(
        "oauth2_token",
        sa.Column("client_id", sa.String(length=48), nullable=True),
        sa.Column("token_type", sa.String(length=40), nullable=True),
        sa.Column("access_token", sa.String(length=255), nullable=False),
        sa.Column("refresh_token", sa.String(length=255), nullable=True),
        sa.Column("scope", sa.Text(), nullable=True),
        sa.Column("revoked", sa.Boolean(), nullable=True),
        sa.Column("issued_at", sa.Integer(), nullable=False),
        sa.Column("expires_in", sa.Integer(), nullable=False),
        sa.Column("id", sa.INTEGER(), nullable=False),
        sa.Column("user_id", sa.Unicode(length=80), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.user_name"],
            name=op.f("fk_oauth2_token_user_id_user"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_oauth2_token")),
        sa.UniqueConstraint("access_token", name=op.f("uq_oauth2_token_access_token")),
    )
    op.create_index(
        op.f("ix_oauth2_token_refresh_token"),
        "oauth2_token",
        ["refresh_token"],
        unique=False,
    )


def downgrade():
    op.drop_table("oauth2_token")
    op.drop_table("oauth2_code")
    op.drop_table("oauth2_client")
