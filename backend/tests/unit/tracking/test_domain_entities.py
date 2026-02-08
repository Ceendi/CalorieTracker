import pytest
from uuid import uuid4
from datetime import date
from src.tracking.domain.entities import MealEntry, MealType, DailyLog

class TestMealEntry:
    def test_meal_entry_initialization_success(self):
        entry = MealEntry(
            id=uuid4(),
            daily_log_id=uuid4(),
            meal_type=MealType.BREAKFAST,
            product_name="Test Product",
            amount_grams=100,
            kcal_per_100g=100,
            protein_per_100g=10,
            fat_per_100g=5,
            carbs_per_100g=15
        )
        assert entry.amount_grams == 100
        assert entry.product_name == "Test Product"

    def test_meal_entry_computed_properties(self):
        entry = MealEntry(
            id=uuid4(),
            daily_log_id=uuid4(),
            meal_type=MealType.LUNCH,
            product_name="Chicken",
            amount_grams=200,  # 2x 100g
            kcal_per_100g=150,
            protein_per_100g=20,
            fat_per_100g=5,
            carbs_per_100g=2
        )
        # Expected: values * 2
        assert entry.computed_kcal == 300
        assert entry.computed_protein == 40.0
        assert entry.computed_fat == 10.0
        assert entry.computed_carbs == 4.0

    def test_meal_entry_validation_negative_values(self):
        base_kwargs = {
            "id": uuid4(),
            "daily_log_id": uuid4(),
            "meal_type": MealType.DINNER,
            "product_name": "Bad Data",
            "amount_grams": 100,
            "kcal_per_100g": 100,
            "protein_per_100g": 10,
            "fat_per_100g": 10,
            "carbs_per_100g": 10
        }

        with pytest.raises(ValueError, match="amount_grams cannot be negative"):
            MealEntry(**{**base_kwargs, "amount_grams": -1})

        with pytest.raises(ValueError, match="kcal_per_100g cannot be negative"):
            MealEntry(**{**base_kwargs, "kcal_per_100g": -5})

        with pytest.raises(ValueError, match="protein_per_100g cannot be negative"):
            MealEntry(**{**base_kwargs, "protein_per_100g": -1})

        with pytest.raises(ValueError, match="fat_per_100g cannot be negative"):
            MealEntry(**{**base_kwargs, "fat_per_100g": -1})

        with pytest.raises(ValueError, match="carbs_per_100g cannot be negative"):
            MealEntry(**{**base_kwargs, "carbs_per_100g": -1})

    def test_meal_entry_validation_empty_name(self):
        with pytest.raises(ValueError, match="product_name cannot be empty"):
            MealEntry(
                id=uuid4(),
                daily_log_id=uuid4(),
                meal_type=MealType.SNACK,
                product_name="",
                amount_grams=50,
                kcal_per_100g=50,
                protein_per_100g=1,
                fat_per_100g=1,
                carbs_per_100g=1
            )


class TestDailyLog:
    def test_daily_log_totals(self):
        entry1 = MealEntry(
            id=uuid4(), daily_log_id=uuid4(), meal_type=MealType.BREAKFAST,
            product_name="Egg", amount_grams=100,
            kcal_per_100g=150, protein_per_100g=13, fat_per_100g=11, carbs_per_100g=1
        )
        entry2 = MealEntry(
            id=uuid4(), daily_log_id=uuid4(), meal_type=MealType.LUNCH,
            product_name="Rice", amount_grams=200,
            kcal_per_100g=130, protein_per_100g=2, fat_per_100g=0, carbs_per_100g=28
        )
        
        # entry1: 150 kcal, 13p, 11f, 1c
        # entry2 (200g): 260 kcal, 4p, 0f, 56c
        # Total: 410 kcal, 17p, 11f, 57c

        log = DailyLog(
            id=uuid4(),
            user_id=uuid4(),
            date=date.today(),
            entries=[entry1, entry2]
        )

        assert log.total_kcal == 410
        assert log.total_protein == 17.0
        assert log.total_fat == 11.0
        assert log.total_carbs == 57.0

    def test_daily_log_empty_entries(self):
        log = DailyLog(
            id=uuid4(),
            user_id=uuid4(),
            date=date.today(),
            entries=[]
        )
        assert log.total_kcal == 0
        assert log.total_protein == 0.0
        assert log.total_fat == 0.0
        assert log.total_carbs == 0.0
