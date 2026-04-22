

from pydantic import BaseModel, Field
from typing import Optional




class TicketCategory(BaseModel):
    """Classification output from LLM call #1."""
    department: str = Field(description="Department: Billing / Technical / Account / Other")
    urgency: str = Field(description="Urgency level: Critical / High / Normal / Low")


class TicketSummary(BaseModel):
    """Analysis output from LLM call #2."""
    issue_summary: str = Field(description="Brief 1-2 sentence summary of the issue")
    root_cause: str = Field(description="Likely root cause of the issue")
    suggested_action: str = Field(description="Suggested action for the support agent")
    sentiment: str = Field(description="Customer sentiment: Angry / Neutral / Satisfied")


class DraftReply(BaseModel):
    """Draft reply output from LLM call #3 (bonus node for Critical tickets)."""
    reply_text: str = Field(description="Professional reply to send to the customer")




class TicketInput(BaseModel):
    """Single raw ticket from CSV."""
    id: str
    subject: str
    body: str


class ProcessedTicket(BaseModel):
    """A fully processed ticket with all pipeline outputs."""
    id: str
    subject: str
    body: str
    department: Optional[str] = None
    urgency: Optional[str] = None
    issue_summary: Optional[str] = None
    root_cause: Optional[str] = None
    suggested_action: Optional[str] = None
    sentiment: Optional[str] = None
    draft_reply: Optional[str] = None




class PipelineState(BaseModel):
    """State that flows through the LangGraph pipeline."""
    raw_tickets: list[TicketInput] = Field(default_factory=list)
    processed_tickets: list[ProcessedTicket] = Field(default_factory=list)
    current_index: int = 0
    errors: list[str] = Field(default_factory=list)
