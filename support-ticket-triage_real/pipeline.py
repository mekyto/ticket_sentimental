import csv
import json
import os
import time

from dotenv import load_dotenv
from langgraph.graph import StateGraph, END

from models import (
    PipelineState,
    TicketInput,
    ProcessedTicket,
    TicketCategory,
    TicketSummary,
    DraftReply,
)
from prompts import (
    TICKET_CLASSIFICATION_SYSTEM,
    TICKET_CLASSIFICATION_USER,
    TICKET_ANALYSIS_SYSTEM,
    TICKET_ANALYSIS_USER,
    DRAFT_REPLY_SYSTEM,
    DRAFT_REPLY_USER,
)

load_dotenv()


from langchain_google_genai import ChatGoogleGenerativeAI

from langchain_groq import ChatGroq

def get_llm():
    return ChatGroq(
        model="llama-3.1-8b-instant",
        temperature=0.2,
    )


def llm_structured_call(system_prompt: str, user_prompt: str, output_model):
    llm = get_llm()
    structured_llm = llm.with_structured_output(output_model)
    messages = [
        ("system", system_prompt),
        ("human", user_prompt),
    ]
    result = structured_llm.invoke(messages)
    return result

#Node 1
def ingest_tickets(state: PipelineState) -> dict:
    print("\n📥 [Node 1] Ingesting tickets from CSV...")
    tickets = []
    csv_path = os.path.join(os.path.dirname(__file__), "tickets.csv")

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            tickets.append(TicketInput(
                id=row["id"],
                subject=row["subject"],
                body=row["body"],
            ))

    print(f"   ✅ Loaded {len(tickets)} tickets")
    return {
        "raw_tickets": tickets,
        "processed_tickets": [
            ProcessedTicket(id=t.id, subject=t.subject, body=t.body)
            for t in tickets
        ],
    }


#Node 2
def classify_tickets(state: PipelineState) -> dict:
    print("\n🏷️  [Node 2] Classifying tickets (LLM call #1)...")
    updated = list(state.processed_tickets)
    errors = list(state.errors)

    for i, ticket in enumerate(updated):
        try:
            user_prompt = TICKET_CLASSIFICATION_USER.format(
                ticket_id=ticket.id,
                subject=ticket.subject,
                body=ticket.body,
            )
            result: TicketCategory = llm_structured_call(
                TICKET_CLASSIFICATION_SYSTEM, user_prompt, TicketCategory
            )
            ticket.department = result.department
            ticket.urgency = result.urgency
            print(f"   Ticket #{ticket.id}: {result.department} / {result.urgency}")
            time.sleep(0.5)  
        except Exception as e:
            errors.append(f"Classification error on ticket #{ticket.id}: {e}")
            print(f"   ❌ Error on ticket #{ticket.id}: {e}")

    return {"processed_tickets": updated, "errors": errors}


#Node 3
def analyze_tickets(state: PipelineState) -> dict:
    print("\n🔍 [Node 3] Analyzing tickets (LLM call #2)...")
    updated = list(state.processed_tickets)
    errors = list(state.errors)

    for ticket in updated:
        try:
            user_prompt = TICKET_ANALYSIS_USER.format(
                ticket_id=ticket.id,
                subject=ticket.subject,
                body=ticket.body,
                department=ticket.department or "Unknown",
                urgency=ticket.urgency or "Unknown",
            )
            result: TicketSummary = llm_structured_call(
                TICKET_ANALYSIS_SYSTEM, user_prompt, TicketSummary
            )
            ticket.issue_summary = result.issue_summary
            ticket.root_cause = result.root_cause
            ticket.suggested_action = result.suggested_action
            ticket.sentiment = result.sentiment
            print(f"   Ticket #{ticket.id}: sentiment={result.sentiment}")
            time.sleep(0.5)
        except Exception as e:
            errors.append(f"Analysis error on ticket #{ticket.id}: {e}")
            print(f"   ❌ Error on ticket #{ticket.id}: {e}")

    return {"processed_tickets": updated, "errors": errors}


#Noode 4
def draft_replies(state: PipelineState) -> dict:
    print("\n✉️  [Node 4] Drafting replies for Critical tickets (LLM call #3)...")
    updated = list(state.processed_tickets)
    errors = list(state.errors)
    critical_count = 0

    for ticket in updated:
        if ticket.urgency and ticket.urgency.lower() == "critical":
            critical_count += 1
            try:
                user_prompt = DRAFT_REPLY_USER.format(
                    ticket_id=ticket.id,
                    subject=ticket.subject,
                    body=ticket.body,
                    issue_summary=ticket.issue_summary or "",
                    root_cause=ticket.root_cause or "",
                    suggested_action=ticket.suggested_action or "",
                )
                result: DraftReply = llm_structured_call(
                    DRAFT_REPLY_SYSTEM, user_prompt, DraftReply
                )
                ticket.draft_reply = result.reply_text
                print(f"   📝 Draft reply generated for ticket #{ticket.id}")
                time.sleep(0.5)
            except Exception as e:
                errors.append(f"Draft reply error on ticket #{ticket.id}: {e}")
                print(f"   ❌ Error on ticket #{ticket.id}: {e}")

    if critical_count == 0:
        print("   No Critical tickets found — skipping draft replies.")

    return {"processed_tickets": updated, "errors": errors}


#Node 5
def export_results(state: PipelineState) -> dict:
    """Export processed tickets to output files."""
    print("\n📤 [Node 5] Exporting results...")
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)

  
    tickets_data = [t.model_dump() for t in state.processed_tickets]
    json_path = os.path.join(output_dir, "triage_results.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(tickets_data, f, indent=2, ensure_ascii=False)
    print(f"   ✅ JSON saved to {json_path}")

   
    csv_path = os.path.join(output_dir, "triage_results.csv")
    if tickets_data:
        fieldnames = list(tickets_data[0].keys())
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(tickets_data)
        print(f"   ✅ CSV saved to {csv_path}")

   
    print("\n📊 Summary by Department:")
    dept_groups: dict[str, list] = {}
    for t in state.processed_tickets:
        dept = t.department or "Unknown"
        dept_groups.setdefault(dept, []).append(t)

    for dept, tickets in sorted(dept_groups.items()):
        print(f"\n   [{dept}] — {len(tickets)} ticket(s)")
        for t in tickets:
            print(f"     • #{t.id} [{t.urgency}] {t.subject}")
            if t.issue_summary:
                print(f"       Summary: {t.issue_summary}")

    if state.errors:
        print(f"\n⚠️  {len(state.errors)} error(s) occurred during processing.")

    return {}



def build_graph():
    """Construct and compile the LangGraph StateGraph."""
    graph = StateGraph(PipelineState)

    
    graph.add_node("ingest_tickets", ingest_tickets)
    graph.add_node("classify_tickets", classify_tickets)
    graph.add_node("analyze_tickets", analyze_tickets)
    graph.add_node("draft_replies", draft_replies)
    graph.add_node("export_results", export_results)

    
    graph.set_entry_point("ingest_tickets")
    graph.add_edge("ingest_tickets", "classify_tickets")
    graph.add_edge("classify_tickets", "analyze_tickets")
    graph.add_edge("analyze_tickets", "draft_replies")
    graph.add_edge("draft_replies", "export_results")
    graph.add_edge("export_results", END)

    return graph.compile()



def main():
    print("=" * 60)
    print("  🎫 Support Ticket Triage Pipeline")
    print("=" * 60)

    pipeline = build_graph()
    initial_state = PipelineState()
    final_state = pipeline.invoke(initial_state)

    print("\n" + "=" * 60)
    print("  ✅ Pipeline complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
