"""add_meal_planning_tables

Revision ID: d2e3f4a5b6c7
Revises: c1a2b3d4e5f6
Create Date: 2026-01-27 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'd2e3f4a5b6c7'
down_revision: Union[str, Sequence[str], None] = 'c1a2b3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create meal planning tables."""
    # meal_plans - main plan table
    op.create_table(
        'meal_plans',
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('preferences', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('daily_targets', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='draft'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_meal_plans_id'), 'meal_plans', ['id'], unique=False)
    op.create_index(op.f('ix_meal_plans_user_id'), 'meal_plans', ['user_id'], unique=False)
    op.create_index(op.f('ix_meal_plans_status'), 'meal_plans', ['status'], unique=False)

    # meal_plan_days - days within a plan
    op.create_table(
        'meal_plan_days',
        sa.Column('meal_plan_id', sa.Uuid(), nullable=False),
        sa.Column('day_number', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(['meal_plan_id'], ['meal_plans.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('meal_plan_id', 'day_number', name='uix_meal_plan_day_number'),
        sa.CheckConstraint('day_number >= 1', name='check_day_number_positive')
    )
    op.create_index(op.f('ix_meal_plan_days_id'), 'meal_plan_days', ['id'], unique=False)
    op.create_index(op.f('ix_meal_plan_days_meal_plan_id'), 'meal_plan_days', ['meal_plan_id'], unique=False)

    # meal_plan_meals - individual meals within a day
    op.create_table(
        'meal_plan_meals',
        sa.Column('meal_plan_day_id', sa.Uuid(), nullable=False),
        sa.Column('meal_type', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('preparation_time_minutes', sa.Integer(), nullable=True),
        sa.Column('total_kcal', sa.Float(), nullable=True),
        sa.Column('total_protein', sa.Float(), nullable=True),
        sa.Column('total_fat', sa.Float(), nullable=True),
        sa.Column('total_carbs', sa.Float(), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(['meal_plan_day_id'], ['meal_plan_days.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_meal_plan_meals_id'), 'meal_plan_meals', ['id'], unique=False)
    op.create_index(op.f('ix_meal_plan_meals_meal_plan_day_id'), 'meal_plan_meals', ['meal_plan_day_id'], unique=False)

    # meal_plan_ingredients - ingredients within a meal
    op.create_table(
        'meal_plan_ingredients',
        sa.Column('meal_plan_meal_id', sa.Uuid(), nullable=False),
        sa.Column('food_id', sa.Uuid(), nullable=True),
        sa.Column('custom_name', sa.String(length=255), nullable=True),
        sa.Column('amount_grams', sa.Float(), nullable=False),
        sa.Column('unit_label', sa.String(length=50), nullable=True),
        sa.Column('kcal', sa.Float(), nullable=True),
        sa.Column('protein', sa.Float(), nullable=True),
        sa.Column('fat', sa.Float(), nullable=True),
        sa.Column('carbs', sa.Float(), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(['food_id'], ['foods.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['meal_plan_meal_id'], ['meal_plan_meals.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_meal_plan_ingredients_id'), 'meal_plan_ingredients', ['id'], unique=False)
    op.create_index(op.f('ix_meal_plan_ingredients_meal_plan_meal_id'), 'meal_plan_ingredients', ['meal_plan_meal_id'], unique=False)
    op.create_index(op.f('ix_meal_plan_ingredients_food_id'), 'meal_plan_ingredients', ['food_id'], unique=False)


def downgrade() -> None:
    """Drop meal planning tables."""
    op.drop_index(op.f('ix_meal_plan_ingredients_food_id'), table_name='meal_plan_ingredients')
    op.drop_index(op.f('ix_meal_plan_ingredients_meal_plan_meal_id'), table_name='meal_plan_ingredients')
    op.drop_index(op.f('ix_meal_plan_ingredients_id'), table_name='meal_plan_ingredients')
    op.drop_table('meal_plan_ingredients')

    op.drop_index(op.f('ix_meal_plan_meals_meal_plan_day_id'), table_name='meal_plan_meals')
    op.drop_index(op.f('ix_meal_plan_meals_id'), table_name='meal_plan_meals')
    op.drop_table('meal_plan_meals')

    op.drop_index(op.f('ix_meal_plan_days_meal_plan_id'), table_name='meal_plan_days')
    op.drop_index(op.f('ix_meal_plan_days_id'), table_name='meal_plan_days')
    op.drop_table('meal_plan_days')

    op.drop_index(op.f('ix_meal_plans_status'), table_name='meal_plans')
    op.drop_index(op.f('ix_meal_plans_user_id'), table_name='meal_plans')
    op.drop_index(op.f('ix_meal_plans_id'), table_name='meal_plans')
    op.drop_table('meal_plans')
