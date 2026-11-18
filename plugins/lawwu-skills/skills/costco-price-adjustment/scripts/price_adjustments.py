# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Work out which Costco purchases are owed a price adjustment, and keep a ledger of requests.

Usage:
  uv run price_adjustments.py candidates --purchases purchases.json --prices prices.json --ledger ledger.json
  uv run price_adjustments.py record --ledger ledger.json --order 1234567890 --item 1234567 \
      --promo-price 299.99 --promo-date 2026-11-12 --quantity 1 --credit 100.00 --status submitted
  uv run price_adjustments.py pending --ledger ledger.json

File shapes are documented in SKILL.md. All money is handled as decimal strings.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

WINDOW_DAYS = 30
CREDIT_BUSINESS_DAYS = 10
INACTIVE_STATUSES = {"cancelled", "canceled", "returned", "refunded"}
# A denied or withdrawn request does not block asking again at a different price.
DEAD_REQUESTS = {"denied", "withdrawn"}


def load(path: str | None) -> list[dict]:
    if not path or not Path(path).exists():
        return []
    data = json.loads(Path(path).read_text())
    if not isinstance(data, list):
        sys.exit(f"{path}: expected a JSON list")
    return data


def day(value: str) -> date:
    return datetime.fromisoformat(value).date()


def money(value) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"))


def add_business_days(start: date, days: int) -> date:
    current = start
    while days:
        current += timedelta(days=1)
        if current.weekday() < 5:
            days -= 1
    return current


def latest_prices(prices: list[dict]) -> dict[tuple[str, str], dict]:
    """Keep the most recent price seen for each (item, channel)."""
    latest: dict[tuple[str, str], dict] = {}
    for obs in prices:
        key = (str(obs["item_number"]), obs.get("channel", "online"))
        if key not in latest or obs["checked_at"] > latest[key]["checked_at"]:
            latest[key] = obs
    return latest


def find_candidates(purchases, prices, ledger, today: date, window: int) -> dict:
    latest = latest_prices(prices)
    candidates, skipped = [], []
    open_until: list[date] = []  # last day of every purchase still inside its window

    for p in purchases:
        item = str(p["item_number"])
        channel = p.get("channel", "online")
        ref = str(p.get("order_number") or p.get("receipt_id") or "")
        base = {
            "channel": channel,
            "order_number": ref,
            "item_number": item,
            "description": p.get("description", ""),
            "purchase_date": p["purchase_date"],
        }

        def skip(reason: str) -> None:
            skipped.append({**base, "reason": reason})

        if p.get("status", "").lower() in INACTIVE_STATUSES:
            skip(f"purchase is {p['status'].lower()}")
            continue

        bought = day(p["purchase_date"])
        last_day = bought + timedelta(days=window)
        if today > last_day:
            skip(f"bought more than {window} days ago (window closed {last_day})")
            continue

        open_until.append(last_day)
        obs = latest.get((item, channel))
        if obs is None:
            other = "warehouse" if channel == "online" else "online"
            if (item, other) in latest:
                skip(f"only the {other} price was checked; Costco does not adjust across channels")
            else:
                skip("no current price checked")
            continue

        promo_end = day(obs["promo_end"]) if obs.get("promo_end") else None
        if promo_end and promo_end >= today:
            open_until.append(promo_end)
        if promo_end and promo_end < today:
            skip(f"promotion ended {promo_end}; Costco may deny requests made after it ends")
            continue

        paid = money(p["unit_price_paid"])
        now = money(obs["price"])
        if now >= paid:
            skip(f"no drop (paid {paid}, now {now})")
            continue

        quantity = int(p.get("quantity", 1))
        limit = obs.get("limit")
        eligible = min(quantity, int(limit)) if limit else quantity

        prior = [
            e
            for e in ledger
            if str(e.get("order_number")) == ref
            and str(e.get("item_number")) == item
            and e.get("status", "").lower() not in DEAD_REQUESTS
        ]
        compare_to = paid
        prior_price = None
        if prior:
            prior_price = min(money(e["promo_price"]) for e in prior)
            if prior_price <= now:
                skip(f"already requested at {prior_price}")
                continue
            compare_to = prior_price

        credit = (compare_to - now) * eligible
        promo_date = day(obs.get("promo_start") or obs["checked_at"])
        deadline = min(last_day, promo_end) if promo_end else last_day

        entry = {
            **base,
            "action": "submit_form" if channel == "online" else "returns_counter",
            "unit_price_paid": str(paid),
            "promo_price": str(now),
            "quantity_bought": quantity,
            "quantity_eligible": eligible,
            "expected_credit_before_tax": str(credit),
            "deadline": deadline.isoformat(),
            "days_left": (deadline - today).days,
            "price_source": obs.get("source", ""),
        }
        notes = []
        if prior_price is not None:
            entry["prior_request_price"] = str(prior_price)
            notes.append(
                "price fell again after an earlier request; credit is the extra difference"
            )
        if eligible < quantity:
            notes.append(f"promotion limit {limit}; only {eligible} of {quantity} qualify")
        if notes:
            entry["notes"] = notes
        if channel == "online":
            entry["form"] = {
                "month": bought.strftime("%B"),
                "year": str(bought.year),
                "order_number": ref,
                "item_number": item,
                "promotional_price": str(now),
                "promotion_date": promo_date.strftime("%m/%d/%Y"),
            }
        else:
            entry["warehouse"] = p.get("warehouse", "")
        candidates.append(entry)

    candidates.sort(key=lambda c: (c["days_left"], -Decimal(c["expected_credit_before_tax"])))
    total = sum((Decimal(c["expected_credit_before_tax"]) for c in candidates), Decimal("0"))
    run_again_by = max(min(open_until) - timedelta(days=2), today) if open_until else None
    return {
        "today": today.isoformat(),
        "run_again_by": run_again_by.isoformat() if run_again_by else None,
        "candidates": candidates,
        "expected_credit_before_tax": str(total),
        "skipped": skipped,
    }


