from ledger.sqlite_store import SQLiteStore
from reports.basic_summary import summarize, top_spend_vendors, top_spend_by_kind_safe

store = SQLiteStore("data/simplebook.db")
store.init_db()

YEAR = 2025
MONTH = 11

txs = store.list_transactions(year=YEAR, month=MONTH, limit=10000)
s = summarize(txs)

print(f"Month: {YEAR}-{MONTH:02d}")
print("Count:", s.count)
print("Credits:", s.credits_count, "Total:", s.credits_total)
print("Debits :", s.debits_count, "Total:", s.debits_total)
print("Net    :", s.net_total)

print("\nTop spend vendors:")
for name, total in top_spend_vendors(txs, n=10):
    print(f"{total:10.2f}  {name}")

print("\nTop spend by kind:")
buckets = top_spend_by_kind_safe(txs, n=10)
for kind, items in buckets.items():
    print(f"\n{kind}:")
    for name, total in items:
        print(f"{total:10.2f}  {name}")
