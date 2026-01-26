from ingest.qfx.qfx_ingest import ingest_qfx

FILEPATH = "samples/July24.qfx"  # adjust if needed

txs = ingest_qfx(FILEPATH)
print("Loaded:", len(txs))
print("First 3:")
for t in txs[:3]:
    print(t.id, t.posted_date, t.amount, t.name, "|", t.memo)
