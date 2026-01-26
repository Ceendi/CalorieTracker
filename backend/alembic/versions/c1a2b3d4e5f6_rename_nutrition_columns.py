"""rename nutrition columns for consistency

Revision ID: c1a2b3d4e5f6
Revises: bf4f39d54fa7
Create Date: 2026-01-26 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'c1a2b3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'bf4f39d54fa7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Rename nutrition columns for consistency across codebase."""
    # Rename prot_per_100g -> protein_per_100g
    op.alter_column(
        'tracking_meal_entries',
        'prot_per_100g',
        new_column_name='protein_per_100g'
    )

    # Rename carb_per_100g -> carbs_per_100g
    op.alter_column(
        'tracking_meal_entries',
        'carb_per_100g',
        new_column_name='carbs_per_100g'
    )


def downgrade() -> None:
    """Revert column renames."""
    # Rename protein_per_100g -> prot_per_100g
    op.alter_column(
        'tracking_meal_entries',
        'protein_per_100g',
        new_column_name='prot_per_100g'
    )

    # Rename carbs_per_100g -> carb_per_100g
    op.alter_column(
        'tracking_meal_entries',
        'carbs_per_100g',
        new_column_name='carb_per_100g'
    )