def cmd_candidates(args) -> None:
    today = day(args.today) if args.today else date.today()
    result = find_candidates(
        load(args.purchases), load(args.prices), load(args.ledger), today, args.window
    )
    print(json.dumps(result, indent=2))


def cmd_record(args) -> None:
    path = Path(args.ledger)
    ledger = load(args.ledger)
    submitted = day(args.submitted) if args.submitted else date.today()
    ledger.append(
        {
            "order_number": args.order,
            "item_number": args.item,
            "channel": args.channel,
            "promo_price": str(money(args.promo_price)),
            "promo_date": args.promo_date,
            "quantity": args.quantity,
            "expected_credit_before_tax": str(money(args.credit)),
            "status": args.status,
            "submitted_at": submitted.isoformat(),
            "credit_expected_by": add_business_days(submitted, CREDIT_BUSINESS_DAYS).isoformat(),
            "confirmation": args.confirmation or "",
        }
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(ledger, indent=2) + "\n")
    print(f"recorded {args.order} / {args.item} as {args.status} ({len(ledger)} entries)")


def cmd_pending(args) -> None:
    today = day(args.today) if args.today else date.today()
    waiting = [e for e in load(args.ledger) if e.get("status") == "submitted"]
    for e in waiting:
        e["overdue"] = bool(e.get("credit_expected_by")) and day(e["credit_expected_by"]) < today
    print(json.dumps(waiting, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)

    c = sub.add_parser("candidates", help="list purchases owed a price adjustment")
    c.add_argument("--purchases", required=True)
    c.add_argument("--prices", required=True)
    c.add_argument("--ledger")
    c.add_argument("--today", help="YYYY-MM-DD (default: today)")
    c.add_argument("--window", type=int, default=WINDOW_DAYS)
    c.set_defaults(func=cmd_candidates)

    r = sub.add_parser("record", help="add a request to the ledger")
    r.add_argument("--ledger", required=True)
    r.add_argument("--order", required=True, help="order number, or receipt id for warehouse")
    r.add_argument("--item", required=True)
    r.add_argument("--channel", default="online", choices=["online", "warehouse"])
    r.add_argument("--promo-price", required=True)
    r.add_argument("--promo-date", required=True, help="YYYY-MM-DD")
    r.add_argument("--quantity", type=int, default=1)
    r.add_argument("--credit", required=True, help="expected credit before tax")
    r.add_argument(
        "--status",
        default="submitted",
        choices=["submitted", "credited", "denied", "withdrawn", "asked_at_warehouse"],
    )
    r.add_argument("--submitted", help="YYYY-MM-DD (default: today)")
    r.add_argument("--confirmation", help="confirmation text or number shown after submitting")
    r.set_defaults(func=cmd_record)

    p = sub.add_parser("pending", help="list submitted requests not yet credited")
    p.add_argument("--ledger", required=True)
    p.add_argument("--today")
    p.set_defaults(func=cmd_pending)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
