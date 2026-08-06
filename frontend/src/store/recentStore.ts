import { create } from 'zustand';
import { persist } from 'zustand/middleware';

const MAX_RECENT = 8;

interface RecentState {
  recentIds: string[];
  addRecent: (id: string) => void;
}

export const useRecentStore = create<RecentState>()(
  persist(
    (set) => ({
      recentIds: [],
      addRecent: (id) => set((state) => ({
        recentIds: [id, ...state.recentIds.filter((r) => r !== id)].slice(0, MAX_RECENT)
      })),
    }),
    { name: 'template-recent' }
  )
);
