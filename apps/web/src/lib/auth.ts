// SPDX-License-Identifier: AGPL-3.0-or-later
import { create } from "zustand";
import { persist } from "zustand/middleware";

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  setTokens: (access: string, refresh: string) => void;
  clearTokens: () => void;
  getAccessToken: () => string | null;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      accessToken: null,
      refreshToken: null,
      setTokens: (access, refresh) => set({ accessToken: access, refreshToken: refresh }),
      clearTokens: () => set({ accessToken: null, refreshToken: null }),
      getAccessToken: () => get().accessToken,
    }),
    { name: "openidp-auth" }
  )
);

export function getStoredAccessToken(): string | null {
  return useAuthStore.getState().accessToken;
}
