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
    SZTUKA_MALA = "Sztuka (mała)"
    SZTUKA_SREDNIA = "Sztuka (średnia)"
    SZTUKA_DUZA = "Sztuka (duża)"
    PORCJA = "porcja"
    PORCJA_MALA = "Porcja (mała)"
    PORCJA_SREDNIA = "Porcja (średnia)"
    PORCJA_DUZA = "Porcja (duża)"
    KROMKA = "kromka"
    PLASTER = "plaster"
    PLASTERKI = "plasterki"
    OPAKOWANIE = "opakowanie"
    TABLICZKA = "tabliczka"
