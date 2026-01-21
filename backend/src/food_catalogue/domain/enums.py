from enum import Enum, unique


class StrEnum(str, Enum):
    pass


@unique
class UnitType(StrEnum):
    GRAM = "gram"
    CUP = "cup"
    TABLESPOON = "tablespoon"
    TEASPOON = "teaspoon"
    PIECE = "piece"
    PORTION = "portion"


@unique
class UnitLabel(StrEnum):
    GRAM = "gram"
    SZKLANKA = "szklanka"
    LYZKA = "łyżka"
    LYZECZKA = "łyżeczka"
    SZTUKA = "sztuka"
    PORCJA = "porcja"
