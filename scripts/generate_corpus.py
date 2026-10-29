"""Generate a synthetic invoice corpus plus ground-truth answers. DO NOT MODIFY.

    python scripts/generate_corpus.py --n 300 --out corpus --answers answers.jsonl

Mix: mostly 1-page invoices, some long multi-page ones (larger than the model's
context window), exact duplicates under different file names, and a few broken
files (empty, binary, non-UTF-8).
"""

import argparse
import json
import random
from datetime import date, timedelta
from pathlib import Path

VENDORS = ["Acme Industrial Supplies Pvt Ltd", "Globex Logistics LLP", "Initech Software Services",
           "Umbrella Pharma Distributors", "Stark Components India", "Wayne Office Solutions",
           "Hooli Cloud Services", "Soylent Foods & Catering"]
ITEMS = ["Steel bolts M8", "Packing tape", "Cloud compute hours", "Consulting (hours)", "A4 paper ream",
         "Forklift rental (day)", "Safety gloves", "Network switch 24p", "Courier charges", "Toner cartridge"]
CURRENCIES = ["INR", "USD", "EUR"]
NUMBER_LABELS = ["Invoice No:", "Invoice Number:", "Invoice #"]
VENDOR_LABELS = ["Vendor:", "Supplier:", "From:"]
DATE_LABELS = ["Invoice Date:", "Date of Issue:", "Dated:"]
DATE_FORMATS = ["%Y-%m-%d", "%d/%m/%Y", "%B %d, %Y", "%d %b %Y"]
TOTAL_LABELS = ["Grand Total:", "Total Due:", "Amount Payable:"]
TERMS = ("Payment is due within 30 days. Late payments attract interest at 1.5% per month. "
         "Goods once sold will not be taken back. All disputes are subject to local jurisdiction. ")


def _money(x: float) -> str:
    return f"{x:,.2f}"


def make_invoice(rng: random.Random, idx: int, pages: int) -> tuple[str, dict]:
    number = f"{rng.choice(['INV', 'BL', 'TX'])}-{rng.randint(10_000, 99_999_999)}"
    vendor = rng.choice(VENDORS)
    issued = date(2025, 1, 1) + timedelta(days=rng.randint(0, 600))
    currency = rng.choice(CURRENCIES)
    items_per_page = rng.randint(4, 10) if pages == 1 else 45

    header = (f"{rng.choice(VENDOR_LABELS)} {vendor}\n"
              f"{rng.choice(NUMBER_LABELS)} {number}\n"
              f"{rng.choice(DATE_LABELS)} {issued.strftime(rng.choice(DATE_FORMATS))}\n"
              f"Currency: {currency}\nBill To: Customer #{rng.randint(1000, 9999)}\n\n")
    body, subtotal = [], 0.0
    for page in range(1, pages + 1):
        if pages > 1:
            body.append(f"\n--- Page {page} of {pages} --- Invoice No: {number}\n")
        for _ in range(items_per_page):
            qty, price = rng.randint(1, 50), round(rng.uniform(5, 900), 2)
            subtotal += qty * price
            body.append(f"  {qty:>3} x {rng.choice(ITEMS):<26} @ {_money(price):>10} = {_money(qty * price):>12}\n")
    tax = round(subtotal * 0.18, 2)
    total = round(subtotal + tax, 2)
    footer = (f"\nSubtotal: {_money(subtotal)}\nTax (18%): {_money(tax)}\n"
              f"{rng.choice(TOTAL_LABELS)} {currency} {_money(total)}\n\n{TERMS * rng.randint(1, 3)}")
    answer = {"invoice_number": number, "vendor": vendor, "invoice_date": issued.isoformat(),
              "currency": currency, "total": f"{total:.2f}"}
    return header + "".join(body) + footer, answer


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=300)
    parser.add_argument("--out", default="corpus")
    parser.add_argument("--answers", default="answers.jsonl")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    rng = random.Random(args.seed)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    answers, written = [], []

    for i in range(args.n):
        name = f"doc_{i:06d}.txt"
        roll = rng.random()
        if roll < 0.02:
            (out / name).write_bytes(b"")
            answers.append({"file": name, "expect_error": True})
        elif roll < 0.04:
            (out / name).write_bytes(bytes(rng.randrange(256) for _ in range(2048)))
            answers.append({"file": name, "expect_error": True})
        elif roll < 0.09 and written:
            source_text, source_answer = rng.choice(written)
            (out / name).write_text(source_text, encoding="utf-8")
            answers.append({"file": name, **source_answer})
        else:
            pages = 1 if roll < 0.80 else rng.randint(3, 8)
            text, answer = make_invoice(rng, i, pages)
            if rng.random() < 0.03:
                (out / name).write_bytes(text.replace("Customer", "Kundé").encode("latin-1"))
            else:
                (out / name).write_text(text, encoding="utf-8")
            written.append((text, answer))
            answers.append({"file": name, **answer})

    with open(args.answers, "w") as f:
        for a in answers:
            f.write(json.dumps(a) + "\n")
    print(f"wrote {args.n} documents to {out}/ and answers to {args.answers}")


if __name__ == "__main__":
    main()
