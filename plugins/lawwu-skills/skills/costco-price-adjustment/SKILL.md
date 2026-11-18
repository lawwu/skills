---
name: costco-price-adjustment
description: Find Costco purchases whose price has dropped since they were bought and request the price adjustment (the refund of the difference) for each one. Reads recent Costco.com orders and warehouse receipts from the signed-in account, checks each item's current price, works out which are inside Costco's 30-day window, fills in and submits the Costco.com price adjustment form, and keeps a ledger so nothing is requested twice and unpaid credits get chased. Use whenever someone wants a Costco price adjustment or price match, asks whether anything they bought at Costco has gone on sale or is cheaper now, wants money back because a Costco price dropped, wants their Costco purchases monitored or checked on a schedule for price drops, or mentions the Costco PriceAdjustmentView form, even if they only name one item or one order.
compatibility: Needs a browser the agent can drive with the user signed in to Costco.com, and uv for the bundled script.
---

# Costco price adjustment

Costco refunds the difference when an item's price drops within 30 days of buying it, but only
if the member asks. This skill does the asking: it finds the purchases that qualify, requests
the adjustment for each, and keeps track until the credit arrives.

## The rules that decide what qualifies

These come from Costco's price adjustment policy
(<https://customerservice.costco.com/app/answers/detail/a_id/628>). Reread that page if a
request is denied or the form has changed; Costco can change the policy.

- **30 days.** The price must drop within 30 days of the purchase date, and the request must be
  made inside that window.
- **Promotions with end dates** (Member-Only Savings, holiday events): ask while the promotion
  is still running. Requests made after it ends may be denied, so a promotion ending tomorrow is
  more urgent than a 30-day window that closes next week.
- **Same channel only.** A Costco.com order is adjusted against the Costco.com price; a warehouse
  purchase against that warehouse's price. Costco does not adjust an online order to a warehouse
  price or the reverse (online prices include shipping), and never matches other retailers.
- **Promotion limits.** If the promotion says "Limit 2 per member", only 2 units qualify.
- **Costco.com orders** are requested through the form at
  <https://www.costco.com/PriceAdjustmentView>. The credit goes to the original payment method,
  typically within 5 to 10 business days; orders paid with a Costco Shop Card are credited as a
  new Digital Costco Shop Card sent by email.
- **Warehouse purchases cannot be requested online.** They are handled in person at the Returns
  counter of the warehouse where the item was bought. For these the skill's job ends at a clear
  list the member can take with them.
- Not eligible: precious metals, anything already returned or cancelled, and resale purchases.
  Costco may deny any request at its discretion.

## Ground rules

- **The user signs in.** If Costco shows a sign-in, passcode or CAPTCHA page, show the browser
  and ask the user to complete it. Never ask for or type their password or codes.
- **Submitting is the user's call.** Sending the form is a request made in their name. Show the
  list of what will be submitted and get a yes before the first submission of a run, unless the
  request that started the run already said to submit (for example a scheduled run they set up
  to "submit whatever qualifies"). If nobody is there to say yes, stop after the review list and
  leave it for them.
- **Only claim real drops.** Enter the price actually shown on Costco.com for that exact item
  number, on the date it was seen. A wrong promotional price is a false claim in the user's
  name, so when the current price is unclear (see "Check current prices"), leave the item out
  and say why.
- **Purchase history is private.** Keep the working files below on this machine, outside any
  git repository, and don't send them anywhere.

## Working files

Keep state in `~/.costco-price-adjustment/` (or a folder the user names). Three JSON files, each
a list:

`purchases.json`: one entry per item line bought in the last 30 days or so.

```json
{"channel": "online", "order_number": "1234567890", "purchase_date": "2026-11-03",
 "item_number": "1234567", "description": "Example Blender, Black",
 "unit_price_paid": "399.99", "quantity": 1, "status": "delivered"}
```

For warehouse lines use `"channel": "warehouse"`, a `receipt_id` instead of `order_number`,
`"warehouse": "<name or number>"`, and `"food": true` on food and drink.

`prices.json`: one entry each time a current price is checked. Append; don't rewrite old
observations.

```json
{"item_number": "1234567", "channel": "online", "checked_at": "2026-11-17T09:00:00",
 "price": "299.99", "promo_start": "2026-11-12", "promo_end": "2026-11-30", "limit": 2,
 "source": "https://www.costco.com/...product page URL"}
```

`promo_start`, `promo_end` and `limit` are optional; record them when the page shows them.

`ledger.json`: every request made, written by the script's `record` command.

## Workflow

### 1. Collect recent purchases

**Online orders: start from the price adjustment form, not the order history.** The Online tab
of Orders & Purchases can leave out recent orders, while the form's own dropdowns list exactly
the orders Costco will accept. Open <https://www.costco.com/PriceAdjustmentView> and, without
submitting anything:

1. Note the months offered under Month and Year (only eligible ones are listed).
2. For each, choose it and read the Order Number dropdown ("order number - date"). A month with
   nothing eligible says "We could not find any orders for the selected month and year."
3. Choose each order and read its item cards: description, item number, price, quantity.

Then open each order's details page (from Orders & Purchases, or
`.../orderdetails/<order number>` under the same account URL) for two things the form does not
show:

