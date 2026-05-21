
from sqlmodel import SQLModel, Field, Relationship, Column, JSON
from sqlalchemy import UniqueConstraint
import sqlalchemy as sa
from typing import Optional, List, Any
from datetime import datetime


class Project(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    description: Optional[str] = None

    cards: List["Card"] = Relationship(back_populates="project", sa_relationship_kwargs={"cascade": "all, delete-orphan"})



class LLMConfig(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    provider: str = Field(index=True)
    display_name: Optional[str] = None
    model_name: str
    api_base: Optional[str] = None
    api_key: str
    api_protocol: str = Field(
        default="chat_completions",
        sa_column=Column(sa.String, nullable=False, server_default="chat_completions"),
    )
    custom_request_path: Optional[str] = None
    models_path: Optional[str] = None
    user_agent: Optional[str] = None
    base_url: Optional[str] = None  # Legacy field; current implementation uses api_base
    token_limit: int = Field(
        default=-1,
        sa_column=Column(sa.Integer, nullable=False, server_default='-1')
    )
    call_limit: int = Field(
        default=-1,
        sa_column=Column(sa.Integer, nullable=False, server_default='-1')
    )
    used_tokens_input: int = Field(
        default=0,
        sa_column=Column(sa.Integer, nullable=False, server_default='0')
    )
    used_tokens_output: int = Field(
        default=0,
        sa_column=Column(sa.Integer, nullable=False, server_default='0')
    )
    used_calls: int = Field(
        default=0,
        sa_column=Column(sa.Integer, nullable=False, server_default='0')
    )
    rpm_limit: int = Field(
        default=-1,
        sa_column=Column(sa.Integer, nullable=False, server_default='-1')
    )
    tpm_limit: int = Field(
        default=-1,
        sa_column=Column(sa.Integer, nullable=False, server_default='-1')
    )


class Prompt(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    key: Optional[str] = Field(default=None, index=True)
    name: str = Field(unique=True, index=True)
    description: Optional[str] = None
    template: str
    version: int = 1
    built_in: bool = Field(default=False)



class CardType(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    key: Optional[str] = Field(default=None, index=True)
    name: str = Field(index=True)
    model_name: Optional[str] = Field(default=None, index=True)
    description: Optional[str] = None
    json_schema: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    ai_params: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    editor_component: Optional[str] = None  # e.g., 'NovelEditor' for custom UI
    is_ai_enabled: bool = Field(default=True)
    is_singleton: bool = Field(default=False)  # e.g., only one 'Synopsis' card per project
    built_in: bool = Field(default=False)
    default_ai_context_template: Optional[str] = Field(default=None)
    default_ai_context_template_review: Optional[str] = Field(default=None)
    ui_layout: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    cards: List["Card"] = Relationship(back_populates="card_type")


class Card(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    model_name: Optional[str] = Field(default=None, index=True)
    content: Any = Field(default={}, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.now, nullable=False)

    json_schema: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    ai_params: Optional[dict] = Field(default=None, sa_column=Column(JSON))

    parent_id: Optional[int] = Field(default=None, foreign_key="card.id")
    parent: Optional["Card"] = Relationship(
        back_populates="children",
        sa_relationship_kwargs={"remote_side": "[Card.id]"}
    )
    children: List["Card"] = Relationship(
        back_populates="parent",
        sa_relationship_kwargs={
            "cascade": "all, delete, delete-orphan",
            "single_parent": True,
        },
    )

    project_id: int = Field(foreign_key="project.id")
    project: "Project" = Relationship(back_populates="cards")

    card_type_id: int = Field(foreign_key="cardtype.id")
    card_type: "CardType" = Relationship(back_populates="cards")

    display_order: int = Field(default=0)
    ai_context_template: Optional[str] = Field(default=None)
    ai_context_template_review: Optional[str] = Field(default=None)

    ai_modified: bool = Field(default=False)  # Whether AI modified it
    needs_confirmation: bool = Field(default=False)  # Whether user confirmation is needed for workflow triggers
    last_modified_by: Optional[str] = Field(default=None)  # Last modifier: user | ai | None

class ForeshadowItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id")
    chapter_id: Optional[int] = Field(default=None)  # Chapter card ID or chapter ID
    title: str
    type: str = Field(default='other', index=True)  # goal | item | person | other
    note: Optional[str] = None
    status: str = Field(default='open', index=True)  # open | resolved
    created_at: datetime = Field(default_factory=datetime.now, nullable=False)
    resolved_at: Optional[datetime] = None


class Knowledge(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    key: Optional[str] = Field(default=None, index=True)
    name: str = Field(unique=True, index=True)
    description: Optional[str] = None
    content: str
    built_in: bool = Field(default=False)


class Workflow(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    description: Optional[str] = None
    dsl_version: int = Field(default=2)  # DSL version: 2=code workflow
    is_built_in: bool = Field(default=False)
    is_active: bool = Field(default=True)

    definition_code: str = Field(default="")  # Workflow code

    is_template: bool = Field(default=False)
    template_category: Optional[str] = None  # Example: content generation, data processing

    keep_run_history: bool = Field(default=False)

    triggers_cache: Optional[List[dict]] = Field(default=None, sa_column=Column(JSON))
    """Trigger cache extracted automatically from code.

    Structure:
    [
        {
            "trigger_on": "onsave",           # Trigger event type
            "card_type_name": "chapter",      # Optional card type
            "filter_json": {                  # Optional filter config
                "events": ["create", "update"],
                "conditions": [...]
            }
        },
        ...
    ]

    Benefits:
    - Startup performance improves by 100x (5ms vs 500ms)
    - Avoids data duplication and sync issues
    - Code is the single source of truth
    """

    created_at: datetime = Field(default_factory=datetime.now, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.now, nullable=False)

    # Relations
    runs: List["WorkflowRun"] = Relationship(back_populates="workflow", sa_relationship_kwargs={
        "cascade": "all, delete-orphan"
    })


class WorkflowRun(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    workflow_id: int = Field(foreign_key="workflow.id")
    workflow: Workflow = Relationship(back_populates="runs")

    definition_version: int = Field(default=1)
    # queued | running | succeeded | failed | cancelled | paused | timeout
    status: str = Field(default="queued", index=True)
    scope_json: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    params_json: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    idempotency_key: Optional[str] = Field(default=None, index=True)

    state_json: Optional[dict] = Field(default=None, sa_column=Column(JSON))  # Runtime state: variables, node outputs, etc.
    error_json: Optional[dict] = Field(default=None, sa_column=Column(JSON))  # Error information

    max_execution_time: Optional[int] = None  # Seconds; None means unlimited

    created_at: datetime = Field(default_factory=datetime.now, nullable=False)
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    summary_json: Optional[dict] = Field(default=None, sa_column=Column(JSON))

    # Relations
    node_states: List["NodeExecutionState"] = Relationship(back_populates="run", sa_relationship_kwargs={
        "cascade": "all, delete-orphan"
    })


class NodeExecutionState(SQLModel, table=True):
    __tablename__ = "nodeexecutionstate"
    __table_args__ = (
        UniqueConstraint('run_id', 'node_id', name='uq_run_node'),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    run_id: int = Field(foreign_key="workflowrun.id", index=True)
    run: WorkflowRun = Relationship(back_populates="node_states")

    node_id: str = Field(index=True)  # Node ID from DSL
    node_type: str  # Node type

    status: str = Field(default="idle", index=True)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    progress: int = Field(default=0)  # 0-100

    outputs_json: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    """Node output data used for resume.

    When workflow resumes after pause, completed node outputs are read here,
    so downstream nodes can access upstream node results.

    Example:
    {
        "project_id": 123,
        "card_id": 456,
        "result": {...}
    }
    """

    error_message: Optional[str] = None

    checkpoint_json: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    """Checkpoint data: lightweight metadata.

    Structure:
    {
        "percent": 50.0,                    # Progress percent
        "message": "processed 30/60",       # Progress message
        "data": {                           # Optional node custom data
            "processed_count": 30,          # Lightweight counter
            "last_item_id": "item_30",      # Lightweight identifier
            "current_batch": 3              # Lightweight batch number
        },
        "timestamp": "2026-02-04T10:30:00"  # Saved time
    }

    Note:
    - data stores position info only, not business data
    - Size limit: < 10KB
    - Used for resume; nodes access it through context.checkpoint
    """

    created_at: datetime = Field(default_factory=datetime.now, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.now, nullable=False)

class KGRelation(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("project_id", "source", "target", "kind_en", name="uq_kg_relation_key"),
        sa.Index("ix_kg_relation_project_source", "project_id", "source"),
        sa.Index("ix_kg_relation_project_target", "project_id", "target"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(index=True)
    source: str = Field(index=True)
    target: str = Field(index=True)
    kind_en: str = Field(index=True)
    kind_cn: str = Field(default="Khac")
    fact: Optional[str] = None
    a_to_b_addressing: Optional[str] = None
    b_to_a_addressing: Optional[str] = None
    recent_dialogues: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    recent_event_summaries: List[dict] = Field(default_factory=list, sa_column=Column(JSON))
    stance: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.now, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.now, nullable=False)
