"""empty message

Revision ID: 130f3559bfe7
Revises: c9061cd185c7
Create Date: 2025-03-19 17:08:08.222324

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '130f3559bfe7'
down_revision: Union[str, None] = 'c9061cd185c7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('books_slug_key', 'books', type_='unique')
    op.create_unique_constraint(None, 'books', ['title'])
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'books', type_='unique')
    op.create_unique_constraint('books_slug_key', 'books', ['slug'])
    # ### end Alembic commands ###
