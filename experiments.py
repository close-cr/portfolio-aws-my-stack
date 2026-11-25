"""README experiments: what happens to the total if I change architecture decisions?

Uses the same official AWS prices as cost_estimate.py (us-east-1, on-demand).
Usage: python3 experiments.py
"""
from cost_estimate import estimate

cases = [
    ("Proposed architecture (baseline)", {}),
    ("Without RDS Proxy", dict(proxy=False)),
    ("Without Multi-AZ (single zone for the database)", dict(multi_az=False)),
    ("Without Proxy and without Multi-AZ", dict(proxy=False, multi_az=False)),
    ("4 app tasks instead of 2", dict(tasks=4)),
]
baseline = sum(v for _, v in estimate())
print("| Case | Monthly total (USD) | Difference from baseline |")
print("|---|---|---|")
for name, kw in cases:
    total = sum(v for _, v in estimate(**kw))
    print(f"| {name} | {total:,.2f} | {total - baseline:+,.2f} |")
