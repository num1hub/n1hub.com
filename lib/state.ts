"use client";

import { create } from "zustand";

type ScopeType = "my" | "public" | "inbox" | "tags";

interface RagScopeState {
  scopeType: ScopeType;
  scope: string[]; // Tags when scopeType is "tags", otherwise empty
  setScopeType: (type: ScopeType) => void;
  toggleTag: (tag: string) => void;
  setScope: (tags: string[]) => void;
  getScopeForAPI: () => string[]; // Returns formatted scope for API
}

export const useRagScope = create<RagScopeState>((set, get) => ({
  scopeType: "my", // Default: My Capsules (Section 10)
  scope: [],
  setScopeType: (type) => {
    set({ scopeType: type, scope: type === "tags" ? get().scope : [] });
  },
  toggleTag: (tag) => {
    if (get().scopeType !== "tags") {
      // Switch to tags mode when toggling tags
      set({ scopeType: "tags", scope: [tag] });
      return;
    }
    const current = get().scope;
    if (current.includes(tag)) {
      set({ scope: current.filter((t) => t !== tag) });
    } else {
      set({ scope: [...current, tag] });
    }
  },
  setScope: (tags) => set({ scope: tags }),
  getScopeForAPI: () => {
    const state = get();
    if (state.scopeType === "tags") {
      return state.scope;
    }
    return [state.scopeType]; // ["my"], ["public"], or ["inbox"]
  },
}));
