import { ChatKit, useChatKit } from "@openai/chatkit-react";
import type { ColorScheme } from "../hooks/useColorScheme";
import {
  CHATKIT_API_DOMAIN_KEY,
  CHATKIT_API_URL,
  GREETING,
  PLACEHOLDER_INPUT,
  STARTER_PROMPTS,
} from "../lib/config";

type ChatKitPanelProps = {
  theme: ColorScheme;
  onResponseEnd: () => void;
  onThemeRequest: (scheme: ColorScheme) => void;
};

export function ChatKitPanel({
  theme,
  onResponseEnd,
  onThemeRequest,
}: ChatKitPanelProps) {

  const chatkit = useChatKit({
    api: { url: CHATKIT_API_URL, domainKey: CHATKIT_API_DOMAIN_KEY },
    theme: {
      colorScheme: theme,
      color: {
        grayscale: {
          hue: 220,
          tint: 6,
          shade: theme === "dark" ? -1 : -4,
        },
        accent: {
          primary: theme === "dark" ? "#f1f5f9" : "#0f172a",
          level: 1,
        },
      },
      radius: "round",
    },
    startScreen: {
      greeting: GREETING,
      prompts: STARTER_PROMPTS,
    },
    composer: {
      placeholder: PLACEHOLDER_INPUT,
    },
    threadItemActions: {
      feedback: false,
    },
    onClientTool: async (invocation) => {
      if (invocation.name !== "switch_theme") {
        return { success: false };
      }
      const requested = invocation.params.theme;
      if (requested !== "light" && requested !== "dark") {
        return { success: false };
      }
      onThemeRequest(requested);
      return { success: true };
    },
    onResponseEnd: () => {
      onResponseEnd();
    },
    onThreadChange: () => {
      // Thread changed - any necessary cleanup can be added here
    },
    onError: ({ error }) => {
      // ChatKit handles displaying the error to the user
      console.error("ChatKit error", error);
    },
  });

  return (
    <div className="relative h-full w-full overflow-hidden border border-slate-200/60 bg-white shadow-card dark:border-slate-800/70 dark:bg-slate-900">
      <ChatKit control={chatkit.control} className="block h-full w-full" />
    </div>
  );
}
