import clsx from "clsx";

import { ColorScheme } from "../hooks/useColorScheme";
import { useMedications } from "../hooks/useMedications";
import { ChatKitPanel } from "./ChatKitPanel";
import { MedicationCard } from "./MedicationCard";
import { ThemeToggle } from "./ThemeToggle";

export default function Home({
  scheme,
  handleThemeChange,
}: {
  scheme: ColorScheme;
  handleThemeChange: (scheme: ColorScheme) => void;
}) {
  const { medications, refresh, performAction } = useMedications();

  const containerClass = clsx(
    "min-h-screen bg-gradient-to-br transition-colors duration-300",
    scheme === "dark"
      ? "from-slate-900 via-slate-950 to-slate-850 text-slate-100"
      : "from-slate-100 via-white to-slate-200 text-slate-900"
  );

  return (
    <div className={containerClass}>
      <div className="mx-auto flex min-h-screen w-full max-w-6xl flex-col-reverse gap-10 px-6 pt-4 pb-10 md:py-10 lg:flex-row">
        <div className="relative w-full md:w-[45%] flex h-[90vh] items-stretch overflow-hidden rounded-3xl bg-white/80 shadow-[0_45px_90px_-45px_rgba(15,23,42,0.6)] ring-1 ring-slate-200/60 backdrop-blur md:h-[90vh] dark:bg-slate-900/70 dark:shadow-[0_45px_90px_-45px_rgba(15,23,42,0.85)] dark:ring-slate-800/60">
          <ChatKitPanel
            theme={scheme}
            onWidgetAction={performAction}
            onResponseEnd={refresh}
            onThemeRequest={handleThemeChange}
          />
        </div>
        <section className="flex-1 space-y-8 py-8">
          <header className="space-y-6">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div className="space-y-3">
                <h1 className="text-3xl font-semibold sm:text-4xl">
                  Health Coach
                </h1>
                <p className="max-w-xl text-sm text-slate-600 dark:text-slate-300">
                  Your comprehensive AI health coach providing personalized guidance on 
                  nutrition, exercise, medication management, sleep optimization, stress 
                  management, and overall wellness. Get expert health advice tailored to 
                  your unique needs and goals.
                </p>
              </div>
              <ThemeToggle value={scheme} onChange={handleThemeChange} />
            </div>
          </header>

          <div>
            <h2 className="text-lg font-semibold text-slate-700 dark:text-slate-200">
              Your Medication Cabinet
            </h2>
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
              Your medications appear here after you mention them in the conversation.
            </p>
            <div className="mt-6">
              <div className="rounded-3xl border border-slate-200/60 bg-white/70 shadow-[0_35px_90px_-55px_rgba(15,23,42,0.45)] ring-1 ring-slate-200/50 backdrop-blur-sm dark:border-slate-800/70 dark:bg-slate-900/50 dark:shadow-[0_45px_95px_-60px_rgba(15,23,42,0.85)] dark:ring-slate-900/60">
                <div className="max-h-[50vh] overflow-y-auto p-6 sm:max-h-[40vh]">
                  {medications.length === 0 ? (
                    <div className="flex flex-col items-start justify-center gap-3 text-slate-600 dark:text-slate-300">
                      <span className="text-base font-medium text-slate-700 dark:text-slate-200">
                        No medications recorded yet.
                      </span>
                      <span className="text-sm text-slate-500 dark:text-slate-400">
                        Start a conversation in the chat to record your first medication.
                      </span>
                    </div>
                  ) : (
                    <ul className="list-none space-y-3">
                      {medications.map((medication) => (
                        <MedicationCard key={medication.name} medication={medication} />
                      ))}
                    </ul>
                  )}
                </div>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
