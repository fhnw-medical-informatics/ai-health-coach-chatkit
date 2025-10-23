import { useCallback, useEffect, useState } from "react";

import { MEDICATIONS_API_URL } from "../lib/config";
import type { MedicationRecord } from "../lib/medications";

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

  const refreshMedications = useCallback(() => {
    fetchMedications();
  }, [fetchMedications]);

  const clearAllMedications = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(MEDICATIONS_API_URL, {
        method: 'DELETE',
      });
      if (!response.ok) {
        throw new Error(`Failed to clear medications: ${response.statusText}`);
      }
      // Clear local state immediately
      setMedications([]);
    } catch (err) {
      console.error("Failed to clear medications:", err);
      setError(err instanceof Error ? err.message : "Failed to clear medications");
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch medications on mount
  useEffect(() => {
    fetchMedications();
  }, [fetchMedications]);

  return { medications, loading, error, refreshMedications, clearAllMedications };
}
