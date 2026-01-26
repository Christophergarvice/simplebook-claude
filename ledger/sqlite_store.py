from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable, List, Optional

from models.transaction import Transaction


class SQLiteStore:
    def __init__(self, db_path: str = "data/simplebook.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> None:
        with self.connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id TEXT PRIMARY KEY,
                    posted_date TEXT NOT NULL,
                    amount REAL NOT NULL,
                    direction TEXT NOT NULL,
                    name TEXT,
                    memo TEXT,
                    type TEXT,
                    checknum TEXT,
                    source_file TEXT,
                    raw_json TEXT,
                    tags_json TEXT,
                    notes TEXT
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tx_posted_date ON transactions(posted_date)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tx_amount ON transactions(amount)")
            conn.commit()

    def upsert_transactions(self, txs: Iterable[Transaction]) -> int:
        """
        Inserts transactions; skips duplicates by primary key (id).
        Returns count inserted (not total seen).
        """
        import json

        inserted = 0
        with self.connect() as conn:
            cur = conn.cursor()
            for tx in txs:
                try:
                    cur.execute("""
                        INSERT OR IGNORE INTO transactions
                        (id, posted_date, amount, direction, name, memo, type, checknum, source_file, raw_json, tags_json, notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        tx.id,
                        tx.posted_date,
                        tx.amount,
                        tx.direction,
                        tx.name,
                        tx.memo,
                        tx.type,
                        tx.checknum,
                        tx.source_file,
                        json.dumps(tx.raw, ensure_ascii=False),
                        json.dumps(list(tx.tags), ensure_ascii=False),
                        tx.notes,
                    ))
                    if cur.rowcount == 1:
                        inserted += 1
                except sqlite3.IntegrityError:
                    # should be covered by OR IGNORE, but keep safe
                    pass
            conn.commit()
        return inserted

    def count_transactions(self) -> int:
        with self.connect() as conn:
            row = conn.execute("SELECT COUNT(*) AS c FROM transactions").fetchone()
            return int(row["c"])

    def list_transactions(
        self,
        year: Optional[int] = None,
        month: Optional[int] = None,
        limit: int = 50
    ) -> List[Transaction]:
        """
        Returns newest-first by posted_date.
        """
        import json

        where = []
        params = []

        if year is not None and month is not None:
            prefix = f"{year:04d}-{month:02d}-"
            where.append("posted_date LIKE ?")
            params.append(prefix + "%")

        where_sql = ("WHERE " + " AND ".join(where)) if where else ""
        sql = f"""
            SELECT * FROM transactions
            {where_sql}
            ORDER BY posted_date DESC, ABS(amount) DESC
            LIMIT ?
        """
        params.append(limit)

        out: List[Transaction] = []
        with self.connect() as conn:
            rows = conn.execute(sql, params).fetchall()
            for r in rows:
                raw = json.loads(r["raw_json"]) if r["raw_json"] else {}
                tags = tuple(json.loads(r["tags_json"])) if r["tags_json"] else tuple()
                out.append(Transaction(
                    id=r["id"],
                    posted_date=r["posted_date"],
                    amount=float(r["amount"]),
                    direction=r["direction"],
                    name=r["name"],
                    memo=r["memo"],
                    type=r["type"],
                    checknum=r["checknum"],
                    source_file=r["source_file"],
                    raw=raw,
                    tags=tags,
                    notes=r["notes"],
                ))
        return out

    def list_by_month(self, year: int, month: int, limit: int = 5000) -> List[Transaction]:
        if not (1 <= month <= 12):
            raise ValueError("month must be 1..12")

        return self.list_transactions(year=year, month=month, limit=limit)

    def list_months(self) -> list[tuple[str, int]]:
        """
        Returns a list of (YYYY-MM, count) sorted newest-first.
        """
        sql = """
            SELECT SUBSTR(posted_date, 1, 7) AS ym, COUNT(*) AS c
            FROM transactions
            WHERE posted_date IS NOT NULL AND posted_date != ''
            GROUP BY ym
            ORDER BY ym DESC
        """
        with self.connect() as conn:
            rows = conn.execute(sql).fetchall()
            return [(r["ym"], int(r["c"])) for r in rows]






