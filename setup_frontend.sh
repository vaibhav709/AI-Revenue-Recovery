#!/bin/bash
set -e

cd /Users/vaibhav/Desktop/Projects/AI-Revenue-Recovery/frontend

# Create directory structure
mkdir -p src/components/{common,layout,dashboard,analysis,recovery}
mkdir -p src/pages
mkdir -p src/services
mkdir -p src/types
mkdir -p src/hooks
mkdir -p src/context
mkdir -p src/utils

# Overwrite tailwind.config.js
cat << 'EOF' > tailwind.config.js
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f0f5ff',
          100: '#e5edff',
          200: '#cddbfe',
          300: '#b4c6fc',
          400: '#8da2fb',
          500: '#6875f5',
          600: '#5850ec',
          700: '#5145cd',
          800: '#42389d',
          900: '#362f78',
        }
      }
    },
  },
  plugins: [],
}
EOF

# Overwrite index.css
cat << 'EOF' > src/index.css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  body {
    @apply bg-gray-50 text-gray-900;
  }
}
EOF

# Create types/index.ts
cat << 'EOF' > src/types/index.ts
export interface RecoveryAnalysisRequest {
  customer_id: number;
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
  num_delayed_payments: number;
  max_payment_delay: number;
  avg_payment_delay: number;
  recent_payment_delay: number;
  avg_bill_amount: number;
  avg_payment_amount: number;
  total_bill_amount: number;
  total_payment_amount: number;
  payment_to_bill_ratio: number;
  credit_utilization: number;
  payment_std: number;
  recent_payment_amount: number;
  recent_bill_amount: number;
  recent_payment_ratio: number;
}

export interface FinalRecoveryPlan {
  customer_id: number;
  priority: "ROUTINE" | "PROACTIVE" | "HIGH";
  strategy: "BALANCE_CLARIFICATION" | "ESCALATED_RECOVERY";
  communication_channel: "EMAIL" | "SMS" | "PHONE";
  follow_up_days: number;
  escalation_candidate: boolean;
  final_action: string;
  customer_message: string;
  follow_up_action: string;
}
EOF

# Create services/api.ts
cat << 'EOF' > src/services/api.ts
import axios from 'axios';
import { RecoveryAnalysisRequest, FinalRecoveryPlan } from '../types';

const api = axios.create({
  baseURL: 'http://localhost:8000', // Assuming FastAPI runs on 8000
});

export const analyzeCustomer = async (data: RecoveryAnalysisRequest): Promise<FinalRecoveryPlan> => {
  const response = await api.post<FinalRecoveryPlan>('/recovery/analyze', data);
  return response.data;
};

// Mock api for case list
export const fetchCases = async () => {
    return [];
}
EOF

echo "Scaffolding complete"
