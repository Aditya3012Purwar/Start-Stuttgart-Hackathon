# From System of Records to System of Context

**Hackathon Case - Purchase-to-Pay in a legacy ERP landscape**

---

## The situation

You have just been handed access to the production database of a fictional
automotive supplier. It has been running for twenty years. It contains every
purchase order, every delivery, every supplier invoice and every payment the
company has ever processed.

It is a perfect **system of records**. It knows exactly *what* happened.

It knows nothing about what any of it *means*.

Open `data/schema.sql` and you will find a table called `RBKP` with a column
called `STAT_KZ`. One of the values in that column is `34`. Somewhere in the
building there is a woman in Accounts Payable who knows that `34` means a
supplier invoice is sitting in verification and cannot be paid. She has known
it since the system was harmonised in 2019, when a number of these codes
quietly changed meaning. It is written down nowhere.

When she retires, that knowledge leaves with her.

Meanwhile the business asks questions like *"which supplier invoices are
stuck?"* and *"how much money is tied up in them?"* - and answering them
takes a specialist a day and a half of manual spreadsheet work, every single
month.

## Your mission

**Build a system of context on top of the system of records.**

Something that can take a question phrased in business language, understand
what it means in terms of this database, answer it correctly, and show its
work.

That is the whole brief. How you get there is up to you.

---

## Setup (should take under five minutes)

Requires **Python 3.10 - 3.14**. Check with `python --version` before you
start. Everything else installs in one step.

**macOS / Linux**

```bash
git clone <repo-url>
cd <repo>

python3 -m venv .venv
source .venv/bin/activate

python -m pip install -r requirements.txt

cp .env.example .env
# paste the API key you were given at the kickoff into .env

python setup.py               # health check, tells you what is missing
python baseline.py
```

**Windows (PowerShell)**

```powershell
git clone <repo-url>
cd <repo>

python -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install -r requirements.txt

Copy-Item .env.example .env
notepad .env                  # paste the key from the kickoff, then save

python setup.py
python baseline.py
```

Use `python -m pip`, not `pip`. On a managed corporate laptop `pip.exe` is
often blocked outright while the module behind it works fine - see
troubleshooting below.

No database server. No Docker. No credentials beyond the one API key.
`data/erp_legacy.db` is a plain SQLite file - `sqlite3.connect()` and you are
in. The repo is around 45 MB because the database is real.

**The extract was taken on 1 March 2026.** Nothing in the data is dated after
that. When a question says "currently" or "still", that is the date it means.

**If you are not querying data within ten minutes of sitting down, stop and
grab an organiser.** That is a problem with our setup, not with you.

### Troubleshooting

Four failures account for nearly everything that goes wrong on a corporate
Windows machine. None of them are your fault and none take longer than a
minute to fix.

**`pip` fails with "Zugriff verweigert" / "Access is denied"**

Your endpoint protection blocks `pip.exe` as a package manager. The Python
module underneath is not blocked. Use it instead:

```powershell
python -m pip install -r requirements.txt
```

**`python` opens the Microsoft Store**

Python is not on your PATH and Windows is offering you its own. Either
reinstall from python.org with **Add python.exe to PATH** ticked, or switch
the aliases off under *Settings > Apps > Advanced app settings > App
execution aliases* - both `python.exe` and `python3.exe`.

**`Activate.ps1 cannot be loaded because running scripts is disabled`**

PowerShell's execution policy. This is a per-user setting, not a system
change:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

**Do not put `.venv` inside OneDrive**

If your `Documents` folder syncs to OneDrive, clone somewhere local such as
`C:\hack\` instead. A synced virtual environment means thousands of files
churning through the sync client, and OneDrive placeholder files can refuse
to execute. The database and the context files are fine in OneDrive; the
virtual environment is not.

If none of these is your problem, grab an organiser rather than losing the
morning to it.

---

## What is in the repo

```
data/
  erp_legacy.db       the production database. 1,274 tables, 310k rows in
                      the fourteen that matter.
  schema.sql          DDL of the 14 tables a colleague says are relevant.
                      He put the list together by hand. He is not certain
                      it is complete.
  schema_full.sql     DDL of all 1,274 tables. ~95,000 tokens.
  incoming_documents.jsonl
                      31 documents that were processed recently. For level 3.

context/
  GLOSSARY.md         the official data catalogue. Last full revision 2018.
  PROCESS.md          how the business describes the process. No table names.
  tickets.jsonl       43 support tickets spanning eight months of 2025.
  emails.md           mail threads from Accounts Payable and Procurement.

