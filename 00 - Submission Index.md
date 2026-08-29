# Submission — Decoding Customer Value: A SQL-Driven Retention Strategy

**Summer Projects '26 · Consulting & Analytics Club, IIT Guwahati** · Submitted by Raman Mishra
**POC:** Achyuth · Dhairya Nisar

---

## The answer (read this first)

*Is the brand building a loyal base, or reliant on promotions?* **Neither story is true.** The brand has a genuinely committed base it is failing to *activate*; promo reliance is modest and concentrated, while under-activation is large and fixable.

- **15.8% of revenue ($36,766)** is plausibly discount-caused — the entire measurable promo exposure. Discount dependency is **not** the core problem.
- **26.9% of revenue ($62,645)** flows through subscriber discounts whose necessity is untested by design.
- **969 "committed-but-slow" customers (25% of base)** carry a **~$996k value gap** to their activated equivalents — **2.7x the size** of the measurable promo exposure, and the single largest opportunity.

Loyalty was **defined, not declared** — two competing definitions (behavioral vs. commitment-based) built, tested, and the commitment definition adopted; an automated definition-search with a planted-signal control confirmed no data-mined alternative beats it.

---

## Deliverables in this folder

| # | File | What it is | Satisfies |
|---|---|---|---|
| **D1** | `D1 - Engineered Data.xlsx` · `D1 - Feature Engineering (Python)/` | Cleaned dataset + engineered features (dependency score, value tier, satisfaction flag); the 6 Python scripts that build them, with logic per feature | Python |
| **D2** | `D2 - Segmentation Queries.sql` · `D2 - SQL Results/` | Segmentation queries answering all 5 key business questions, plus the exported result table for each | SQL |
| **D3** | `D3 - Founder Dashboard (Power BI)/` + `D3 - Founder Dashboard (static preview).pdf` | Four-panel founder dashboard (pyramid · segments · geo · category) + a static PDF preview that opens without Power BI | Power BI |
| **D4** | `D4 - Retention Playbook.pdf` | Promotional sunset plan + ideal customer profile, each with named segment, trigger, timeline, tracked metric, and trade-off | Playbook |
| **D5** | `D5 - Executive Summary.pdf` | One-page findings + recommendations under either scenario | Summary (max 1 page) |

## How to open

- **D1** — `D1 - Engineered Data.xlsx` opens in Excel; the Python scripts run in order (`01_clean` → `06_playbook_numbers`).
- **D2** — open the `.sql` in any client, or read pre-exported answers in `D2 - SQL Results/`.
- **D3** — `D3 - Founder Dashboard (static preview).pdf` opens anywhere (no install); for the interactive version open `RetentionDashboard.pbip` in Power BI Desktop (free).
- **D4 / D5** — PDFs, zero-install.
