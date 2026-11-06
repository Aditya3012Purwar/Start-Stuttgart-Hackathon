# Development Question Set

These are the questions the business department actually asks. They are
phrased the way a person would phrase them, not the way a database would.

Use this set to calibrate your solution. **The jury evaluates against a
different, hidden set of questions phrased in the same style.** Hard-coding
the answers below will not help you and will be obvious in the demo.

Each question lists the expected answer so you can verify yourself.

---

## Warm-up - can you read the schema at all?

**Q1.** How many of our vendors are based in Germany?
> **177** of 340

**Q2.** How many purchase orders are in the system in total?
> **15,000**

**Q3.** What purchase order document types do we use?
> **NB** Standard purchase order, **UB** Stock transport order,
> **FO** Blanket purchase order, **ZRB** Scheduling agreement release

---

## Core - can you map process states?

**Q4.** How many supplier invoices are currently stuck in verification?
> **2,227**
> This is the single most important question in this case. "Stuck in
> verification" means the invoice has been recorded and has entered
> verification, but has not been approved for payment and has not been paid.

**Q5.** How many purchase orders are still waiting for approval?
> **1,136**

**Q6.** How many purchase orders have received only a partial delivery?
> **1,731**

**Q7.** How many invoices failed the three-way match and need a clerk to
look at them?
> **1,510**
> Note this is a different set from Q4. Q4 is normal processing, Q7 is the
> exception branch.

**Q8.** How many invoices are approved for payment but have not been paid
yet?
> **1,069**

---

## Advanced - can you get the numbers right?

**Q9.** What is the total value of the stuck invoices from Q4, in euro?
> **294,814,064.51 EUR**
> Not all invoices are in euro. Conversion uses the exchange rate table,
> taking the most recent rate valid on or before the posting date.

**Q10.** Which five vendors have the highest value tied up in stuck
invoices?
> 1. Rosenthal Technologies AG - 12 invoices, 2,886,307.65 EUR
> 2. Auerbach Industrial Systems KG - 16 invoices, 2,688,879.21 EUR
> 3. Birkenfeld Manufacturing KG - 16 invoices, 2,400,566.44 EUR
> 4. Kaltbrunn Components GmbH - 14 invoices, 2,281,376.75 EUR
> 5. Pflueger Components GmbH - 8 invoices, 2,205,928.58 EUR

**Q11.** What is the total net value of all purchase order items that are
actually valid?
> **1,998,331,067.40 EUR**
> If your answer is in the hundreds of billions, you have fallen into two
> traps at once. Both of them are described somewhere in the context
> sources.

**Q12.** Which vendors are blocked?
> **29 vendors**, among them Eichstaedt Technologies AG, Neuhaus
> Technologies AG, Pflueger Automotive GmbH, Sonntag Manufacturing KG and
> Zellweger Polymers GmbH.
> Careful: 3,737 invoices carry a payment block. That is a different concept
> and a different question. If you answered 3,737, you answered the wrong
> question.

**Q13.** How long does an invoice spend in verification on average?
> **7.36 days**
> The only reliable source for this is the processing history, not the
> current state of the documents.

**Q14.** For how many purchase orders have we received all the goods but
never got an invoice?
> **1,464**

**Q15.** Which invoice has been sitting in verification the longest?
> Document **0005103537**, vendor Neuhaus Technologies AG, posted
> 2025-01-20, 290,262.48 EUR.

---

## What good looks like

A strong answer does more than return a number. For Q4 the business does not
just want "2,227" - they want to know which invoices, from which vendors, how
much money is tied up, how long they have been sitting there, and why.

And they want to be able to check it. An answer no one can trace back to the
underlying records is worth very little in a finance department.
