import { useCallback, useEffect, useState } from "react";

import { MEDICATIONS_API_URL } from "../lib/config";
import type { MedicationRecord } from "../lib/medications";

export type MedicationAction = {
  type: "save" | "delete";
  medicationName: string;
};

export function useMedications() {
  const [medications, setMedications] = useState<MedicationRecord[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchMedications = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(MEDICATIONS_API_URL);
      if (!response.ok) {
        throw new Error(`Failed to fetch medications: ${response.statusText}`);
      }
      const data = await response.json();
      setMedications(data.medications || []);
    } catch (err) {
      console.error("Failed to fetch medications:", err);
      setError(err instanceof Error ? err.message : "Failed to fetch medications");
    } finally {
      setLoading(false);
    }
  }, []);

  const performAction = useCallback(async (action: MedicationAction) => {
    if (action.type === "save") {
      const name = action.medicationName.trim();
      if (!name) {
        return;
      }
      
      // Add to local state immediately for UI responsiveness
      setMedications((current) => {
        if (current.some((medication) => medication.name === name)) {
          return current;
        }
        const saved: MedicationRecord = {
          name,
          createdAt: new Date().toISOString(),
        };
        return [...current, saved];
      });
    } else if (action.type === "delete") {
      setMedications((current) => current.filter((medication) => medication.name !== action.medicationName));
    }
  }, []);

  const refresh = useCallback(() => {
    fetchMedications();
  }, [fetchMedications]);

  // Fetch medications on mount
  useEffect(() => {
    fetchMedications();
  }, [fetchMedications]);

  return { medications, loading, error, refresh, performAction };
}
