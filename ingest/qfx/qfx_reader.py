from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


def parse_qfx_to_raw(filepath: str) -> List[Dict[str, Any]]:
    """
    Reads a QFX file and returns a list of raw transaction dicts.
    This stays close to the original QFX fields for traceability.
    """
    path = Path(filepath)
    text = path.read_text(errors="ignore")

    blocks = re.findall(r"<STMTTRN>(.*?)</STMTTRN>", text, flags=re.DOTALL)

    raw_txs: List[Dict[str, Any]] = []

    for block in blocks:
        tx_type = _extract_tag(block, "TRNTYPE")
        posted_raw = _extract_tag(block, "DTPOSTED")
        amount_raw = _extract_tag(block, "TRNAMT")
        fitid = _extract_tag(block, "FITID")
        checknum = _extract_tag(block, "CHECKNUM")
        name = _extract_tag(block, "NAME")
        memo = _extract_tag(block, "MEMO")

        posted_date = _normalize_qfx_date(posted_raw)

        try:
            amount = float(amount_raw) if amount_raw else 0.0
        except Exception:
            amount = 0.0

        raw_txs.append({
            "type": tx_type,
            "posted_raw": posted_raw,
            "posted_date": posted_date,
            "amount": amount,
            "fitid": fitid,
            "checknum": checknum,
            "name": name,
            "memo": memo,
        })

    return raw_txs


def _extract_tag(block: str, tag: str) -> Optional[str]:
    match = re.search(rf"<{tag}>(.*?)(?=<|$)", block, flags=re.DOTALL)
    return match.group(1).strip() if match else None


def _normalize_qfx_date(raw: Optional[str]) -> Optional[str]:
    """
    Converts QFX DTPOSTED like '20240701120000.000[-5:EST]' -> '2024-07-01'
    """
    if not raw:
        return None

    m = re.match(r"(\d{8})", raw)
    if not m:
        return None

    yyyymmdd = m.group(1)
    dt = datetime.strptime(yyyymmdd, "%Y%m%d")
    return dt.strftime("%Y-%m-%d")
