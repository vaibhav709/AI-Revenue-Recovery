export interface RecoveryAnalysisRequest {
  customer_id: number;
  nickname?: string;
  credit_limit: number;
  gender: number;
  education: number;
  marital_status: number;
  age: number;
  pay_status_1: number;
  pay_status_2: number;
  pay_status_3: number;
  pay_status_4: number;
  pay_status_5: number;
  pay_status_6: number;
  bill_amount_1: number;
  bill_amount_2: number;
  bill_amount_3: number;
  bill_amount_4: number;
  bill_amount_5: number;
  bill_amount_6: number;
  payment_amount_1: number;
  payment_amount_2: number;
  payment_amount_3: number;
  payment_amount_4: number;
  payment_amount_5: number;
  payment_amount_6: number;

}

export interface FinalRecoveryPlan {
  customer_id: number;
  failure_probability: number;
  predicted_failure: boolean;
  risk_level: "LOW" | "MEDIUM" | "HIGH" | "PROACTIVE";
  credit_utilization: number;
  payment_to_bill_ratio: number;
  priority: "ROUTINE" | "PROACTIVE" | "HIGH" | "URGENT" | "STANDARD";
  strategy: string;
  communication_channel: "EMAIL" | "SMS" | "PHONE";
  follow_up_days: number;
  escalation_candidate: boolean;
  final_action: string;
  customer_message: string;
  follow_up_action: string;
}

export interface CustomerListItem {
  id: number;
  customer_id: number;
  nickname?: string;
  credit_limit: number;
  risk: string;
  status: string;
  updated_at: string;
}

export interface RecoveryCaseItem {
  id: number;
  customer_id: number;
  nickname?: string;
  failure_probability: number;
  predicted_failure: boolean;
  risk_level: string;
  priority: string;
  strategy: string;
  communication_channel: string;
  follow_up_days: number;
  escalation_candidate: boolean;
  final_action: string;
  customer_message: string;
  follow_up_action: string;
  status: string;
  amount_at_risk: number;
  amount_recovered: number;
  recovery_status: string;
  recovery_completed_at?: string | null;
  attempt_count: number;
  max_attempts: number;
  last_attempt_at?: string | null;
  escalation_reason?: string | null;
  ai_decision?: string | null;
  ai_recommended_action?: string | null;
  ai_reasoning?: string | null;
  ai_confidence?: number | null;
  ai_communication_channel?: string | null;
  ai_follow_up_days?: number | null;
  ai_customer_message?: string | null;
  priority_score?: number | null;
  priority_tier?: string | null;
  priority_factors?: string | null;
  created_at: string;
  updated_at: string;
}

export interface CustomerDetailResponse {
  customer: any;
  latest_case: RecoveryCaseItem | null;
  history: RecoveryCaseItem[];
}

export interface RecoveryCaseDetailResponse {
  case: RecoveryCaseItem;
  customer: any;
}

export interface DashboardMetrics {
  total_analyzed: number;
  high_risk: number;
  proactive: number;
  escalated: number;
}

export interface BatchAnalysisResponse {
  success: boolean;
  total_analyzed: number;
  new_cases_created: number;
  existing_cases_updated: number;
  cases_skipped: number;
  critical_cases: number;
  high_priority_cases: number;
  medium_priority_cases: number;
  low_priority_cases: number;
  errors: any[];
}