questions.md          15 questions with verified answers. Calibrate on these.
setup.py              health check.
baseline.py           naive text-to-SQL. Your starting point and your enemy.
```

**Read that first entry again.** The database has 1,274 tables. `schema.sql`
contains 14 of them because somebody sat down and guessed which ones matter.
You can work from that extract all day and get a long way - the questions in
`questions.md` are answerable from those 14 tables.

But the extract is a crutch, and we will take it away in the demo.

There are also tables in there named `EKKO_BAK`, `RBKP_SHADOW`, `ZRBKP_STG`,
`ZTSTAT_OLD` and `RBKP_ARCH`. Some are stale copies, some are half-loaded
staging areas, one is an archive. They contain data that looks entirely
plausible. Deciding which table to trust is part of the job.

The context sources are deliberately messy. They are incomplete, they
overlap, they were written at different times by different people, and **at
least one of them is confidently wrong about something important.** Working
out which source to trust when they disagree is not an annoying side quest.
It is the case.

### On resolving contradictions

You will find disagreements between the sources. The obvious move is to pick
whichever source feels more trustworthy. Resist it.

Counting sources does not work either - three documents saying the same thing
may all have copied the same outdated original. A majority is not evidence.

What does work: **turn the claim into a prediction and check it against the
data.** If a document asserts that a status code means "approved", then
documents in that status should behave in a particular way. They either do or
they do not. The database cannot be argued with.

Doing this once by hand is worth a few points. Building something that does
it systematically - so that it still works on a claim you have not seen - is
what the case is actually asking for.

---

## The north star question

Every team must be able to answer this one, live, at the end of the day:

> **"Which supplier invoices are currently stuck, how much money is tied up
> in them, and why are they stuck?"**

If your system can answer that correctly and show where each part of the
answer came from, you have built something real.

---

## Level 3 - optional, only if you get there

Nobody is expected to reach this. It exists so that teams who finish early
have somewhere to go, and it is where the case stops being a reporting
exercise.

`data/incoming_documents.jsonl` contains 31 documents that moved through the
system in the weeks before the extract. Each one carries its processing
history.

> **Which of these look wrong, and why?**

Nobody will tell you what "wrong" means. But if your system has understood
the process from the historical data, it already knows what normal looks
like - and anything it knows to be normal, it can use as a yardstick.

Three warnings, in increasing order of importance:

1. Not everything unusual is broken. Some of these documents are rare but
   perfectly legitimate. A system that flags every outlier is useless - on a
   real system with 1.5 million documents a 5% false positive rate means
   75,000 alerts and an inbox nobody opens.
2. Not every anomaly is visible in the history alone. At least one document
   looks entirely normal until you check it against the ERP data.
3. **An alert nobody can act on is worse than no alert.** "This document is
   anomalous, score 0.87" is noise. "This invoice was paid without ever
   entering verification - 0 of 7,755 historical invoices did that" is
   something a person can pick up the phone about.

---

## Rules

**Allowed:** anything. Any library, any architecture, any model available
through the key you were given. Knowledge graphs, vector stores, fine-tuned
classifiers, a handwritten YAML file - no approach is out of bounds.

**Token cost is not a constraint today.** The budget is sponsored and it is
generous. Spend it. But be ready to answer what your approach would cost per
query against the full 1,274-table database.

**Not allowed:** editing `data/` or `questions.md`. The database is
read-only - treat it as a production system you have been given a replica of.

**A warning about knowledge graphs.** Several of you will want to stand up
Neo4j. In an eight-hour event that is a trap. If a graph is the right answer
for you, build it in memory with NetworkX or in SQLite and spend your time on
the semantics instead of on infrastructure. We will not award points for the
logo on your database.

---

## How you will be judged

| Criterion | Weight | What we are looking for |
|---|---:|---|
| **Context quality** | 35% | Are the answers right? Did you spot the contradictions between sources - and can you show *how* your system decided, rather than how you decided? |
| **Generalisation** | 25% | We will ask questions you have not seen, phrased the same way as the ones in `questions.md`. |
| **Scalability** | 20% | Does your system work against all 1,274 tables, not just the 14 in the extract? We will ask you to try it. |
| **Demo & value** | 20% | Five minutes, live, no slides. Convince the woman in Accounts Payable. |

Level 3 is not scored separately. It counts towards context quality, and it
is the strongest evidence you can offer that your system understood the
process rather than memorised a set of answers.

### On provenance

An answer nobody can verify is worthless in a finance department. A system
that says *"2,227 invoices, and here are the document numbers, the rule I
applied, and the source I learned that rule from"* beats a system that says
*"2,227"* - even if the number is identical.

---

Case owner is in the room all day. **Ask questions.** Working out what
`ZTFRG` means by staring at it is not a good use of your afternoon; working
out how to make a system do it for you is.

---

## A suggested first hour

Not a requirement, just what we would do.

1. Run `baseline.py`. Watch it answer the north star question. Check the
   answer against `questions.md`. Notice that it is wrong.
2. Work out *why* it is wrong. This is the most valuable twenty minutes of
   your day.
3. Read `context/PROCESS.md` - you will not get far without understanding
   what a three-way match is.
4. Only then start designing. The teams that win events like this are the
   ones who understood the problem before they started typing.

Good luck.
