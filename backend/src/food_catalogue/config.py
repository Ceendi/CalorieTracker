from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class FoodCatalogueSettings(BaseSettings):
    OFF_BASE_URL: str = Field("https://world.openfoodfacts.org/api/v0", description="API Base URL")
    OFF_SEARCH_URL: str = Field("https://world.openfoodfacts.org/cgi/search.pl", description="Search URL")
    OFF_USER_AGENT: str = Field("CalorieTracker/1.0 (contact@example.com)", description="User Agent for OFF")
    OFF_TIMEOUT_SEC: float = Field(10.0, description="HTTP Timeout")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_prefix="FOOD_"
    )


settings = FoodCatalogueSettings()
