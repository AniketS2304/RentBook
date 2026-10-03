/**
 * API Type Definitions for RentBook Mobile
 * Strictly matching backend FastAPI schemas and docs/architecture/API.md
 * 
 * Rules:
 * - Money is always integer paise (number).
 * - Dates are ISO strings: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ.
 * - UUIDs are strings.
 * - Enums match backend definitions exactly.
 */

// ==========================================
// Common & Error Schemas
// ==========================================

export interface FieldError {
  field?: string;
  message: string;
}

export interface ApiErrorResponse {
  detail: string;
  code?: string;
  errors?: FieldError[];
}

export interface HealthResponse {
  status: string;
  version: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
}

// ==========================================
// Auth & Owner
// ==========================================

export interface OwnerBrief {
  id: string;
  email: string;
  full_name: string;
}

export interface OwnerOut {
  id: string;
  email: string;
  full_name: string;
  phone?: string | null;
  created_at: string;
  updated_at: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name: string;
  phone?: string | null;
}

export interface RegisterResponse {
  id: string;
  email: string;
  full_name: string;
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: OwnerBrief;
}

export interface RefreshRequest {
  refresh_token: string;
}

export interface RefreshResponse {
  access_token: string;
  refresh_token?: string | null;
  token_type: string;
}

// ==========================================
// Property
// ==========================================

export interface PropertyCreate {
  name: string;
  address?: string | null;
  notes?: string | null;
}

export interface PropertyUpdate {
  name?: string | null;
  address?: string | null;
  notes?: string | null;
}

export interface PropertyListItem {
  id: string;
  name: string;
  address?: string | null;
  notes?: string | null;
  unit_count: number;
  occupied_count: number;
  vacant_count: number;
  archived_at?: string | null;
  created_at: string;
}

export interface PropertyListResponse {
  items: PropertyListItem[];
  total: number;
  page: number;
  per_page: number;
}

export interface PropertyDetail {
  id: string;
  name: string;
  address?: string | null;
  notes?: string | null;
  unit_count: number;
  occupied_count: number;
  vacant_count: number;
  archived_at?: string | null;
  created_at: string;
  updated_at: string;
  units: UnitOut[];
}

export interface PropertyArchiveResponse {
  message: string;
  archived_at: string;
}

// ==========================================
// Unit
// ==========================================

export type UnitType = 'FLAT' | 'ROOM' | 'SHOP' | 'OTHER';

export interface CurrentTenantBrief {
  id: string;
  name: string;
}

export interface UnitCreate {
  name: string;
  unit_type: UnitType;
  monthly_rent_paise: number;
  rent_due_day: number; // 1-28
  notes?: string | null;
}

export interface UnitUpdate {
  name?: string | null;
  unit_type?: UnitType | null;
  monthly_rent_paise?: number | null;
  rent_due_day?: number | null;
  notes?: string | null;
}

export interface UnitOut {
  id: string;
  property_id: string;
  name: string;
  unit_type: string;
  monthly_rent_paise: number;
  rent_due_day: number;
  notes?: string | null;
  archived_at?: string | null;
  created_at: string;
  updated_at: string;
  is_occupied: boolean;
  current_tenant?: CurrentTenantBrief | null;
}

export interface UnitArchiveResponse {
  message: string;
  archived_at: string;
}

// ==========================================
// Tenant
// ==========================================

export type TenantStatus = 'ACTIVE' | 'INACTIVE';

export interface TenantUnitBrief {
  id: string;
  name: string;
  property_name: string;
}

export interface TenantCreate {
  unit_id: string;
  name: string;
  phone: string;
  email?: string | null;
  move_in_date: string; // YYYY-MM-DD
  security_deposit_paise?: number;
  notes?: string | null;
}

export interface TenantUpdate {
  name?: string | null;
  phone?: string | null;
  email?: string | null;
  move_in_date?: string | null;
  security_deposit_paise?: number | null;
  notes?: string | null;
}

export interface TenantDeactivateRequest {
  move_out_date?: string | null; // YYYY-MM-DD
}

export interface TenantDeactivateResponse {
  message: string;
  tenant_status: string;
  unit_status: string;
}

export interface TenantListItem {
  id: string;
  name: string;
  phone: string;
  email?: string | null;
  unit: TenantUnitBrief;
  move_in_date: string;
  status: string;
  current_month_rent_status?: string | null;
}

export interface TenantListResponse {
  items: TenantListItem[];
  total: number;
  page: number;
  per_page: number;
}

export interface TenantRentHistoryItem {
  id: string;
  month: number;
  year: number;
  expected_amount_paise: number;
  total_paid_paise: number;
  due_date: string;
  status: string;
  payments: PaymentDetail[];
}

export interface TenantDetail {
  id: string;
  name: string;
  phone: string;
  email?: string | null;
  unit: TenantUnitBrief;
  move_in_date: string;
  move_out_date?: string | null;
  security_deposit_paise: number;
  status: string;
  notes?: string | null;
  rent_history: TenantRentHistoryItem[];
  created_at: string;
  updated_at: string;
}

// ==========================================
// Rent Record
// ==========================================

export type RentStatus = 'PENDING' | 'DUE' | 'OVERDUE' | 'PAID' | 'PARTIALLY_PAID';

export interface RentRecordUpdate {
  expected_amount_paise?: number | null;
  notes?: string | null;
}

export interface RentRecordVoidRequest {
  reason?: string | null;
}

export interface RentRecordVoidResponse {
  message: string;
  id: string;
  is_void: boolean;
}

export interface RentRecordListItem {
  id: string;
  tenant_name: string;
  unit_name: string;
  property_name: string;
  expected_amount_paise: number;
  total_paid_paise: number;
  due_date: string;
  status: string;
  last_reminder_at?: string | null;
}

