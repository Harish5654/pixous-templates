import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from './apiClient';
import type { Template, Variable } from '../types/template';
import type { User } from '../types/user';
import type { MasterData, MasterDataLists } from '../types/masterData';

type TemplateInput = Omit<Template, 'id' | 'created_by' | 'updated_by' | 'version'>;

export const useTemplates = () => {
  return useQuery({
    queryKey: ['templates'],
    queryFn: async () => {
      const { data } = await apiClient.get<Template[]>('/templates');
      return data;
    },
  });
};

export const useTemplate = (id: string) => {
  return useQuery({
    queryKey: ['template', id],
    queryFn: async () => {
      const { data } = await apiClient.get<Template>(`/templates/${id}`);
      return data;
    },
    enabled: !!id,
  });
};

export const useVariables = () => {
  return useQuery({
    queryKey: ['variables'],
    queryFn: async () => {
      const { data } = await apiClient.get<Variable[]>('/variables');
      return data;
    },
  });
};

export const useCategories = () => {
  return useQuery({
    queryKey: ['categories'],
    queryFn: async () => {
      const { data } = await apiClient.get<string[]>('/categories');
      return data;
    },
  });
};

export const useAIAction = () => {
  return useMutation({
    mutationFn: async ({ action, content, targetLanguage }: { action: string; content: string; targetLanguage?: string }) => {
      const { data } = await apiClient.post<{ result: string }>('/ai/action', { action, content, targetLanguage });
      return data.result;
    },
  });
};

export const useLogin = () => {
  return useMutation({
    mutationFn: async ({ email, password }: { email: string; password: string }) => {
      const { data } = await apiClient.post<{ access_token: string; token_type: string; user: User }>('/auth/login', { email, password });
      return data;
    },
  });
};

export const useCreateTemplate = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: TemplateInput) => {
      const { data } = await apiClient.post<Template>('/templates', payload);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] });
    },
  });
};

export const useUpdateTemplate = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, payload }: { id: string; payload: TemplateInput }) => {
      const { data } = await apiClient.put<Template>(`/templates/${id}`, payload);
      return data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['templates'] });
      queryClient.invalidateQueries({ queryKey: ['template', data.id] });
    },
  });
};

export const useDeleteTemplate = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await apiClient.delete(`/templates/${id}`);
      return id;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] });
    },
  });
};

export const useMasterData = () => {
  return useQuery({
    queryKey: ['master-data'],
    queryFn: async () => {
      const { data } = await apiClient.get<MasterData>('/master-data');
      return data;
    },
  });
};

export const useUpdateMasterData = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (lists: MasterDataLists) => {
      const { data } = await apiClient.put<MasterData>('/master-data', { lists });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['master-data'] });
      queryClient.invalidateQueries({ queryKey: ['categories'] });
    },
  });
};
