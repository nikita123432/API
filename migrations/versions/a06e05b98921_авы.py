"""авы

Revision ID: a06e05b98921
Revises: 4c9b4e3a048c
Create Date: 2025-06-20 16:15:17.821603

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a06e05b98921'
down_revision: Union[str, None] = '4c9b4e3a048c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