export interface RentSummary {
  total_expected_paise: number;
  total_collected_paise: number;
  total_pending_paise: number;
  paid_count: number;
  due_count: number;
  overdue_count: number;
}

export interface RentListResponse {
  month: number;
  year: number;
  summary: RentSummary;
  items: RentRecordListItem[];
}

export interface RentRecordPaymentItem {
  id: string;
  amount_paise: number;
  payment_method: string;
  paid_date: string;
  notes?: string | null;
}

export interface RentRecordDetail {
  id: string;
  tenant_id: string;
  tenant_name: string;
  unit_id: string;
  unit_name: string;
  property_id: string;
  property_name: string;
  month: number;
  year: number;
  expected_amount_paise: number;
  total_paid_paise: number;
  due_date: string;
  status: string;
  notes?: string | null;
  is_void: boolean;
  payments: RentRecordPaymentItem[];
  created_at: string;
  updated_at: string;
}

// ==========================================
// Payment
// ==========================================

export type PaymentMethod = 'CASH' | 'UPI' | 'BANK_TRANSFER' | 'OTHER';

export interface PaymentCreate {
  amount_paise: number;
  payment_method: PaymentMethod;
  paid_date: string; // YYYY-MM-DD
  notes?: string | null;
  confirm_excess?: boolean;
}

export interface PaymentUpdate {
  amount_paise?: number | null;
  payment_method?: PaymentMethod | null;
  paid_date?: string | null;
  notes?: string | null;
  confirm_excess?: boolean;
}

export interface PaymentVoidRequest {
  reason?: string | null;
}

export interface PaymentVoidResponse {
  message: string;
  id: string;
  is_void: boolean;
}

export interface PaymentDetail {
  id: string;
  rent_record_id: string;
  amount_paise: number;
  payment_method: string;
  paid_date: string;
  notes?: string | null;
  is_void: boolean;
  created_at: string;
  updated_at: string;
}

export interface RentRecordBriefStatus {
  id: string;
  expected_amount_paise: number;
  total_paid_paise: number;
  status: string;
}

export interface PaymentCreateResponse {
  payment: PaymentDetail;
  rent_record: RentRecordBriefStatus;
}

// ==========================================
// Dashboard
// ==========================================

export interface DashboardDueItem {
  tenant_name: string;
  unit_name: string;
  property_name: string;
  amount_paise: number;
  rent_record_id: string;
  tenant_id?: string | null;
  tenant_phone?: string | null;
  due_date?: string | null;
}

export interface DashboardOverdueItem {
  tenant_name: string;
  unit_name: string;
  property_name: string;
  amount_paise: number;
  due_date: string;
  rent_record_id: string;
  tenant_id?: string | null;
  tenant_phone?: string | null;
  days_overdue?: number | null;
}

export interface DashboardRecentPaymentItem {
  tenant_name: string;
  amount_paise: number;
  payment_method: string;
  paid_date: string;
  id?: string | null;
  unit_name?: string | null;
  property_name?: string | null;
}

export interface DashboardSummaryBreakdown {
  total_expected_paise: number;
  total_collected_paise: number;
  total_pending_paise: number;
  paid_count: number;
  due_count: number;
  overdue_count: number;
}

export interface DashboardSummaryResponse {
  month: number;
  year: number;
  total_expected_paise: number;
  total_collected_paise: number;
  total_pending_paise: number;
  paid_count: number;
  due_count: number;
  overdue_count: number;
  total_units: number;
  occupied_units: number;
  vacant_units: number;
  todays_due: DashboardDueItem[];
  overdue_list: DashboardOverdueItem[];
  recent_payments: DashboardRecentPaymentItem[];
  summary?: DashboardSummaryBreakdown | null;
}

// ==========================================
// Reminders
// ==========================================

export interface ReminderCreateRequest {
  message?: string | null;
  channel?: string;
}

export interface TenantReminderCreateRequest {
  rent_record_id: string;
  message?: string | null;
  channel?: string;
}

export interface ReminderCreateResponse {
  id: string;
  tenant_id: string;
  rent_record_id: string;
  whatsapp_url: string;
  message: string;
  remaining_amount_paise: number;
  sent_at: string;
}

export interface ReminderListItem {
  id: string;
  tenant_id: string;
  rent_record_id: string;
  channel: string;
  message: string;
  sent_at: string;
  created_at: string;
  whatsapp_url?: string | null;
}

// ==========================================
// Reports
// ==========================================

export interface MonthlyReportSummary {
  total_expected_paise: number;
  total_collected_paise: number;
  total_pending_paise: number;
  paid_count: number;
  partially_paid_count: number;
  due_count: number;
  overdue_count: number;
}

export interface MonthlyReportPaymentBreakdown {
  cash_paise: number;
  upi_paise: number;
  bank_transfer_paise: number;
  other_paise: number;
}

export interface OutstandingTenantItem {
  tenant_id: string;
  tenant_name: string;
  property_id: string;
  property_name: string;
  unit_id: string;
  unit_name: string;
  rent_record_id: string;
  expected_amount_paise: number;
  paid_amount_paise: number;
  remaining_amount_paise: number;
  status: string;
  due_date: string;
  days_overdue: number;
}

export interface OutstandingSummary {
  total_count: number;
  total_amount_paise: number;
  tenants: OutstandingTenantItem[];
}

export interface MonthlyReportResponse {
  month: number;
  year: number;
  summary: MonthlyReportSummary;
  payment_breakdown: MonthlyReportPaymentBreakdown;
  outstanding: OutstandingSummary;
}
