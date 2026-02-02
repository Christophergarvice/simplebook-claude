from __future__ import annotations
from dataclasses import dataclass
import html

from config.runtime_config import CFG


@dataclass
class RuleResult:
    category: str | None = None
    confidence: str = "guess"   # "hard" or "guess"
    note: str | None = None


def _clean(s: str | None) -> str:
    # Handles AT&amp;T -> AT&T, etc.
    return html.unescape(s or "").strip()


def classify_tx(t) -> RuleResult:
    """
    Lightweight rule-based classifier for SimpleBook v0.1.
    t is a Transaction object (your models/transaction.py).
    """
    name = _clean(getattr(t, "name", "")).upper()
    memo = _clean(getattr(t, "memo", ""))
    amt = float(getattr(t, "amount", 0) or 0)
    # Payment apps are high-risk: never auto-assume rental income
    if amt > 0 and any(x in name for x in {"CASH APP", "VENMO", "PAYPAL", "ZELLE", "APPLE CASH", "META PAY"}):
        return RuleResult(category=None, confidence="guess", note="payment app income - classify manually")

    # --- INCOME (config-driven)
    if amt > 0 and CFG["ASSUME_ALL_INCOME_IS_RENTAL"]:
        return RuleResult(category="Rental Income", confidence="guess")

    # --- VENDOR RULES (config-driven contains match)
    for needle, cat, conf, note in CFG["VENDOR_RULES"]:
        if needle in name:
            return RuleResult(category=cat, confidence=conf, note=note)

    # Checks with unknown payee
    if "CHECK #" in name or (getattr(t, "checknum", None) is not None):
        return RuleResult(category=None, confidence="guess", note="unknown check payee")

    # Default: unknown
    return RuleResult(category=None, confidence="guess")

