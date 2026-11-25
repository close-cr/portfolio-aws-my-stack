"""Estimación mensual de la arquitectura propuesta (región us-east-1, escenario pequeño).

Los precios unitarios salen de la LISTA OFICIAL de precios de AWS (Price List bulk API, archivos
regionales de us-east-1, versiones publicadas entre 2026-11-20 y 2026-11-25). Son precios bajo demanda
en dólares. Cambian con el tiempo: para una cifra vigente usar https://calculator.aws/

Uso:  python3 calculo_costos.py
"""
H = 730  # horas por mes

# --- Precios unitarios (USD) ---
P = dict(
    fargate_vcpu_h=0.04048, fargate_gb_h=0.004445,
    alb_h=0.0225, alb_lcu_h=0.008,
    rds_t4g_small_multiaz_h=0.065, rds_gp3_multiaz_gb_mes=0.23, rds_proxy_vcpu_h=0.015,
    ipv4_h=0.005,
    lambda_gb_s=0.0000166667, lambda_millon_peticiones=0.20,
    lambda_gratis_gb_s=400_000, lambda_gratis_peticiones=1_000_000,
    s3_gb_mes=0.023,
    secreto_mes=0.40, kms_llave_mes=1.00,
    cw_ingesta_gb=0.50, cw_almacen_gb_mes=0.03,
    waf_acl_mes=5.00, waf_regla_mes=1.00, waf_millon_peticiones=0.60,
)

# --- Supuestos del escenario pequeño (editar y volver a correr) ---
S = dict(
    tareas=2, vcpu=0.5, gb_ram=1,         # app en Fargate, 2 tareas en 2 zonas
    lcu_promedio=1,                       # SUPUESTO conservador (techo) de capacidad usada del balanceador
    db_gb=20, db_vcpus=2,                 # RDS Multi-AZ db.t4g.small (2 vCPU)
    ips_publicas=4,                       # 2 del balanceador (una por zona) + 2 de las tareas
    invocaciones_mes=900, segundos=90, lambda_gb=1,   # ~30 al día, 90 s cada una, 1 GB
    s3_gb=5, secretos=10, llaves=1,
    logs_gb=2, waf_reglas=3, waf_millones_peticiones=1,
)

def calcular():
    f = S["tareas"] * (S["vcpu"] * P["fargate_vcpu_h"] + S["gb_ram"] * P["fargate_gb_h"]) * H
    lam_gb_s = S["invocaciones_mes"] * S["segundos"] * S["lambda_gb"]
    lam = max(0, lam_gb_s - P["lambda_gratis_gb_s"]) * P["lambda_gb_s"] + max(0, S["invocaciones_mes"] - P["lambda_gratis_peticiones"]) / 1e6 * P["lambda_millon_peticiones"]
    filas = [
        ("Fargate (app, 2 tareas 0,5 vCPU / 1 GB, 24/7)", f),
        ("Application Load Balancer (hora)", P["alb_h"] * H),
        ("Application Load Balancer (capacidad usada, 1 LCU)", S["lcu_promedio"] * P["alb_lcu_h"] * H),
        ("RDS PostgreSQL Multi-AZ db.t4g.small", P["rds_t4g_small_multiaz_h"] * H),
        ("RDS almacenamiento 20 GB (gp3, Multi-AZ)", S["db_gb"] * P["rds_gp3_multiaz_gb_mes"]),
        ("RDS Proxy (2 vCPU de la instancia)", S["db_vcpus"] * P["rds_proxy_vcpu_h"] * H),
        ("Direcciones IPv4 públicas (4)", S["ips_publicas"] * P["ipv4_h"] * H),
        (f"Lambda workers ({lam_gb_s:,.0f} GB-s: dentro de la capa gratuita)", lam),
        ("SQS + EventBridge Scheduler (dentro de la capa gratuita)", 0.0),
        ("S3 (5 GB)", S["s3_gb"] * P["s3_gb_mes"]),
        ("Secrets Manager (10 secretos)", S["secretos"] * P["secreto_mes"]),
        ("KMS (1 llave)", S["llaves"] * P["kms_llave_mes"]),
        ("CloudWatch Logs (2 GB al mes, retención 30 días)", S["logs_gb"] * (P["cw_ingesta_gb"] + P["cw_almacen_gb_mes"])),
        ("WAF (1 ACL, 3 reglas, 1 millón de peticiones)", P["waf_acl_mes"] + S["waf_reglas"] * P["waf_regla_mes"] + S["waf_millones_peticiones"] * P["waf_millon_peticiones"]),
    ]
    return filas

if __name__ == "__main__":
    filas = calcular()
    for n, v in filas:
        print(f"| {n} | USD {v:,.2f} |")
    print(f"| **Total mensual estimado** | **USD {sum(v for _, v in filas):,.2f}** |")
    print("\nNo incluye: CloudFront (su tarifa por GB no estaba en la lista consultada), transferencia de datos hacia internet, ni impuestos.")
