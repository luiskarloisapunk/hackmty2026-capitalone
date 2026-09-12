# services/influencer.py
from app.services.negocio import Negocio

class Influencer(Negocio):
    def calcular_impuestos(self) -> float:
        ...

    def evaluar_salud_financiera(self) -> str:
        ...