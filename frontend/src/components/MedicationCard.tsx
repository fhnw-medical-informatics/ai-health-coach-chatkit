import { Pill } from "lucide-react";

import type { MedicationRecord } from "../lib/medications";

export function MedicationCard({ medication }: { medication: MedicationRecord }) {
  return (
    <li className="group flex items-start gap-3 text-sm font-medium text-slate-600 dark:text-slate-300">
      <Pill className="h-5 w-5 text-blue-600 dark:text-blue-400 mt-0.5" />
      <div className="flex-1">
        <div className="font-semibold text-slate-800 dark:text-slate-200">
          {medication.name}
        </div>
      </div>
    </li>
  );
}
