# Mailbox Export - Accounts Payable / Procurement

Export of selected mail threads, provided by the business department for the
process transparency initiative. Personal data has been reduced. Threads are
reproduced in the order they were supplied and are not complete.

---

## Thread 1 - "Invoice list for the Monday review"

**From:** Sandra Weber (Accounts Payable)
**To:** Kai Mueller (Procurement Controlling)
**Date:** 2025-09-02

Kai,

I need the list of stuck invoices for the Monday review again. Same as last
month please: everything that is sitting in verification and has not been
released for payment yet, with vendor and amount.

Please do not just take everything that is unpaid - last time the list
included orders that were never even approved, and Thomas took that apart in
front of everyone.

Sandra

**From:** Kai Mueller
**Date:** 2025-09-02

Sandra,

I will put it together. Just so you know, the numbers will not match what the
old report produced. I checked with IT and the status codes in the data
catalogue are not what the system actually does. The document is from 2018
and was never corrected after the migration.

I am building the list from the change log instead, that at least reflects
what really happened to a document.

Kai

---

## Thread 2 - "Question on the supplier report"

**From:** Julia Hofmann (Procurement)
**To:** Kai Mueller
**Date:** 2025-07-18

Kai, your report shows an order volume of 4.2 million for Q2 but my own
figure is around 3.9. Where does the difference come from?

**From:** Kai Mueller
**Date:** 2025-07-18

Two things, and both of them bite everyone eventually.

First, deleted items. When a buyer cancels a single line, the line is not
removed, it is only flagged. If you do not filter those out you are counting
business that never happened.

Second, the price field. The net price is not per piece, it is per price
unit, and the price unit is not always one. For a lot of our C-parts it is
100 or 1000. If you multiply quantity by price without dividing by the price
unit you end up with numbers that are off by orders of magnitude.

Kai

---

## Thread 3 - "Vendor Steinwerk blocked?"

**From:** Ralf Bauer (Plant 1100)
**To:** Vendor Master Data
**Date:** 2025-05-27

Colleagues,

Purchasing tells me Steinwerk is blocked but I have three invoices from them
that were paid last month. Which is it now?

**From:** Vendor Master Data
**Date:** 2025-05-27

Mr Bauer,

There is a misunderstanding here that comes up constantly. A vendor block and
a payment block are two entirely different things, and they are stored in two
entirely different places. To make it worse both fields carry the same name
in the system.

Steinwerk is not blocked as a vendor. Individual invoices of theirs carry a
payment block because of price differences. Business with them continues
normally.

---

## Thread 4 - "USD invoices in the aging report"

**From:** Markus Keller (Controlling)
**To:** Sandra Weber
**Date:** 2025-08-11

Sandra,

The aging report sums document currency. We have USD and CNY suppliers in
there. Summing that up gives a number that means nothing at all.

There is a conversion rate table in the system with a valid-from date. The
rate that applies is the last one valid before the document date, not today's
rate. Whoever builds the next version of this report, please take that into
account.

Markus

---

## Thread 5 - "Handover note"

**From:** Thomas Schmidt (IT Applications)
**To:** Anna Fischer
**Date:** 2025-04-30

Anna,

As discussed, a few things you should know before I hand this over.

The data catalogue is the document everybody starts from and it is the single
biggest source of errors we have. Section 6 in particular. The status values
were partly redefined during the 2019 harmonisation and the document was
never updated. I raised it several times, it was never prioritised.

If you need to know what a status value actually means today, look at the
logging table. It records every status change with a timestamp, so you can
see the actual sequence documents go through. That sequence is the truth. The
catalogue is what somebody wrote down seven years ago.

The two custom tables are not documented at all. The release workflow table
is reasonably self-explanatory once you look at the data. The logging table
is the important one.

Thomas

---

## Thread 6 - "Re: Re: Re: escalation Hagenbach"

**From:** Sandra Weber
**To:** Julia Hofmann
**Date:** 2025-09-09

Julia,

Hagenbach is escalating again. They say four invoices are overdue. I checked,
all four are in verification because the invoiced quantity is higher than
what we received.

This is exactly the case I keep raising. From the supplier's point of view
they have invoiced us and heard nothing. From our point of view the invoice
is in a perfectly normal processing state. Neither side can see the other's
view, so it escalates every single time.

If we could simply answer "your invoice is in verification, reason is a
quantity difference, expected clearing date X" we would save ourselves half
of these calls.

Sandra
