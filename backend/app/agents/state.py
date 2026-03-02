"""
DPP workflow state - LangGraph TypedDict.
EU AI Act Article 12 audit_entries, Article 14 requires_human_review.
v3.0: DDPLifecycleState for 9-phase lifecycle and 13-agent orchestration.
"""
from typing import Annotated, Any, Literal, Optional, TypedDict
from operator import add

# Message type for LangGraph (can use BaseMessage from langchain_core when needed)
TaskType = Literal[
    "compliance_check",
    "data_extraction",
    "product_lookup",
    "supply_chain_trace",
    "generate_dpp",
    "knowledge_query",
    "synthesize",
]

# v3.0: Lifecycle task types (YAML Maste.ini)
LifecycleTaskType = Literal[
    "ddp_generation",
    "compliance_check",
    "audit",
    "data_collection",
    "quality_control",
    "eol_assessment",
    "lifecycle_update",
]

# v3.0: Product lifecycle phases (0-9)
LifecyclePhase = Literal[
    "pre_conception",
    "design",
    "prototype",
    "supplier_qual",
    "manufacturing",
    "distribution",
    "active_use",
    "eol",
    "recycling",
    "destruction",
]


class DPPWorkflowState(TypedDict, total=False):
    """State for the 8-agent DPP workflow."""

    messages: Annotated[list, add]
    query: str
    product_gtin: Optional[str]
    task_type: TaskType

    # Agent outputs
    regulatory_analysis: Optional[dict[str, Any]]
    product_data: Optional[dict[str, Any]]
    supply_chain_trace: Optional[dict[str, Any]]
    compliance_status: Optional[dict[str, Any]]
    document_output: Optional[dict[str, Any]]
    knowledge_context: Optional[dict[str, Any]]

    # Quality control (EU AI Act Art. 14)
    confidence_scores: dict[str, float]
    audit_entries: list[dict[str, Any]]
    requires_human_review: bool
    human_feedback: Optional[str]
    regulation_references: list[str]
    final_response: Optional[str]


class DDPLifecycleState(TypedDict, total=False):
    """Extended state for v3.0 lifecycle workflows (9 phases, 13 agents)."""

    # Core identifiers
    product_gtin: Optional[str]
    serial_number: Optional[str]
    batch_number: Optional[str]
    ddp_uri: Optional[str]
    current_phase: LifecyclePhase
    task_type: LifecycleTaskType

    # Legacy / shared
    messages: Annotated[list, add]
    query: str
    regulatory_analysis: Optional[dict[str, Any]]
    product_data: Optional[dict[str, Any]]
    supply_chain_trace: Optional[dict[str, Any]]
    compliance_status: Optional[dict[str, Any]]
    document_output: Optional[dict[str, Any]]
    knowledge_context: Optional[dict[str, Any]]
    confidence_scores: dict[str, float]
    audit_entries: list[dict[str, Any]]
    requires_human_review: bool
    human_feedback: Optional[str]
    regulation_references: list[str]
    final_response: Optional[str]

    # DPP data (v3.0)
    ddp_data: Optional[dict[str, Any]]
    ddp_completeness: float
    validation_results: list[dict[str, Any]]
    compliance_score: float

    # Data quality
    data_quality_score: float
    anomalies_detected: list[dict[str, Any]]

    # End-of-life / second life
    second_life_pathway: Optional[str]
    recycling_data: Optional[dict[str, Any]]
    destruction_record: Optional[dict[str, Any]]

    # Audit workflow
    audit_scope: Optional[dict[str, Any]]
    audit_findings: list[dict[str, Any]]
    audit_report: Optional[dict[str, Any]]
    corrective_actions: list[dict[str, Any]]
