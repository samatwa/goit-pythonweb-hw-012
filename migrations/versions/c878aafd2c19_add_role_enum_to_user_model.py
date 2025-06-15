from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "c878aafd2c19"
down_revision: Union[str, None] = "62ecc938a1a1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

userrole_enum = sa.Enum("ADMIN", "USER", name="userrole")


def upgrade() -> None:
    userrole_enum.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "users",
        sa.Column(
            "confirmed", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
    )
    op.add_column(
        "users", sa.Column("role", userrole_enum, nullable=False, server_default="USER")
    )
    op.drop_column("users", "is_verified")


def downgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "is_verified",
            sa.BOOLEAN(),
            autoincrement=False,
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.drop_column("users", "role")
    op.drop_column("users", "confirmed")

    userrole_enum.drop(op.get_bind(), checkfirst=True)
