"""
Shared fixtures for meal_planning integration tests.
"""
import pytest
from uuid import uuid4
from unittest.mock import MagicMock, AsyncMock

from src.meal_planning.application.service import MealPlanService
from src.meal_planning.domain.entities import (
    PlanPreferences,
)


# Re-export factory functions from unit conftest
from tests.unit.meal_planning.conftest import (
    make_meal,
    make_user_data,
    make_template,
)


@pytest.fixture
def mock_repo():
    """Async mock repository."""
    repo = AsyncMock()
    repo.create_plan = AsyncMock(return_value=uuid4())
    repo.get_plan = AsyncMock(return_value=None)
    repo.delete_plan = AsyncMock(return_value=True)
    repo.update_status = AsyncMock(return_value=True)
    repo.list_plans = AsyncMock(return_value=[])
    repo.commit = AsyncMock()
    return repo


@pytest.fixture
def mock_planner():
    """Async mock planner implementing MealPlannerPort."""
    planner = AsyncMock()

    # Default: return 1 day with 1 breakfast template
    planner.generate_meal_templates = AsyncMock(
        return_value=[[make_template()]]
    )

    # Default: return a meal with one ingredient
    planner.generate_meal = AsyncMock(
        return_value=make_meal()
    )

    # Default: return days unchanged
    planner.optimize_plan = AsyncMock(
        side_effect=lambda days, profile: days
    )
    return planner


@pytest.fixture
def mock_food_search():
    """Async mock food search."""
    search = AsyncMock()
    search.search_for_meal_planning = AsyncMock(return_value=[])
    search.find_product_by_name = AsyncMock(return_value=None)
    return search


@pytest.fixture
def mock_session():
    """Mock database session."""
    return MagicMock()


@pytest.fixture
def full_service(mock_repo, mock_planner, mock_food_search, mock_session):
    """MealPlanService with all mocked dependencies."""
    return MealPlanService(
        repository=mock_repo,
        planner=mock_planner,
        food_search=mock_food_search,
        session=mock_session,
    )


@pytest.fixture
def user_data():
    """Default test user data."""
    return make_user_data()


@pytest.fixture
def preferences():
    """Default test preferences."""
    return PlanPreferences()
