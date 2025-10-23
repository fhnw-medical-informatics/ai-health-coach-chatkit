"""Multi-agent setup for health coaching with specialized agents."""

from __future__ import annotations

import logging
from typing import Any

from agents import Agent, RunContextWrapper, function_tool, handoff
from chatkit.agents import AgentContext

from .constants import MODEL
from .medications import Medication, medication_store


@function_tool(description_override="List all medications in the patient's medicine cabinet. Use this to see what medications the patient currently has.")
async def list_medications(
    ctx: RunContextWrapper[AgentContext],
) -> dict[str, Any]:
    """List all medications in the medicine cabinet."""
    try:
        medications = await medication_store.list_all()
        return {
            "medications": [medication.as_dict() for medication in medications],
            "count": len(medications)
        }
    except Exception as e:
        logging.exception("Failed to list medications")
        return {"error": "Failed to retrieve medications"}


@function_tool(description_override="Add a new medication to the patient's medicine cabinet. Use this when the patient mentions taking, buying, or using a new medication.")
async def add_medication(
    ctx: RunContextWrapper[AgentContext],
    medication_name: str,
) -> dict[str, Any]:
    """Add a medication to the medicine cabinet."""
    try:
        medication = await medication_store.create(name=medication_name)
        return {
            "medication_name": medication.name,
            "status": "added",
            "created_at": medication.created_at.isoformat()
        }
    except Exception as e:
        logging.exception("Failed to add medication")
        return {"error": "Failed to add medication"}


@function_tool(description_override="Get information about a specific medication in the patient's medicine cabinet.")
async def get_medication(
    ctx: RunContextWrapper[AgentContext],
    medication_name: str,
) -> dict[str, Any]:
    """Get information about a specific medication."""
    try:
        medication = await medication_store.get(medication_name)
        if medication:
            return {
                "found": True,
                "medication": medication.as_dict()
            }
        else:
            return {
                "found": False,
                "message": f"Medication '{medication_name}' not found in medicine cabinet"
            }
    except Exception as e:
        logging.exception("Failed to get medication")
        return {"error": "Failed to retrieve medication"}


@function_tool(description_override="Remove a medication from the patient's medicine cabinet. Use this when the patient stops taking a medication.")
async def remove_medication(
    ctx: RunContextWrapper[AgentContext],
    medication_name: str,
) -> dict[str, Any]:
    """Remove a medication from the medicine cabinet."""
    try:
        deleted = await medication_store.delete(medication_name)
        if deleted:
            return {
                "medication_name": medication_name,
                "status": "removed"
            }
        else:
            return {
                "medication_name": medication_name,
                "status": "not_found",
                "message": f"Medication '{medication_name}' was not found in the medicine cabinet"
            }
    except Exception as e:
        logging.exception("Failed to remove medication")
        return {"error": "Failed to remove medication"}


def create_supervisor_agent(pharmacist: Agent[AgentContext], psychologist: Agent[AgentContext]) -> Agent[AgentContext]:
    return Agent(
        name="Supervisor",
        model=MODEL,
        instructions=(
            "You are a supervisor tasked with routing health-related user queries to the appropriate specialist. Never answer questions yourself, only focus on triage."
        ),
        handoffs=[
            handoff(pharmacist, tool_name_override="to_pharmacist", tool_description_override="Handoff to pharmacist for medication questions"),
            handoff(psychologist, tool_name_override="to_psychologist", tool_description_override="Handoff to psychologist for emotional support"),
        ],
    )


def create_pharmacist_agent() -> Agent[AgentContext]:
    return Agent(
        name="Pharmacist",
        model=MODEL,
        instructions=(
            "You are a pharmacist who manages a medicine cabinet (use your tools to inspect and manage the contents of the medicine cabinet).\n"
            "If users report symptoms or conditions which are treatable with current medications in the medicine cabinet, suggest the appropriate medication and dosage."
            "Be very careful with giving advice and suggest consulting with a healthcare provider for serious medical concerns."
        ),
        tools=[list_medications, add_medication, get_medication, remove_medication],
    )


def create_psychologist_agent() -> Agent[AgentContext]:
    """Create the psychologist agent specialized in mental health support."""
    return Agent(
        name="Psychologist",
        model=MODEL,
        instructions=(
            "You are a psychologist who specializes in supporting patients with mental health struggles. "
            "Please be empathetic and supportive.\n\n"
            "You specialize in:\n"
            "- Stress management and coping strategies\n"
            "- Anxiety and depression support\n"
            "- Sleep hygiene and mental wellness\n"
            "- Emotional regulation techniques\n"
            "- Mindfulness and relaxation methods\n"
            "- Building healthy mental habits\n"
            "- Crisis intervention and support\n\n"
            "Always maintain a supportive, non-judgmental tone. For serious mental health crises, "
            "encourage immediate professional help and provide crisis resources."
        ),
        tools=[],  # No specific tools for psychologist
    )


def create_agents() -> tuple[Agent[AgentContext], Agent[AgentContext], Agent[AgentContext]]:
    """Create all three agents with proper dependencies."""
    pharmacist = create_pharmacist_agent()
    psychologist = create_psychologist_agent()
    supervisor = create_supervisor_agent(pharmacist, psychologist)
    
    return pharmacist, psychologist, supervisor
