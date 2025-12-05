import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import api from '../services/api';

type WidgetItem = { id: string };

type DashboardState = {
  selectedPracticeIds: string[];
  layout: WidgetItem[];
  widgets: Record<string, any>;
  loading: boolean;
  error: string | null;
  setSelectedPracticeIds: (ids: string[]) => void;
  loadLayout: (practiceId: string) => Promise<void>;
  saveLayout: (practiceId: string, layout: WidgetItem[], widgets: Record<string, any>) => Promise<void>;
};

export const useDashboardStore = create<DashboardState>()(
  persist(
    (set) => ({
      selectedPracticeIds: [],
      layout: [],
      widgets: {},
      loading: false,
      error: null,

      setSelectedPracticeIds: (ids) => set({ selectedPracticeIds: ids }),

      loadLayout: async (practiceId: string) => {
        set({ loading: true, error: null });
        try {
          const res = await api.get('/dashboard/layout', { params: { practiceId } });
          set({ layout: res.data.layout || [], widgets: res.data.widgets || {}, loading: false });
        } catch (e: any) {
          set({ loading: false, error: e?.message || 'Failed to load layout' });
        }
      },

      saveLayout: async (practiceId: string, layout: WidgetItem[], widgets: Record<string, any>) => {
        set({ loading: true, error: null });
        try {
          await api.post('/dashboard/layout', { practiceId, layout, widgets });
          set({ layout, widgets, loading: false });
        } catch (e: any) {
          set({ loading: false, error: e?.message || 'Failed to save layout' });
        }
      },
    }),
    {
      name: 'dental-erp-dashboard',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({ selectedPracticeIds: state.selectedPracticeIds, layout: state.layout, widgets: state.widgets }),
    }
  )
);

export default useDashboardStore;
