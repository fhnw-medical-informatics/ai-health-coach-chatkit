export const CHATKIT_API_URL =
  import.meta.env.VITE_CHATKIT_API_URL ?? "/chatkit";

/**
 * ChatKit still expects a domain key at runtime. Use any placeholder locally,
 * but register your production domain at
 * https://platform.openai.com/settings/organization/security/domain-allowlist
 * and deploy the real key.
 */
export const CHATKIT_API_DOMAIN_KEY =
  import.meta.env.VITE_CHATKIT_API_DOMAIN_KEY ?? "domain_pk_localhost_dev";

export const MEDICATIONS_API_URL = import.meta.env.VITE_MEDICATIONS_API_URL ?? "/medications";

export const THEME_STORAGE_KEY = "chatkit-boilerplate-theme";

export const GREETING = "Welcome to your Health Coach";

export const STARTER_PROMPTS = [
  {
    label: "What can you do?",
    prompt: "What can you do?",
    icon: "circle-question",
  },
  {
    label: "I bought Ibuprofen",
    prompt: "I bought Ibuprofen",
    icon: "lab",
  },
  {
    label: "I am feeling a bit low on energy",
    prompt: "I am feeling a bit low on energy",
    icon: "lightbulb",
  },
  {
    label: "Change the theme to dark mode",
    prompt: "Change the theme to dark mode",
    icon: "sparkle",
  },
];

export const PLACEHOLDER_INPUT = "Tell me about your health concerns";
