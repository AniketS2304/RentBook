import { ApiClient, apiClient as defaultClient } from './client';
import type {
  DashboardSummaryResponse,
  LoginRequest,
  LoginResponse,
  MonthlyReportResponse,
  PaymentCreate,
  PaymentCreateResponse,
  PaymentDetail,
  PaymentUpdate,
  PaymentVoidRequest,
  PaymentVoidResponse,
  PropertyArchiveResponse,
  PropertyCreate,
  PropertyDetail,
  PropertyListResponse,
  PropertyUpdate,
  RefreshRequest,
  RefreshResponse,
  RegisterRequest,
  RegisterResponse,
  ReminderCreateRequest,
  ReminderCreateResponse,
  ReminderListItem,
  RentListResponse,
  RentRecordDetail,
  RentRecordUpdate,
  RentRecordVoidRequest,
  RentRecordVoidResponse,
  TenantCreate,
  TenantDeactivateRequest,
  TenantDeactivateResponse,
  TenantDetail,
  TenantListResponse,
  TenantReminderCreateRequest,
  TenantUpdate,
  UnitArchiveResponse,
  UnitCreate,
  UnitOut,
  UnitUpdate,
} from '../types/api';

export function createApiServices(client: ApiClient = defaultClient) {
  return {
    auth: {
      register: (data: RegisterRequest) =>
        client.post<RegisterResponse>('/auth/register', data, { skipAuth: true }),
      login: (data: LoginRequest) =>
        client.post<LoginResponse>('/auth/login', data, { skipAuth: true }),
      refresh: (data: RefreshRequest) =>
        client.post<RefreshResponse>('/auth/refresh', data, { skipAuth: true }),
    },

    properties: {
      list: (params?: { include_archived?: boolean; page?: number; per_page?: number }) =>
        client.get<PropertyListResponse>('/properties', params),
      get: (id: string) =>
        client.get<PropertyDetail>(`/properties/${id}`),
      create: (data: PropertyCreate) =>
        client.post<PropertyDetail>('/properties', data),
      update: (id: string, data: PropertyUpdate) =>
        client.patch<PropertyDetail>(`/properties/${id}`, data),
      archive: (id: string) =>
        client.delete<PropertyArchiveResponse>(`/properties/${id}`),
    },

    units: {
      list: (propertyId: string, params?: { include_archived?: boolean }) =>
        client.get<UnitOut[]>(`/properties/${propertyId}/units`, params),
      create: (propertyId: string, data: UnitCreate) =>
        client.post<UnitOut>(`/properties/${propertyId}/units`, data),
      get: (id: string) =>
        client.get<UnitOut>(`/units/${id}`),
      update: (id: string, data: UnitUpdate) =>
        client.patch<UnitOut>(`/units/${id}`, data),
      archive: (id: string) =>
        client.delete<UnitArchiveResponse>(`/units/${id}`),
    },

    tenants: {
      list: (params?: { status?: string; property_id?: string; page?: number; per_page?: number }) =>
        client.get<TenantListResponse>('/tenants', params),
      get: (id: string) =>
        client.get<TenantDetail>(`/tenants/${id}`),
      create: (data: TenantCreate) =>
        client.post<TenantDetail>('/tenants', data),
      update: (id: string, data: TenantUpdate) =>
        client.patch<TenantDetail>(`/tenants/${id}`, data),
      deactivate: (id: string, data?: TenantDeactivateRequest) =>
        client.post<TenantDeactivateResponse>(`/tenants/${id}/deactivate`, data || {}),
    },

    rent: {
      list: (params: { month: number; year: number; property_id?: string }) =>
        client.get<RentListResponse>('/rent', params),
      get: (id: string) =>
        client.get<RentRecordDetail>(`/rent/${id}`),
      update: (id: string, data: RentRecordUpdate) =>
        client.put<RentRecordDetail>(`/rent/${id}`, data),
      voidRecord: (id: string, data?: RentRecordVoidRequest) =>
        client.post<RentRecordVoidResponse>(`/rent/${id}/void`, data || {}),
    },

    payments: {
      create: (rentRecordId: string, data: PaymentCreate) =>
        client.post<PaymentCreateResponse>(`/rent/${rentRecordId}/payments`, data),
      get: (id: string) =>
        client.get<PaymentDetail>(`/payments/${id}`),
      update: (id: string, data: PaymentUpdate) =>
        client.put<PaymentDetail>(`/payments/${id}`, data),
      voidPayment: (id: string, data?: PaymentVoidRequest) =>
        client.post<PaymentVoidResponse>(`/payments/${id}/void`, data || {}),
    },

    dashboard: {
      getSummary: (params?: { month?: number; year?: number; property_id?: string }) =>
        client.get<DashboardSummaryResponse>('/dashboard/summary', params),
    },

    reports: {
      getMonthly: (params: { month: number; year: number; property_id?: string }) =>
        client.get<MonthlyReportResponse>('/reports/monthly', params),
    },

    reminders: {
      sendRentReminder: (rentRecordId: string, data?: ReminderCreateRequest) =>
        client.post<ReminderCreateResponse>(`/rent/${rentRecordId}/reminder`, data || {}),
      sendTenantReminder: (tenantId: string, data: TenantReminderCreateRequest) =>
        client.post<ReminderCreateResponse>(`/tenants/${tenantId}/reminders`, data),
      listForTenant: (tenantId: string) =>
        client.get<ReminderListItem[]>(`/tenants/${tenantId}/reminders`),
    },
  };
}

export const api = createApiServices(defaultClient);
