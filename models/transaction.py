from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from hashlib import sha1
from typing import Any, Dict, Optional


def _clean_str(s: Optional[str]) -> Optional[str]:
    if s is None:
        return None
    s2 = str(s).strip()
    return s2 if s2 else None


def _stable_fallback_id(
    posted_date: Optional[str],
    amount: float,
    name: Optional[str],
    memo: Optional[str],
    checknum: Optional[str],
) -> str:
    """
    Deterministic fallback ID when FITID is missing.
    Important: This must be stable across runs for dedupe.
    """
    basis = "|".join([
        posted_date or "",
        f"{amount:.2f}",
        (name or "").upper(),
        (memo or "").upper(),
        checknum or "",
    ])
    return "SB-" + sha1(basis.encode("utf-8", errors="ignore")).hexdigest()[:16]


@dataclass(frozen=True, slots=True)
class Transaction:
    """
    Canonical SimpleBook transaction model (v1).

    Conventions:
      - amount: positive = credit, negative = debit
      - direction: 'credit' or 'debit' (redundant on purpose; helps rules and humans)
      - id: FITID if available, else stable deterministic fallback
      - raw: preserves original parsed fields for debugging and traceability
    """

    id: str
    posted_date: str                      # YYYY-MM-DD
    amount: float                         # +credit, -debit
    direction: str                        # 'credit' | 'debit'

    name: Optional[str] = None            # QFX <NAME>
    memo: Optional[str] = None            # QFX <MEMO>
    type: Optional[str] = None            # QFX <TRNTYPE>
    checknum: Optional[str] = None        # QFX <CHECKNUM>

    source_file: Optional[str] = None     # filename/path imported from
    raw: Dict[str, Any] = field(default_factory=dict)

    tags: tuple[str, ...] = field(default_factory=tuple)
    notes: Optional[str] = None

    @staticmethod
    def from_qfx_dict(raw_tx: Dict[str, Any], source_file: Optional[str] = None) -> "Transaction":
        """
        Build a Transaction from a dict produced by the QFX parser.
        Expected keys (from your current parser):
          - type, posted_date, amount, fitid, checknum, name, memo, posted_raw
        """
        posted_date = _clean_str(raw_tx.get("posted_date"))
        if not posted_date:
            raise ValueError(f"Missing posted_date in raw_tx: {raw_tx}")

        # Validate date format (YYYY-MM-DD)
        try:
            datetime.strptime(posted_date, "%Y-%m-%d")
        except Exception as e:
            raise ValueError(f"Invalid posted_date '{posted_date}': {e}")

        amount_raw = raw_tx.get("amount", 0.0)
        try:
            amount = float(amount_raw)
        except Exception as e:
            raise ValueError(f"Invalid amount '{amount_raw}': {e}")

        direction = "credit" if amount > 0 else "debit"

        fitid = _clean_str(raw_tx.get("fitid"))
        checknum = _clean_str(raw_tx.get("checknum"))
        name = _clean_str(raw_tx.get("name"))
        memo = _clean_str(raw_tx.get("memo"))
        tx_type = _clean_str(raw_tx.get("type"))

        tx_id = fitid or _stable_fallback_id(posted_date, amount, name, memo, checknum)

        # Keep a copy of raw input for traceability
        raw_copy = dict(raw_tx)
        if source_file is not None:
            raw_copy.setdefault("_source_file", source_file)

        return Transaction(
            id=tx_id,
            posted_date=posted_date,
            amount=amount,
            direction=direction,
            name=name,
            memo=memo,
            type=tx_type,
            checknum=checknum,
            source_file=source_file,
            raw=raw_copy,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "posted_date": self.posted_date,
            "amount": self.amount,
            "direction": self.direction,
            "name": self.name,
            "memo": self.memo,
            "type": self.type,
            "checknum": self.checknum,
            "source_file": self.source_file,
            "tags": list(self.tags),
            "notes": self.notes,
            "raw": self.raw,
        }
