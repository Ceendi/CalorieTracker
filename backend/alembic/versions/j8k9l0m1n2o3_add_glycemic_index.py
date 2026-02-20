"""add glycemic index to foods and tracking_meal_entries

Revision ID: j8k9l0m1n2o3
Revises: i7j8k9l0m1n2
Create Date: 2026-02-20 10:00:00.000000

Adds glycemic_index column (FLOAT, nullable) to the foods table for storing
GI values sourced from scientific tables. Adds gi_per_100g snapshot column
to tracking_meal_entries following the existing denormalization pattern
(kcal_per_100g, protein_per_100g, etc.) for historical accuracy.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = 'j8k9l0m1n2o3'
down_revision: Union[str, Sequence[str], None] = 'i7j8k9l0m1n2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('foods', sa.Column('glycemic_index', sa.Float(), nullable=True))
    op.add_column('tracking_meal_entries', sa.Column('gi_per_100g', sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column('tracking_meal_entries', 'gi_per_100g')
    op.drop_column('foods', 'glycemic_index')
