import { useCallback, useEffect, useState } from "react";

import { FACTS_API_URL } from "../lib/config";
import type { FactRecord } from "../lib/facts";

export type FactAction = {
  type: "save" | "discard";
  factId: string;
  factText?: string;
};

export function useFacts() {
  const [facts, setFacts] = useState<FactRecord[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchFacts = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(FACTS_API_URL);
      if (!response.ok) {
        throw new Error(`Failed to fetch facts: ${response.statusText}`);
      }
      const data = await response.json();
      setFacts(data.facts || []);
    } catch (err) {
      console.error("Failed to fetch facts:", err);
      setError(err instanceof Error ? err.message : "Failed to fetch facts");
    } finally {
      setLoading(false);
    }
  }, []);

  const performAction = useCallback(async (action: FactAction) => {
    if (action.type === "save") {
      const text = (action.factText ?? "").trim();
      if (!text) {
        return;
      }
      
      // Add to local state immediately for UI responsiveness
      setFacts((current) => {
        if (current.some((fact) => fact.id === action.factId)) {
          return current;
        }
        const saved: FactRecord = {
          id: action.factId,
          text,
          status: "saved",
          createdAt: new Date().toISOString(),
        };
        return [...current, saved];
      });
    } else if (action.type === "discard") {
      setFacts((current) => current.filter((fact) => fact.id !== action.factId));
    }
  }, []);

  const refresh = useCallback(() => {
    fetchFacts();
  }, [fetchFacts]);

  // Fetch facts on mount
  useEffect(() => {
    fetchFacts();
  }, [fetchFacts]);

  return { facts, loading, error, refresh, performAction };
}
