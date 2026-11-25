"""Experimentos del README: ¿qué pasa con el total si cambio decisiones de la arquitectura?

Usa los mismos precios de la lista oficial de AWS que calculo_costos.py (us-east-1, bajo demanda).
Uso: python3 experimentos.py
"""
from calculo_costos import calcular

casos = [
    ("Arquitectura propuesta (base)", {}),
    ("Sin RDS Proxy", dict(proxy=False)),
    ("Sin Multi-AZ (una sola zona para la base)", dict(multi_az=False)),
    ("Sin Proxy y sin Multi-AZ", dict(proxy=False, multi_az=False)),
    ("4 tareas de la app en vez de 2", dict(tareas=4)),
]
base = sum(v for _, v in calcular())
print("| Caso | Total mensual (USD) | Diferencia con la base |")
print("|---|---|---|")
for nombre, kw in casos:
    total = sum(v for _, v in calcular(**kw))
    print(f"| {nombre} | {total:,.2f} | {total - base:+,.2f} |")
