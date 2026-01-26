from __future__ import annotations

from collections import Counter
import re

from dataclasses import dataclass
from typing import Iterable

from models.transaction import Transaction



@dataclass
class Summary:
    count: int
    credits_count: int
    debits_count: int
    credits_total: float
    debits_total: float
    net_total: float


def summarize(txs: Iterable[Transaction]) -> Summary:
    credits_total = 0.0
    debits_total = 0.0
    credits_count = 0
    debits_count = 0
    count = 0

    for t in txs:
        count += 1
        amt = float(getattr(t, "amount", 0) or 0)
        if amt > 0:
            credits_total += amt
            credits_count += 1
        else:
            debits_total += amt  # negative
            debits_count += 1

    net = credits_total + debits_total
    return Summary(
        count=count,
        credits_count=credits_count,
        debits_count=debits_count,
        credits_total=round(credits_total, 2),
        debits_total=round(debits_total, 2),
        net_total=round(net, 2),
    )


def top_spend_vendors(txs: Iterable[Transaction], n: int = 10):
    """
    Returns a simple top-N list of spend "vendors" across ALL debit txs.
    Vendor name comes from memo/name.
    """
    c = Counter()
    for t in txs:
        amt = float(getattr(t, "amount", 0) or 0)
        if amt >= 0:
            continue
        key = (getattr(t, "memo", None) or getattr(t, "name", None) or "Unknown").strip() or "Unknown"
        c[key] += abs(amt)
    return [(name, round(total, 2)) for name, total in c.most_common(n)]


# Optional: categorized top spend by kind (safe; won’t KeyError)
def tx_kind(t: Transaction) -> str:
    tx_type = (getattr(t, "type", "") or "").upper()
    name = (getattr(t, "name", "") or "").upper()
    memo = (getattr(t, "memo", "") or "").upper()
    checknum = getattr(t, "checknum", None)

    if checknum or tx_type == "CHECK" or "CHECK" in name:
        return "CHECK"
    if "TRANSFER" in name or "TRANSFER" in memo or tx_type in ("XFER", "TRANSFER"):
        return "TRANSFER"
    return "OTHER_DEBIT"


def top_spend_by_kind_safe(txs: Iterable[Transaction], n: int = 10):
    buckets = {"CHECK": Counter(), "TRANSFER": Counter(), "CARD_PAYMENT": Counter(), "OTHER_DEBIT": Counter()}

    for t in txs:
        amt = float(getattr(t, "amount", 0) or 0)
        if amt >= 0:
            continue

        kind = tx_kind(t) or "OTHER_DEBIT"
        if kind not in buckets:
            kind = "OTHER_DEBIT"

        key = (getattr(t, "memo", None) or getattr(t, "name", None) or "Unknown").strip() or "Unknown"
        buckets[kind][key] += abs(amt)

    return {k: [(name, round(total, 2)) for name, total in c.most_common(n)]
            for k, c in buckets.items()}
