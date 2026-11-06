# Purchase-to-Pay - Process Description

**Document:** BPD-P2P-2.3
**Author:** External consultancy, process transparency initiative
**Date:** 2023-06-15
**Audience:** business departments, internal audit

This document describes the target purchase-to-pay process as agreed with
Procurement and Accounts Payable. It deliberately contains no references to
technical system objects. A mapping to the underlying application tables was
planned as work package 4 but was descoped.

---

## 1. Overview

The purchase-to-pay process covers everything from the moment a demand is
raised until the supplier's money leaves the building.

```
  Demand  ->  Purchase order  ->  Approval  ->  Goods receipt
                                                     |
                                                     v
        Payment  <-  Payment release  <-  Invoice verification
```

## 2. Process steps

### 2.1 Purchase order creation

A buyer creates a purchase order against a vendor. The order carries one or
more items, each referencing a material, a quantity and an agreed price.
At this point the order is not yet legally binding on our side.

### 2.2 Approval

Depending on order value and purchasing group, an order requires approval by
one or more approvers. Until the order is fully approved, no goods may be
received against it. Orders can remain in this state for weeks - this is one
of the most common causes of delayed deliveries.

The business refers to an unapproved order as **"sitting in the approval
queue"** or **"waiting for release"**.

### 2.3 Goods receipt

When the goods physically arrive at the plant, the warehouse posts a goods
receipt. A receipt may be **partial** - the supplier delivers less than
ordered - or **complete**. A purchase order item is only considered closed
once the delivery is flagged as finished.

Partial deliveries that never complete are referred to as **"open
receipts"** and are a recurring topic in the monthly operations review.

### 2.4 Invoice verification

The supplier sends an invoice. Accounts Payable checks it against the
purchase order and the goods receipt. This check is known as the
**three-way match**:

1. Does the invoice reference a valid purchase order?
2. Were the goods actually received?
3. Do quantity and price match what was agreed?

If all three agree, the invoice may proceed. If any one of them deviates, the
invoice is **blocked** and must be clarified with the supplier or the buyer.
The most frequent reason for a block is a **price variance** or an invoiced
quantity exceeding the quantity received.

**Important:** an invoice that has been recorded in the system is not the
same as an invoice that has been approved for payment. Between those two
states sits the verification step, and invoices routinely spend weeks in it.
When the business asks which invoices are **"stuck"**, they mean exactly
this: recorded, not yet approved for payment, not yet paid.

### 2.5 Payment release

Once verification is complete and all deviations are cleared, the invoice is
released for payment. Only from this point onwards is the invoice eligible
for the payment run.

### 2.6 Payment

The payment run selects all released invoices that are due and settles them.
Settlement produces an accounting document. An invoice counts as **paid**
only once it has been cleared by such a document.

---

## 3. Blocks - a note on terminology

The word "block" is used loosely in day-to-day conversation and refers to at
least three different things:

- A **vendor block** stops any new business with a supplier entirely. It is
  set centrally by Vendor Master Data, usually for compliance reasons.
- A **verification block** is set during invoice verification when the
  three-way match fails.
- A **payment block** prevents an otherwise valid invoice from being picked
  up by the payment run. It may be set automatically by the system or
  manually by an accountant.

These are independent of each other. An invoice can carry a payment block
while the vendor itself is perfectly active, and vice versa.

---

## 4. Known pain points

Raised repeatedly by the business during the workshops:

- Nobody can answer the question *"where exactly is this invoice right now"*
  without calling three different people.
- Reporting on stuck invoices is produced manually in spreadsheets and is
  usually two weeks out of date by the time it is circulated.
- The meaning of the status values in the system is not reliably documented.
  Several participants stated that the existing data catalogue is
  **"partly wrong since the migration"**, but nobody could say which parts.
- Cancelled and deleted items are frequently included in reports by mistake,
  which inflates the reported order volume.
