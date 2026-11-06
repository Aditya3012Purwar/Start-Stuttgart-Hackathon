"""SOCX - System of Context for Purchase-to-Pay.

A three-agent pipeline that turns a legacy ERP (a perfect system of records that
knows what happened but nothing about what it means) into a system of context:

    Agent 1  Context Miner      - collect what colleagues wrote/argued about
    Agent 2  Analyst/Validator  - test every claim against the data, find problems
    Agent 3  Advisor/Presenter  - route fixes to people, with evidence & provenance
"""

__version__ = "1.0.0"
