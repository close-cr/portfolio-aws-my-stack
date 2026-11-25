"""Monthly cost estimate for the proposed architecture (us-east-1, small scenario).

Unit prices come from the OFFICIAL AWS price list (Price List bulk API, us-east-1 regional files,
versions published between 2026-11-20 and 2026-11-25). They are on-demand prices in US dollars.
They change over time: for a current figure use https://calculator.aws/

Usage:  python3 cost_estimate.py
"""
HOURS = 730  # hours per month

# --- Unit prices (USD) ---
P = dict(
    fargate_vcpu_h=0.04048, fargate_gb_h=0.004445,
    alb_h=0.0225, alb_lcu_h=0.008,
    rds_t4g_small_multiaz_h=0.065, rds_gp3_multiaz_gb_month=0.23, rds_proxy_vcpu_h=0.015,
    rds_t4g_small_single_h=0.032, rds_gp3_single_gb_month=0.115,  # without Multi-AZ (used by the experiments)
    ipv4_h=0.005,
    lambda_gb_s=0.0000166667, lambda_million_requests=0.20,
    lambda_free_gb_s=400_000, lambda_free_requests=1_000_000,
    s3_gb_month=0.023,
    secret_month=0.40, kms_key_month=1.00,
    cw_ingest_gb=0.50, cw_storage_gb_month=0.03,
    waf_acl_month=5.00, waf_rule_month=1.00, waf_million_requests=0.60,
)

# --- Assumptions for the small scenario (edit and re-run) ---
S = dict(
    tasks=2, vcpu=0.5, ram_gb=1,          # app on Fargate, 2 tasks in 2 zones
    avg_lcu=1,                            # conservative (upper-bound) assumption of load balancer capacity used
    db_gb=20, db_vcpus=2,                 # RDS Multi-AZ db.t4g.small (2 vCPU)
    invocations_month=900, seconds=90, lambda_gb=1,   # ~30 a day, 90 s each, 1 GB
    s3_gb=5, secrets=10, keys=1,
    logs_gb=2, waf_rules=3, waf_million_requests=1,
)


def estimate(multi_az=True, proxy=True, tasks=None):
    tasks = tasks or S["tasks"]
    ips = 2 + tasks  # 2 on the load balancer (one per zone) + one per task
    fargate = tasks * (S["vcpu"] * P["fargate_vcpu_h"] + S["ram_gb"] * P["fargate_gb_h"]) * HOURS
    lam_gb_s = S["invocations_month"] * S["seconds"] * S["lambda_gb"]
    lam = (max(0, lam_gb_s - P["lambda_free_gb_s"]) * P["lambda_gb_s"]
           + max(0, S["invocations_month"] - P["lambda_free_requests"]) / 1e6 * P["lambda_million_requests"])
    return [
        (f"Fargate (app, {tasks} tasks 0.5 vCPU / 1 GB, 24/7)", fargate),
        ("Application Load Balancer (hours)", P["alb_h"] * HOURS),
        ("Application Load Balancer (capacity used, 1 LCU)", S["avg_lcu"] * P["alb_lcu_h"] * HOURS),
        ("RDS PostgreSQL Multi-AZ db.t4g.small" if multi_az else "RDS PostgreSQL Single-AZ db.t4g.small",
         (P["rds_t4g_small_multiaz_h"] if multi_az else P["rds_t4g_small_single_h"]) * HOURS),
        ("RDS storage 20 GB (gp3, Multi-AZ)" if multi_az else "RDS storage 20 GB (gp3, Single-AZ)",
         S["db_gb"] * (P["rds_gp3_multiaz_gb_month"] if multi_az else P["rds_gp3_single_gb_month"])),
        ("RDS Proxy (2 vCPU of the instance)", (S["db_vcpus"] * P["rds_proxy_vcpu_h"] * HOURS) if proxy else 0.0),
        (f"Public IPv4 addresses ({ips})", ips * P["ipv4_h"] * HOURS),
        (f"Lambda workers ({lam_gb_s:,.0f} GB-s: inside the free tier)", lam),
        ("SQS + EventBridge Scheduler (inside the free tier)", 0.0),
        ("S3 (5 GB)", S["s3_gb"] * P["s3_gb_month"]),
        ("Secrets Manager (10 secrets)", S["secrets"] * P["secret_month"]),
        ("KMS (1 key)", S["keys"] * P["kms_key_month"]),
        ("CloudWatch Logs (2 GB a month, 30-day retention)", S["logs_gb"] * (P["cw_ingest_gb"] + P["cw_storage_gb_month"])),
        ("WAF (1 ACL, 3 rules, 1 million requests)", P["waf_acl_month"] + S["waf_rules"] * P["waf_rule_month"] + S["waf_million_requests"] * P["waf_million_requests"]),
    ]


if __name__ == "__main__":
    rows = estimate()
    for name, value in rows:
        print(f"| {name} | USD {value:,.2f} |")
    print(f"| **Estimated monthly total** | **USD {sum(v for _, v in rows):,.2f}** |")
    print("\nNot included: CloudFront (its per-GB rate was not in the price list consulted), data transfer to the internet, or taxes.")
