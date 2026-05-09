# Improvement Demonstration

## Identified Issue

The router only detected the word "citation" for citation-related queries.
Queries using words like "reference" or "paper" were incorrectly routed.

---

## Before Fix

Query:
"Check references in paper"

Result:
- Citation agent NOT triggered
- Incorrect response returned

Feedback:
Bad

---

## Fix Applied

Expanded router keyword matching:

- citation
- reference
- paper
- doi
- metadata

---

## After Fix

Query:
"Check references in paper"

Result:
- Citation agent triggered correctly
- Citation verification successful

Feedback:
Good

---

## Outcome

Routing accuracy improved and citation-related failures decreased.