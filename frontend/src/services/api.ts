import axios from 'axios';
import { 
  RecoveryAnalysisRequest, 
  FinalRecoveryPlan, 
  CustomerListItem, 
  CustomerDetailResponse, 
  RecoveryCaseItem, 
  RecoveryCaseDetailResponse, 
  DashboardMetrics 
} from '../types';

const api = axios.create({
  baseURL: 'http://localhost:8000',
});

export const analyzeCustomer = async (data: RecoveryAnalysisRequest): Promise<FinalRecoveryPlan> => {
  const response = await api.post<FinalRecoveryPlan>('/recovery/analyze', data);
  return response.data;
};

export const getCustomers = async (search?: string): Promise<CustomerListItem[]> => {
  const response = await api.get<CustomerListItem[]>('/customers', { params: { search } });
  return response.data;
};

export const getCustomer = async (id: number): Promise<CustomerDetailResponse> => {
  const response = await api.get<CustomerDetailResponse>(`/customers/${id}`);
  return response.data;
};

export const getRecoveryCases = async (params?: any): Promise<RecoveryCaseItem[]> => {
  const response = await api.get<RecoveryCaseItem[]>('/recovery/cases', { params });
  return response.data;
};

export const completeRecoveryCase = async (id: number): Promise<any> => {
  const response = await api.put(`/recovery/cases/${id}/complete`);
  return response.data;
};

export const getRecoveryCase = async (id: number): Promise<RecoveryCaseDetailResponse> => {
  const response = await api.get<RecoveryCaseDetailResponse>(`/recovery/cases/${id}`);
  return response.data;
};

export const getDashboardMetrics = async (): Promise<DashboardMetrics> => {
  const response = await api.get<DashboardMetrics>('/dashboard/metrics');
  return response.data;
};

export const getAnalyticsMetrics = async (): Promise<any> => {
  const response = await api.get<any>('/analytics/metrics');
  return response.data;
};
