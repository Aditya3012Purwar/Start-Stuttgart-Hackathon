# Data Catalogue - Procurement & Accounts Payable

**Document ID:** DK-MM-014
**Last full revision:** 2018-11-04
**Business owner:** T. Schmidt, IT Applications MM/FI
**Status:** maintained

> Editorial note: This document was last fully revised before the system
> harmonisation programme of 2019. Individual sections have been amended
> since then on an ad-hoc basis. A complete revision is still outstanding.
> In case of doubt, please consult the business department.

---

## 1. Vendor master (LFA1)

| Field | Meaning |
|-------|---------|
| LIFNR | Vendor number, 10 digits with leading zeros |
| NAME1 | Vendor name |
| LAND1 | Country key (ISO) |
| ORT01 | City |
| SPERR | Block indicator |
| ERDAT | Creation date |
| KTOKK | Account group |

## 2. Material master (MARA)

| Field | Meaning |
|-------|---------|
| MATNR | Material number, 18 digits |
| MTART | Material type (ROH = raw material, HALB = semi-finished) |
| MATKL | Material group |
| MEINS | Base unit of measure |
| MAKTX | Short text |
| LVORM | Deletion flag |

## 3. Purchase orders

### EKKO - purchasing document header

| Field   | Meaning |
|---------|---------|
| EBELN   | Purchase order number |
| BUKRS   | Company code (always 1000 in our system) |
| BSART   | Document type, see customizing table T161 |
| LIFNR   | Vendor |
| EKGRP   | Purchasing group |
| WAERS   | Document currency |
| AEDAT   | Creation date |
| ERNAM   | Created by |
| FRGKE   | Release indicator |
| STAT_KZ | Status indicator, see section 6 |

### EKPO - purchasing document item

| Field | Meaning |
|-------|---------|
| EBELN | Purchase order number |
| EBELP | Item number |
| MATNR | Material |
| WERKS | Plant |
| MENGE | Order quantity |
| NETPR | Net price |
| PEINH | Price unit |
| ELIKZ | Delivery completed indicator |
| LOEKZ | Deletion indicator |

## 4. Goods receipt

### MKPF / MSEG - material document

Goods receipts are represented as material documents. Header data resides in
MKPF, items in MSEG. The link back to the purchase order is established via
the fields EBELN and EBELP in MSEG.

BWART is the movement type. Goods receipt against a purchase order uses
movement type 101.

## 5. Invoice verification

### RBKP - invoice header

| Field   | Meaning |
|---------|---------|
| BELNR   | Document number |
| GJAHR   | Fiscal year |
| LIFNR   | Vendor |
| BLDAT   | Document date (date printed on the invoice) |
| BUDAT   | Posting date |
| RMWWR   | Gross invoice amount in document currency |
| SPERR   | Block indicator |
| ZLSPR   | Payment block |
| STAT_KZ | Status indicator, see section 6 |

### RSEG - invoice item

Invoice items with reference to the purchase order item (EBELN/EBELP).

## 6. Status indicator STAT_KZ

The field STAT_KZ records the processing stage of a document. The value range
was originally defined in project PRISMA.

| Value | Meaning |
|-------|---------|
| 10    | Purchase order created |
| 20    | Purchase order released |
| 30    | Goods receipt partially posted |
| 34    | Invoice verified and released |
| 40    | Goods receipt complete |
| 50    | Invoice recorded |
| 80    | Process completed |
| 90    | Cancelled |

> Remark: Additional values were introduced during the 2019 harmonisation.
> The corresponding documentation is held by the FI department and has not
> yet been incorporated here.

## 7. Financial accounting (BKPF)

The payment run creates documents with BLART = 'KZ'. Field AUGBL holds the
clearing document number, AUGDT the clearing date. An item counts as cleared
once AUGBL is populated.

AWKEY provides the reference back to the originating invoice verification
transaction.

## 8. Customizing

- **T161** - purchase order document types.
- **TCURR** - exchange rates. GDATU is the valid-from date. The applicable
  rate is the most recent one valid on or before the document date.

---

## Not yet documented

The following objects are known but have not been described yet:

- `ZTFRG` - in-house development, release workflow. Contact: Mr Weber.
- `ZTSTAT` - in-house development, logging table.
- `EKET` - schedule lines.
- Fields `SHKZG`, `XBLNR`, `USNAM` across several tables.
- The value range of `ZLSPR`.
