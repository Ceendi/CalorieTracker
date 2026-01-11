class TrackingError(Exception):
    pass


class ProductNotFoundInTrackingError(TrackingError):
    def __init__(self, product_id: str):
        self.message = f"Product with id {product_id} not found"
        super().__init__(self.message)


class MealEntryNotFoundError(TrackingError):
    def __init__(self, entry_id: str):
        self.message = f"Meal entry {entry_id} not found"
        super().__init__(self.message)
