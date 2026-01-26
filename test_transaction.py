from models.transaction import Transaction

raw = {
    "type": "DEBIT",
    "posted_date": "2024-07-01",
    "amount": -42.19,
    "fitid": "ABC123",
    "checknum": None,
    "name": "DEBIT CARD PURCHASE",
    "memo": "HOME DEPOT 1234",
    "posted_raw": "20240701120000.000[-5:EST]",
}

tx = Transaction.from_qfx_dict(raw, source_file="samples/July24.qfx")
print(tx)
print(tx.to_dict())
