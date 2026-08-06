import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AcknowledgementsState {
  acknowledgedIds: string[];
  toggleAcknowledge: (id: string) => void;
  isAcknowledged: (id: string) => boolean;
}

export const useAcknowledgementsStore = create<AcknowledgementsState>()(
  persist(
    (set, get) => ({
      acknowledgedIds: [],
      toggleAcknowledge: (id) => set((state) => ({
        acknowledgedIds: state.acknowledgedIds.includes(id)
          ? state.acknowledgedIds.filter((a) => a !== id)
          : [...state.acknowledgedIds, id]
      })),
      isAcknowledged: (id) => get().acknowledgedIds.includes(id),
    }),
    { name: 'notice-acknowledgements' }
  )
);
