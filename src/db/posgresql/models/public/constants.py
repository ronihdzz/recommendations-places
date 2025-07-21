from enum import StrEnum

class PlaceCategory(StrEnum):
    BAR = "bar"
    LUGAR_TRABAJAR = "lugar-trabajar"
    LUGAR_ESTUDIAR = "lugar-estudiar"
    RESTAURANTE = "restaurante"
    CAFETERIA = "cafeteria"
    BIBLIOTECA = "biblioteca"
    GIMNASIO = "gimnasio"
    DEPORTIVO = "deportivo"
    PUBLICO = "publico"
    PATRIMONIO = "patrimonio"
    HOTEL = "hotel"
    TEATRO = "teatro"
    MUSEO = "museo"
    ZOOLOGICO = "zoologico"
    ACUARIO = "acuario"
    CONCIERTO = "concierto"
    MOTEL = "motel"
    COWORKING = "coworking"
    WORKCAFE = "workcafe"

class PriceLevel(StrEnum):
    LOW = "$"
    MEDIUM = "$$"
    HIGH = "$$$"
