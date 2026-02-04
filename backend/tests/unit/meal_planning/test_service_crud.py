"""
Unit tests for MealPlanService CRUD methods with authorization checks.

Tests get_plan, delete_plan, update_plan_status, save_plan, list_plans.
Focuses on verifying authorization is enforced and cannot be bypassed.
"""
import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

from src.meal_planning.application.service import MealPlanService
from tests.unit.meal_planning.conftest import make_plan


@pytest.fixture
def user_id():
    return uuid4()


@pytest.fixture
def other_user_id():
    return uuid4()


@pytest.fixture
def mock_repo():
    repo = AsyncMock()
    repo.commit = AsyncMock()
    return repo


@pytest.fixture
def service(mock_repo):
    return MealPlanService(repository=mock_repo)


def _make_plan_model(user_id):
    """Create a mock plan ORM model with user_id."""
    plan = MagicMock()
    plan.user_id = user_id
    return plan


# ---------------------------------------------------------------------------
# get_plan authorization
# ---------------------------------------------------------------------------

class TestGetPlanAuthorization:
    """Tests for get_plan authorization check."""

    @pytest.mark.asyncio
    async def test_returns_plan_when_user_matches(self, service, mock_repo, user_id):
        mock_plan = _make_plan_model(user_id)
        mock_repo.get_plan = AsyncMock(return_value=mock_plan)

        result = await service.get_plan(uuid4(), user_id)

        assert result is mock_plan

    @pytest.mark.asyncio
    async def test_returns_none_when_user_does_not_match(self, service, mock_repo, user_id, other_user_id):
        mock_plan = _make_plan_model(user_id)
        mock_repo.get_plan = AsyncMock(return_value=mock_plan)

        result = await service.get_plan(uuid4(), other_user_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_when_plan_not_found(self, service, mock_repo, user_id):
        mock_repo.get_plan = AsyncMock(return_value=None)

        result = await service.get_plan(uuid4(), user_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_does_not_call_commit(self, service, mock_repo, user_id):
        mock_plan = _make_plan_model(user_id)
        mock_repo.get_plan = AsyncMock(return_value=mock_plan)

        await service.get_plan(uuid4(), user_id)

        mock_repo.commit.assert_not_called()


# ---------------------------------------------------------------------------
# delete_plan authorization
# ---------------------------------------------------------------------------

class TestDeletePlanAuthorization:
    """Tests for delete_plan authorization check."""

    @pytest.mark.asyncio
    async def test_deletes_when_user_matches(self, service, mock_repo, user_id):
        plan_id = uuid4()
        mock_plan = _make_plan_model(user_id)
        mock_repo.get_plan = AsyncMock(return_value=mock_plan)
        mock_repo.delete_plan = AsyncMock(return_value=True)

        result = await service.delete_plan(plan_id, user_id)

        assert result is True
        mock_repo.delete_plan.assert_called_once_with(plan_id)
        mock_repo.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_false_when_user_does_not_match(self, service, mock_repo, user_id, other_user_id):
        mock_plan = _make_plan_model(user_id)
        mock_repo.get_plan = AsyncMock(return_value=mock_plan)
        mock_repo.delete_plan = AsyncMock()

        result = await service.delete_plan(uuid4(), other_user_id)

        assert result is False
        mock_repo.delete_plan.assert_not_called()

    @pytest.mark.asyncio
    async def test_returns_false_when_plan_not_found(self, service, mock_repo, user_id):
        mock_repo.get_plan = AsyncMock(return_value=None)

        result = await service.delete_plan(uuid4(), user_id)

        assert result is False

    @pytest.mark.asyncio
    async def test_commits_after_successful_delete(self, service, mock_repo, user_id):
        mock_plan = _make_plan_model(user_id)
        mock_repo.get_plan = AsyncMock(return_value=mock_plan)
        mock_repo.delete_plan = AsyncMock(return_value=True)

        await service.delete_plan(uuid4(), user_id)

        mock_repo.commit.assert_called_once()


# ---------------------------------------------------------------------------
# update_plan_status authorization
# ---------------------------------------------------------------------------

class TestUpdatePlanStatusAuthorization:
    """Tests for update_plan_status authorization check."""

    @pytest.mark.asyncio
    async def test_updates_when_user_matches(self, service, mock_repo, user_id):
        plan_id = uuid4()
        mock_plan = _make_plan_model(user_id)
        mock_repo.get_plan = AsyncMock(return_value=mock_plan)
        mock_repo.update_status = AsyncMock(return_value=True)

        result = await service.update_plan_status(plan_id, user_id, "active")

        assert result is True
        mock_repo.update_status.assert_called_once_with(plan_id, "active")

    @pytest.mark.asyncio
    async def test_returns_false_when_user_does_not_match(self, service, mock_repo, user_id, other_user_id):
        mock_plan = _make_plan_model(user_id)
        mock_repo.get_plan = AsyncMock(return_value=mock_plan)
        mock_repo.update_status = AsyncMock()

        result = await service.update_plan_status(uuid4(), other_user_id, "active")

        assert result is False
        mock_repo.update_status.assert_not_called()

    @pytest.mark.asyncio
    async def test_returns_false_when_plan_not_found(self, service, mock_repo, user_id):
        mock_repo.get_plan = AsyncMock(return_value=None)

        result = await service.update_plan_status(uuid4(), user_id, "active")

        assert result is False

    @pytest.mark.asyncio
    async def test_commits_after_successful_update(self, service, mock_repo, user_id):
        mock_plan = _make_plan_model(user_id)
        mock_repo.get_plan = AsyncMock(return_value=mock_plan)
        mock_repo.update_status = AsyncMock(return_value=True)

        await service.update_plan_status(uuid4(), user_id, "active")

        mock_repo.commit.assert_called_once()


# ---------------------------------------------------------------------------
# save_plan
# ---------------------------------------------------------------------------

class TestSavePlan:
    """Tests for save_plan."""

    @pytest.mark.asyncio
    async def test_delegates_to_repo_create_plan(self, service, mock_repo, user_id):
        from datetime import date

        plan = make_plan()
        expected_id = uuid4()
        mock_repo.create_plan = AsyncMock(return_value=expected_id)

        result = await service.save_plan(user_id, plan, "Test Plan", date(2026, 1, 1))

        mock_repo.create_plan.assert_called_once_with(user_id, plan, "Test Plan", date(2026, 1, 1))
        assert result == expected_id

    @pytest.mark.asyncio
    async def test_commits_after_save(self, service, mock_repo, user_id):
        from datetime import date

        mock_repo.create_plan = AsyncMock(return_value=uuid4())

        await service.save_plan(user_id, make_plan(), "Plan", date(2026, 1, 1))

        mock_repo.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_plan_id_from_repo(self, service, mock_repo, user_id):
        from datetime import date

        expected_id = uuid4()
        mock_repo.create_plan = AsyncMock(return_value=expected_id)

        result = await service.save_plan(user_id, make_plan(), "Plan", date(2026, 1, 1))

        assert result == expected_id


# ---------------------------------------------------------------------------
# list_plans
# ---------------------------------------------------------------------------

class TestListPlans:
    """Tests for list_plans."""

    @pytest.mark.asyncio
    async def test_delegates_to_repo_list_plans(self, service, mock_repo, user_id):
        mock_repo.list_plans = AsyncMock(return_value=["plan1", "plan2"])

        result = await service.list_plans(user_id)

        mock_repo.list_plans.assert_called_once_with(user_id, None)
        assert result == ["plan1", "plan2"]

    @pytest.mark.asyncio
    async def test_passes_status_filter(self, service, mock_repo, user_id):
        mock_repo.list_plans = AsyncMock(return_value=[])

        await service.list_plans(user_id, status="active")

        mock_repo.list_plans.assert_called_once_with(user_id, "active")

    @pytest.mark.asyncio
    async def test_passes_none_status_when_not_provided(self, service, mock_repo, user_id):
        mock_repo.list_plans = AsyncMock(return_value=[])

        await service.list_plans(user_id)

        mock_repo.list_plans.assert_called_once_with(user_id, None)