- **Status.** The form still lists orders that were returned or cancelled.
- **Discounts.** Press "Show Details" in the Order Summary. A "Discount on Order" line is not
  spread across the item lines, so work out which item it belongs to (a bundled protection plan
  shown at full price with a matching discount was free). The price paid is the price after
  the discount; adjusting against the list price would overstate the credit. If it is unclear
  which item a discount belongs to, leave those items out and say so.

Skip fee lines (recycling fees and the like) and bundled add-ons that were free.

**Warehouse receipts** get a lighter pass than online orders. An adjustment there costs the
member a trip to the Returns counter, groceries rarely change by enough to justify one, and
there is seldom a price to compare against. So only non-food items that cost $50 or more are
worth checking (the member can pick a different floor; pass it to the script as
`--warehouse-min`).

On Orders & Purchases, open the Warehouse tab and each "View Receipt" and "View Return Receipt"
from the last 30 days. A purchase receipt whose total is under the floor can't contain a
qualifying item, so leave it unopened. The receipt opens in a dialog; read its text
there (the print frame stays empty until Print is pressed). Lines are tab-separated:

```text
E   1234567   KS EXAMPLE     12.59 N     item line: number, short name, price
398765   / 1234567   2.60-               instant savings on that item: subtract it
2 @ 8.99                                 quantity for the line that follows
E   1068080   EXAMPLE EGGS   17.98 N     so this is 2 at 8.99 each
```

Skip deposit and fee lines, gas and food court receipts. Record the remaining lines, marking
food and drink with `"food": true`: lines that start with `E` are groceries, and the short name
settles the rest (a rotisserie chicken has no `E`). The script leaves food and anything under
the floor out without needing a price, and counts them as `warehouse_not_checked`.

**Returns.** A return receipt's lines carry the item numbers that went back. One marked
`RTC ECOM PURCHASE` is a Costco.com order returned at the warehouse, which is how an online
order that still appears on the form turns out to be returned. Mark returned lines
`"status": "returned"`.

**Requests already made by hand.** The form does not hide an order that has already had an
adjustment requested, so the ledger is the only thing preventing a duplicate. On the first
run, and whenever the ledger is empty, ask the user whether they have already filed any
requests themselves and record those first (step 5 shows the command).

Costco's pages change. Go by the visible labels and the page as it is, not by any structure
remembered from a previous run. Replace `purchases.json` with what the account shows now, so
returns and cancellations drop out.

### 2. Check current prices

For each distinct item number bought online, find its product page while signed in (searching
Costco.com for the item number,
`https://www.costco.com/CatalogSearch?keyword=<item number>`, usually lands on it) and confirm
the item number on the page matches. Record the price a member would pay today:

- The price is the "Online Price". If the page shows savings ("$80 OFF", "was $359.99", "valid
  11/16/26 through 12/20/26"), the Online Price already includes them, and the valid dates are
  `promo_start` and `promo_end`. A plain "Price valid through" date is `promo_end`.
- Record any "Limit N per member" as `limit`.
- If the page is out of stock, discontinued, shows a different pack size or colour under a
  different item number, or hides the price until the item is in the cart, there is no usable
  price. Don't add things to the cart or guess; report the item as "could not check".

For warehouse purchases, the Costco.com Online Price is not evidence (see "Same channel only"). A
warehouse price is known only when there is something to point at:

- a later receipt showing the same item cheaper;
- the product page's "Warehouse Price" under In-Warehouse, which is shown for the warehouse set
  as "My Warehouse" (check it is the one the item was bought at; the page warns prices vary);
- the current Member-Only Savings book listing that item number as an in-warehouse offer.

Look these up only for non-food warehouse items at or above the floor, and record them with
`"channel": "warehouse"`. Don't look up prices for the rest.

### 3. Work out what qualifies

```bash
uv run scripts/price_adjustments.py candidates --purchases ~/.costco-price-adjustment/purchases.json --prices ~/.costco-price-adjustment/prices.json --ledger ~/.costco-price-adjustment/ledger.json
```

The script applies the rules above (30-day window, same channel, promotion still running,
quantity limits, nothing requested twice) and prints:

- `run_again_by`: the date of the next check that matters, two days before the earliest window
  or promotion among purchases still open closes. Use it to time the next run.

- `candidates`: each with an `action` of `submit_form` (online) or `returns_counter`
  (warehouse), the expected credit before tax, the deadline, and for online orders the exact
  `form` values to enter. Sorted so the ones about to expire come first.
- `skipped`: every other purchase with the reason. Keep these for the report; "paid 24.99, now
  24.99" is how the user knows the check really happened.

Use the script's answer for dates and amounts so they are not worked out by hand.

### 4. Review with the user

Show the candidates before anything is sent:

| Item | Order | Bought | Paid | Now | Qty | Credit | Ask by |
|------|-------|--------|------|-----|-----|--------|--------|

Then the warehouse ones separately, as a list to take to the Returns counter. Ask which to
submit (see "Submitting is the user's call").

### 5. Submit each online request

Open <https://www.costco.com/PriceAdjustmentView>. One submission covers one item of one order.
Each question appears only after the one before it is answered, so an empty-looking form is
normal: answer, wait for the next field, continue. The form, top to bottom:

1. **When did you purchase the item?** Choose the Month and Year of the order. Only eligible
   purchase dates are offered, so an order missing from the form is one Costco considers
   ineligible; record that and move on.
2. **Order Number**: choose the order (shown as "order number - date").
3. **Select the item**: choose the item card whose item number matches. Check the price and
   quantity on the card against `purchases.json`; if they differ, stop and ask.
4. **Promotional Price** (a number field, shown once an item is chosen): the current price,
   digits only, such as `299.99`.
5. **Promotion Date** (optional, MM/DD/YYYY): the date the lower price started if the page
   showed it, otherwise the date it was seen.
6. **Comments** (optional, 240 characters): one plain sentence helps the reviewer, such as
   "Costco.com price for this item dropped to $299.99 on 11/12/2026."
7. Read the filled form back from the page and compare it with the candidate. Then press
   **Submit Request**.

After submitting, copy whatever confirmation the page shows and record the request straight
away, before starting the next one, so an interrupted run can't lead to a duplicate:

```bash
uv run scripts/price_adjustments.py record --ledger ~/.costco-price-adjustment/ledger.json --order 1234567890 --item 1234567 --promo-price 299.99 --promo-date 2026-11-12 --quantity 1 --credit 100.00 --confirmation "text shown after submitting"
```

If the page shows an error instead of a confirmation, don't resubmit blindly: reload the form
and see whether the order is still offered, and tell the user what the error said.

For a warehouse candidate the user says they have raised at the counter, record it with
`--channel warehouse --status asked_at_warehouse`.

### 6. Follow up on earlier requests

```bash
uv run scripts/price_adjustments.py pending --ledger ~/.costco-price-adjustment/ledger.json
```

This lists requests still waiting for a credit and marks those past 10 business days as
`overdue`. A credit shows up on the order's details or on the card statement, which the user
can check; when they confirm one, record it again with `--status credited`. For an overdue one,
suggest contacting Costco customer service with the order number and submission date. Record a
refusal with `--status denied` so the same price is not retried, while a later, lower price can
still be requested.

### 7. Report

Finish with a short summary:

- Submitted: item, order, credit expected, date the credit is due by. Total expected.
- To raise at the warehouse: item, receipt date, warehouse, paid and current price, last day.
- Could not check, and why.
- Earlier requests: credited, still waiting, overdue.
- How many purchases were checked and found unchanged, and how many warehouse lines were left
  unchecked as groceries or under the floor.

If nothing qualified, say so in one line with the count checked.

## Monitoring on a schedule

If the user asks for monitoring, set up a recurring run with whatever scheduler the agent has
and have it run this whole workflow. When to run follows from how Costco changes prices:

- **Monday or Tuesday morning, every week.** Member-Only Savings books run about four weeks and
  have started on Mondays, and other online prices tend to be set through a Sunday ("Price
  valid through" dates), so new prices mostly appear at the start of a week. A weekly run then
  catches each change within a day or two.
- **Daily from mid-November to the end of December,** and around other big sale events. Holiday
  deals start on scattered days and some last under a week, which a weekly run can miss
  entirely.
- **Before a window closes.** A price that drops on day 29 is still owed. The script's
  `run_again_by` gives the date; if it falls before the next regular run, add a one-off run
  then.

These dates are observed patterns, not a published calendar, so treat them as a default and
adjust if the user's items keep changing price on other days.

Decide with the user, when setting it up, what an unattended run may do, and write the answer
into the scheduled prompt itself:

- **Find and notify** (the default): do steps 1 to 4 and 6, then tell the user what is ready to
  submit. Nothing is sent until they say so.
- **Find and submit:** also do step 5 for online candidates without asking each time. Suggest a
  ceiling, such as asking first for any single credit above an amount they choose.

A scheduled run can only work while the browser's Costco session is still signed in. If it has
expired, the run should say so and stop rather than report "nothing found".
