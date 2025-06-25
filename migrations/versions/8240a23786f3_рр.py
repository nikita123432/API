"""рр

Revision ID: 8240a23786f3
Revises: a06e05b98921
Create Date: 2025-06-20 16:19:09.144779

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8240a23786f3'
down_revision: Union[str, None] = 'a06e05b98921'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
