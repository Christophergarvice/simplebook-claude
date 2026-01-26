from __future__ import annotations

from typing import List
from pathlib import Path

from ingest.qfx.qfx_reader import parse_qfx_to_raw
from models.transaction import Transaction


def ingest_qfx(filepath: str) -> List[Transaction]:
    """
    Reads a QFX file and returns canonical Transaction objects.
    """
    filepath = str(Path(filepath))
    raw_txs = parse_qfx_to_raw(filepath)
    return [Transaction.from_qfx_dict(raw, source_file=filepath) for raw in raw_txs]
