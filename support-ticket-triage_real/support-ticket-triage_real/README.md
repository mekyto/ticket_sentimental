# 🎫 Support Ticket Triage — LangGraph + Gemini Pipeline

An automated customer support ticket triage system built with **LangGraph**, **Google Gemini**, and **Pydantic Structured Outputs**.

## Overview

This pipeline reads support tickets from a CSV file and automatically:
1. **Classifies** each ticket by department and urgency
2. **Analyzes** each ticket to extract summaries, root causes, suggested actions, and sentiment
3. **Drafts replies** for critical-urgency tickets
4. **Exports** structured results to JSON and CSV

## Pipeline Architecture

```
[Node 1: Ingest Tickets]  — Parse CSV input
         ↓
[Node 2: Classify Tickets] — LLM Call #1 → TicketCategory (department + urgency)
         ↓
[Node 3: Analyze Tickets]  — LLM Call #2 → TicketSummary (summary, root cause, action, sentiment)
         ↓
[Node 4: Draft Replies]    — LLM Call #3 (Bonus) → DraftReply for Critical tickets only
         ↓
[Node 5: Export Results]   — Save to JSON + CSV, print summary
```

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Orchestration | LangGraph (StateGraph) |
| LLM | Google Gemini 2.0 Flash (free tier) |
| Structured Outputs | Pydantic v2 models |
| State Management | Pydantic BaseModel as LangGraph state |

## Project Structure

```
├── pipeline.py        # Main LangGraph pipeline (5 nodes)
├── models.py          # Pydantic models (state + structured outputs)
├── prompts.py         # All LLM prompts as named constants
├── tickets.csv        # Sample input data (10 tickets)
├── requirements.txt   # Python dependencies
├── .env.example       # Environment variable template
├── output/
│   ├── triage_results.json   # Full structured output
│   └── triage_results.csv    # Tabular output
└── README.md
```

## Setup & Run

1. **Clone the repo**
   ```bash
   git clone <your-repo-url>
   cd support-ticket-triage
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set your Gemini API key**
   ```bash
   cp .env.example .env
   # Edit .env and paste your key from https://aistudio.google.com/apikey
   ```

4. **Run the pipeline**
   ```bash
   python pipeline.py
   ```

## Pydantic Models

**TicketCategory** — LLM structured output for classification:
- `department`: Billing / Technical / Account / Other
- `urgency`: Critical / High / Normal / Low

**TicketSummary** — LLM structured output for analysis:
- `issue_summary`: Brief description of the issue
- `root_cause`: Likely root cause
- `suggested_action`: Recommended action for support agent
- `sentiment`: Angry / Neutral / Satisfied

**DraftReply** (bonus) — Auto-generated reply for Critical tickets:
- `reply_text`: Professional customer-facing reply

## Sample Output

See `output/triage_results.json` for full structured results after running the pipeline.

## Requirements Met

- ✅ LangGraph StateGraph with 5 nodes (min. 3 required)
- ✅ State as a Pydantic model (`PipelineState`)
- ✅ 3 LLM calls with Pydantic Structured Outputs (min. 2 required)
- ✅ 3 Pydantic output models (min. 2 required)
- ✅ `prompts.py` with all prompts as named constants
- ✅ Bonus: 4th node generates draft replies for Critical tickets
