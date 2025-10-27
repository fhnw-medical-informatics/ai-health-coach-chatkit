"""Pharmacist agent for medication management and advice."""

from __future__ import annotations

import logging
from typing import Any

from agents import Agent, RunContextWrapper, function_tool
from chatkit.agents import AgentContext

from .model import MODEL
from .medications import medication_store

PHARMACIST_INSTRUCTIONS = """You are a pharmacist who manages a medicine cabinet (use your tools to inspect and manage the contents of the medicine cabinet).
If users report symptoms or conditions which are treatable with current medications in the medicine cabinet, suggest the appropriate medication and dosage.
Be very careful with giving advice and suggest consulting with a healthcare provider for serious medical concerns."""


@function_tool(description_override="List all medications in the patient's medicine cabinet. Use this to see what medications the patient currently has.")
async def list_medications(
    _ctx: RunContextWrapper[AgentContext],
) -> dict[str, Any]:
    """List all medications in the medicine cabinet."""
    try:
        medications = await medication_store.list_all()
        return {
            "medications": [medication.as_dict() for medication in medications],
            "count": len(medications)
        }
    except Exception:
        logging.exception("Failed to list medications")
        return {"error": "Failed to retrieve medications"}


@function_tool(description_override="Add a new medication to the patient's medicine cabinet. Use this when the patient mentions taking, buying, or using a new medication.")
async def add_medication(
    _ctx: RunContextWrapper[AgentContext],
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
    except Exception:
        logging.exception("Failed to add medication")
        return {"error": "Failed to add medication"}


@function_tool(description_override="Get information about a specific medication in the patient's medicine cabinet.")
async def get_medication(
    _ctx: RunContextWrapper[AgentContext],
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
    except Exception:
        logging.exception("Failed to get medication")
        return {"error": "Failed to retrieve medication"}


@function_tool(description_override="Remove a medication from the patient's medicine cabinet. Use this when the patient stops taking a medication.")
async def remove_medication(
    _ctx: RunContextWrapper[AgentContext],
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
    except Exception:
        logging.exception("Failed to remove medication")
        return {"error": "Failed to remove medication"}


def create_pharmacist_agent() -> Agent[AgentContext]:
    """Create the pharmacist agent specialized in medication management."""
    return Agent(
        name="Pharmacist",
        model=MODEL,
        instructions=PHARMACIST_INSTRUCTIONS,
        tools=[list_medications, add_medication, get_medication, remove_medication],
    )
