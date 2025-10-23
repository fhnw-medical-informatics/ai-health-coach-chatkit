"""Simple in-memory store for user medications."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List


def normalize_medication_name(name: str) -> str:
    """Normalize medication name: trim whitespace only."""
    return name.strip()


@dataclass(slots=True)
class Medication:
    """Represents a single medication."""

    name: str
    created_at: datetime = field(default_factory=datetime.utcnow)

    def as_dict(self) -> dict[str, str]:
        """Serialize the medication for JSON responses."""
        return {
            "name": self.name,
            "createdAt": self.created_at.isoformat(),
        }


class MedicationStore:
    """Thread-safe helper that stores medications in memory using names as keys."""

    def __init__(self) -> None:
        self._medications: Dict[str, Medication] = {}
        self._lock = asyncio.Lock()

    async def create(self, *, name: str) -> Medication:
        """Create or return existing medication with normalized name."""
        async with self._lock:
            # Normalize the medication name
            normalized_name = normalize_medication_name(name)
            
            # Check if medication already exists
            if normalized_name in self._medications:
                return self._medications[normalized_name]
            
            # Create new medication
            medication = Medication(name=normalized_name)
            self._medications[normalized_name] = medication
            return medication

    async def list_all(self) -> List[Medication]:
        """Return all medications sorted by name."""
        async with self._lock:
            return sorted(self._medications.values(), key=lambda m: m.name)

    async def get(self, name: str) -> Medication | None:
        """Get medication by normalized name."""
        async with self._lock:
            normalized_name = normalize_medication_name(name)
            return self._medications.get(normalized_name)

    async def delete(self, name: str) -> bool:
        """Delete medication by name. Returns True if deleted, False if not found."""
        async with self._lock:
            normalized_name = normalize_medication_name(name)
            if normalized_name in self._medications:
                del self._medications[normalized_name]
                return True
            return False

    async def clear_all(self) -> int:
        """Clear all medications. Returns the number of medications that were deleted."""
        async with self._lock:
            count = len(self._medications)
            self._medications.clear()
            return count


medication_store = MedicationStore()
"""Global instance used by the API and the ChatKit workflow."""