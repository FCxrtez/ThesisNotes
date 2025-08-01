# Thesis Notes – README

This repository contains all the working notes, logs, experiments, and readings related to my thesis. The structure is designed to be simple, clean, and scalable over time.

## Directory Structure
---

## 00_Log/
**Purpose:** Time-based daily logs. One file per day, named as `YYYY-MM-DD.txt`.

**Use cases:**
- Track daily progress
- Write open-ended thoughts or reflections
- Link to deeper notes (see below)

## 01_Topics/
**Purpose:** Topic-specific notes and summaries (e.g., “L1 cache behavior”, “Directory protocols”).

Use when you want to:
- Deep dive into a technical concept
- Summarize lessons from multiple sources
- Write canonical notes to reuse in the thesis

File naming: use underscores for multiple words (e.g., `cache_hierarchy.md`)

---

## 02_Papers/
**Purpose:** Notes from academic papers or books.

Each file should contain:
- Title and citation of the paper/book
- Key takeaways
- Diagrams (if useful, can be described or saved separately)
- Questions or critiques

Optional: start filenames with short tags, e.g., `HP_book_ch4.md`

---

## 03_Experiments/
**Purpose:** Notes from experiments, simulations, benchmarks, and validation work.

Each file should contain:
- Description of setup
- Parameters used (e.g., cache sizes, workloads)
- Observed results (tables/plots can be external)
- Observations, hypotheses, or surprises

Prefix files with `exp_` (e.g., `exp_gem5_l1_latency.md`)

---

## 04_Todo_Lists/
**Purpose:** Track short- and long-term goals, and keep organized weekly plans.

Suggested files:
- `week_YYYY-MM-DD.md`: weekly to-do list and goals
- `long_term.md`: rough roadmap
- `questions_for_advisor.md`: accumulate open questions

## Tips & Conventions

- Use links between files for cross-referencing (e.g., `See: ../02_Papers/MESI_paper.md`)
- At the end of each week, write a short summary and reflect on what was learned.
- Tag potentially useful writing material with `#writing_candidate` or `#figure_needed`.
- File and folder naming conventions keep things sorted:

-- **Dates:** YYYY-MM-DD.txt to ensure correct order.
-- **Topics:** Use underscores and lowercase: gem5_coherence_analysis.txt
-- **Experiments:** exp_[short_description].txt
