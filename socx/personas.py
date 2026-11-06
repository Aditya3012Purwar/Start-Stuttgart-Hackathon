"""The people this system is built for.

Every persona is a real role from the case materials (the mail threads, the
tickets, the process document's audience). Findings and answers are routed to
whoever can actually act on them.
"""

PERSONAS = {
    "ap_clerk": {
        "name": "Accounts Payable",
        "who": "Sandra Weber - and the retiring colleague whose knowledge of the codes is written down nowhere",
        "cares_about": "Which invoices are stuck, for whom, how much, how long, and why",
        "pain": "Builds the Monday stuck-invoice list by hand; got it wrong in front of the room",
        "icon": "AP",
    },
    "procurement": {
        "name": "Procurement / Controlling",
        "who": "Kai Mueller, Julia Hofmann, plant buyers (Ralf Bauer)",
        "cares_about": "Correct order volumes, open receipts, approvals, supplier reports",
        "pain": "1.5 days of spreadsheets a month; figures that never reconcile",
        "icon": "PR",
    },
    "controlling": {
        "name": "Financial Controlling",
        "who": "Markus Keller",
        "cares_about": "Aging and value reports with correct currency conversion",
        "pain": "Aging report sums mixed currencies and means nothing",
        "icon": "FC",
    },
    "vendor_master": {
        "name": "Vendor Master Data",
        "who": "The team that sets vendor blocks",
        "cares_about": "Vendor vs payment vs verification blocks kept distinct",
        "pain": "Same-named fields cause constant 'is this vendor blocked?' confusion",
        "icon": "VM",
    },
    "it_apps": {
        "name": "IT Applications (MM/FI)",
        "who": "Thomas Schmidt (handing over) and Anna Fischer (inheriting)",
        "cares_about": "Capturing the tribal knowledge before it walks out the door",
        "pain": "The catalogue is the biggest source of errors; nobody fixed it",
        "icon": "IT",
    },
    "audit": {
        "name": "Internal Audit",
        "who": "Named audience of the process document",
        "cares_about": "Provenance - which rule, which source, which document numbers",
        "pain": "Answers no one can trace are worthless in a finance department",
        "icon": "AU",
    },
}
