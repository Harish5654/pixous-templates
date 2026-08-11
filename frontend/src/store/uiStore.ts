import { create } from 'zustand';

interface UIState {
  sidebarOpen: boolean;
  toggleSidebar: () => void;
}

// Collapse the sidebar by default on narrow screens so the app stays usable on
// tablets/phones; the user can still toggle it open.
const isNarrow = () => (typeof window === 'undefined' ? false : window.innerWidth < 900);

export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: !isNarrow(),
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
}));
