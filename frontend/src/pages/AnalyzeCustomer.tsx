import { useState } from 'react';
import { 
  ChevronDown, ChevronUp, AlertCircle, CheckCircle2, Copy, Shield, 
  FileText, Search, RefreshCcw, Edit3, ArrowRight, Activity, Calendar
} from 'lucide-react';
import clsx from 'clsx';
import { formatINR } from '../utils/formatters';
import { analyzeCustomer } from '../services/api';
import { RecoveryAnalysisRequest, FinalRecoveryPlan } from '../types';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, Legend
} from 'recharts';

const initialFormState: RecoveryAnalysisRequest = {
  customer_id: 8681,
  nickname: '',
  credit_limit: 50000,
  gender: 2,
  education: 2,
  marital_status: 1,
  age: 37,
  pay_status_1: 2,
  pay_status_2: 2,
  pay_status_3: 0,
  pay_status_4: 0,
  pay_status_5: 0,
  pay_status_6: 0,
  bill_amount_1: 39177,
  bill_amount_2: 40608,
  bill_amount_3: 31086,
  bill_amount_4: 31808,
  bill_amount_5: 32626,
  bill_amount_6: 33496,
  payment_amount_1: 2000,
  payment_amount_2: 1500,
  payment_amount_3: 1500,
  payment_amount_4: 1500,
  payment_amount_5: 1500,
  payment_amount_6: 1500,

};

const Section = ({ title, children, defaultOpen = false }: any) => {
  const [isOpen, setIsOpen] = useState(defaultOpen);
  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden mb-4">
      <button 
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-6 py-4 flex items-center justify-between bg-white hover:bg-gray-50 transition-colors focus:outline-none"
      >
        <h2 className="text-base font-semibold text-gray-900">{title}</h2>
        {isOpen ? <ChevronUp className="w-5 h-5 text-gray-400" /> : <ChevronDown className="w-5 h-5 text-gray-400" />}
      </button>
      {isOpen && (
        <div className="px-6 pb-6 pt-2 border-t border-gray-100">
          {children}
        </div>
      )}
    </div>
  );
};

export default function AnalyzeCustomer() {
  const [formData, setFormData] = useState<RecoveryAnalysisRequest>(initialFormState);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<FinalRecoveryPlan | null>(null);
  const [activeTab, setActiveTab] = useState('Overview');
  const [copied, setCopied] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: name === 'nickname' ? value : Number(value) }));
  };

  const handleCopy = () => {
    if (result) {
      navigator.clipboard.writeText(result.customer_message);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const plan = await analyzeCustomer(formData);
      setResult(plan);
      setActiveTab('Overview');
    } catch (err: any) {
      setError(err.response?.data?.detail || "An unexpected error occurred while processing the recovery analysis.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleEdit = () => {
    setResult(null);
  };

  const handleRegenerate = () => {
    handleSubmit();
  };

  if (result) {
    const tabs = ['Overview', 'Risk Analysis', 'Recovery Plan', 'Communication'];
    const riskPercentage = (result.failure_probability * 100).toFixed(1);
    const utilizationPct = (result.credit_utilization * 100).toFixed(2);
    const p2bPct = (result.payment_to_bill_ratio * 100).toFixed(2);
    
    const riskColors = {
      LOW: { text: 'text-emerald-600', border: 'border-emerald-500', bg: 'bg-emerald-50', badge: 'bg-emerald-100 text-emerald-800' },
      PROACTIVE: { text: 'text-blue-600', border: 'border-blue-500', bg: 'bg-blue-50', badge: 'bg-blue-100 text-blue-800' },
      HIGH: { text: 'text-amber-600', border: 'border-amber-500', bg: 'bg-amber-50', badge: 'bg-amber-100 text-amber-800' },
    };
    const rColor = riskColors[result.risk_level as keyof typeof riskColors] || riskColors.LOW;

    const paymentBehaviorData = [
      { month: '6 Months Ago', bill: formData.bill_amount_6, payment: formData.payment_amount_6 },
      { month: '5 Months Ago', bill: formData.bill_amount_5, payment: formData.payment_amount_5 },
      { month: '4 Months Ago', bill: formData.bill_amount_4, payment: formData.payment_amount_4 },
      { month: '3 Months Ago', bill: formData.bill_amount_3, payment: formData.payment_amount_3 },
      { month: '2 Months Ago', bill: formData.bill_amount_2, payment: formData.payment_amount_2 },
      { month: 'Last Month', bill: formData.bill_amount_1, payment: formData.payment_amount_1 },
    ];

    return (
      <div className="max-w-6xl mx-auto space-y-6 pb-20">
        <div className="flex items-center justify-between">
           <div>
              <div className="flex items-center text-sm text-gray-500 mb-1">
                 <span className="hover:text-gray-900 cursor-pointer" onClick={() => setResult(null)}>Analyze Customer</span>
                 <span className="mx-2">/</span>
                 <span className="font-medium text-gray-900">Recovery Analysis</span>
              </div>
              <h1 className="text-2xl font-bold text-gray-900">Recovery Analysis</h1>
              <p className="text-gray-500 text-sm mt-1">Customer #{result.customer_id} {formData.nickname ? `(${formData.nickname})` : ''} · Analyzed {new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}</p>
           </div>
           <button onClick={() => setResult(null)} className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors">
             <Search className="w-4 h-4" /> New Analysis
           </button>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <div className="border-b border-gray-200 px-6 pt-2">
            <nav className="flex gap-8">
              {tabs.map(tab => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={clsx(
                    "py-4 text-sm font-medium border-b-2 transition-colors relative",
                    activeTab === tab 
                      ? "border-indigo-600 text-indigo-600" 
                      : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                  )}
                >
                  {tab}
                </button>
              ))}
            </nav>
          </div>

          <div className="p-6 min-h-[500px] bg-gray-50/30">
             
             {/* OVERVIEW TAB */}
             {activeTab === 'Overview' && (
                <div className="space-y-6">
                   <div className="bg-white rounded-xl border border-gray-200 p-6 flex flex-col md:flex-row gap-8 items-center md:items-stretch">
                      <div className="flex-1 flex flex-col items-center justify-center border-r border-gray-100 pr-8">
                         <div className="text-sm font-semibold text-gray-500 tracking-wider mb-4 uppercase">Risk Level</div>
                         <div className={clsx("w-32 h-32 rounded-full border-4 flex items-center justify-center", rColor.border)}>
                            <span className={clsx("text-3xl font-bold", rColor.text)}>{result.risk_level}</span>
                         </div>
                         <div className={clsx("mt-4 text-sm font-medium", rColor.text)}>
                            {result.risk_level === 'LOW' ? 'Not at risk' : result.risk_level === 'PROACTIVE' ? 'Requires attention' : 'High exposure'}
                         </div>
                      </div>
                      
                      <div className="flex-[2] grid grid-cols-1 md:grid-cols-2 gap-4">
                         <div className="bg-gray-50 rounded-lg p-5 border border-gray-100">
                            <div className="text-sm text-gray-500 mb-1">Failure Probability</div>
                            <div className="text-2xl font-bold text-amber-600">{riskPercentage}%</div>
                         </div>
                         <div className="bg-gray-50 rounded-lg p-5 border border-gray-100">
                            <div className="text-sm text-gray-500 mb-1">Predicted Failure</div>
                            <div className={clsx("text-2xl font-bold", result.predicted_failure ? "text-red-600" : "text-emerald-600")}>
                               {result.predicted_failure ? 'Yes' : 'No'}
                            </div>
                         </div>
                         <div className="bg-gray-50 rounded-lg p-5 border border-gray-100">
                            <div className="text-sm text-gray-500 mb-1">Credit Utilization</div>
                            <div className="text-2xl font-bold text-gray-900">{utilizationPct}%</div>
                         </div>
                         <div className="bg-gray-50 rounded-lg p-5 border border-gray-100">
                            <div className="text-sm text-gray-500 mb-1">Payment-to-Bill Ratio</div>
                            <div className="text-2xl font-bold text-gray-900">{p2bPct}%</div>
                         </div>
                      </div>
                   </div>

                   <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
                      <div className="px-6 py-4 border-b border-gray-100 flex justify-between items-center bg-gray-50/50">
                         <h3 className="font-semibold text-gray-900">Recovery Recommendation</h3>
                         <span className="px-3 py-1 bg-indigo-50 text-indigo-700 text-xs font-medium rounded-md border border-indigo-100">Policy decision</span>
                      </div>
                      <div className="p-6 grid grid-cols-2 md:grid-cols-5 gap-6">
                         <div>
                            <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Priority</div>
                            <div className="font-bold text-indigo-600">{result.priority}</div>
                         </div>
                         <div className="col-span-1 md:col-span-1">
                            <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Strategy</div>
                            <div className="font-bold text-gray-900 leading-tight">{result.strategy.replace('_', ' ')}</div>
                         </div>
                         <div>
                            <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Communication</div>
                            <div className="font-bold text-gray-900">{result.communication_channel}</div>
                         </div>
                         <div>
                            <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Follow-up</div>
                            <div className="font-bold text-gray-900">{result.follow_up_days} days</div>
                         </div>
                         <div>
                            <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Escalation</div>
                            <div className="font-bold text-emerald-600">{result.escalation_candidate ? 'Candidate' : 'Not a candidate'}</div>
                         </div>
                      </div>
                      <div className="px-6 py-3 bg-gray-50 border-t border-gray-100 flex items-center gap-2 text-xs text-gray-500">
                         <Shield className="w-3.5 h-3.5" />
                         Decisions generated by the policy engine · AI is used only for communication drafting
                      </div>
                   </div>
                </div>
             )}
             
             {/* RISK ANALYSIS TAB */}
             {activeTab === 'Risk Analysis' && (
                <div className="space-y-6">
                   <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                      <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
                         <div className="text-sm text-gray-500 mb-2">Failure Probability</div>
                         <div className="text-3xl font-bold text-amber-600 mb-4">{riskPercentage}%</div>
                         <div className="w-full bg-gray-100 rounded-full h-2">
                            <div className="bg-amber-500 h-2 rounded-full" style={{ width: `${riskPercentage}%` }}></div>
                         </div>
                      </div>
                      <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
                         <div className="text-sm text-gray-500 mb-2">Risk Level</div>
                         <div className={clsx("text-3xl font-bold mb-2", rColor.text)}>{result.risk_level}</div>
                         <div className={clsx("text-sm", rColor.text)}>{result.risk_level === 'LOW' ? 'Manageable exposure' : 'Review required'}</div>
                      </div>
                      <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
                         <div className="text-sm text-gray-500 mb-2">Predicted Failure</div>
                         <div className={clsx("text-3xl font-bold mb-2 uppercase", result.predicted_failure ? "text-red-600" : "text-emerald-600")}>
                            {result.predicted_failure ? 'TRUE' : 'FALSE'}
                         </div>
                         <div className="text-sm text-gray-500">
                            {result.predicted_failure ? 'Default expected soon' : 'No default expected'}
                         </div>
                      </div>
                   </div>

                   <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
                      <h3 className="text-lg font-bold text-gray-900 mb-6">Key Risk Factors</h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                         <div className="flex justify-between items-center p-4 bg-amber-50/50 border border-amber-100 rounded-lg">
                            <span className="text-gray-700 font-medium">High credit utilization</span>
                            <span className="font-bold text-amber-700">{utilizationPct}%</span>
                         </div>
                         <div className="flex justify-between items-center p-4 bg-amber-50/50 border border-amber-100 rounded-lg">
                            <span className="text-gray-700 font-medium">Payment-to-bill ratio</span>
                            <span className="font-bold text-amber-700">{p2bPct}%</span>
                         </div>
                         <div className="flex justify-between items-center p-4 bg-gray-50 border border-gray-100 rounded-lg">
                            <span className="text-gray-700 font-medium">Recent payment</span>
                            <span className="font-bold text-gray-900">${formData.payment_amount_1.toLocaleString()}</span>
                         </div>
                         <div className="flex justify-between items-center p-4 bg-gray-50 border border-gray-100 rounded-lg">
                            <span className="text-gray-700 font-medium">Recent bill amount</span>
                            <span className="font-bold text-gray-900">${formData.bill_amount_1.toLocaleString()}</span>
                         </div>
                         <div className="flex justify-between items-center p-4 bg-emerald-50/50 border border-emerald-100 rounded-lg">
                            <span className="text-gray-700 font-medium">Payment delays</span>
                            <span className="font-bold text-emerald-700">{[formData.pay_status_1, formData.pay_status_2, formData.pay_status_3, formData.pay_status_4, formData.pay_status_5, formData.pay_status_6].filter(p => p > 0).length}</span>
                         </div>
                         <div className="flex justify-between items-center p-4 bg-gray-50 border border-gray-100 rounded-lg">
                            <span className="text-gray-700 font-medium">Average payment</span>
                            <span className="font-bold text-gray-900">{formatINR((formData.payment_amount_1 + formData.payment_amount_2 + formData.payment_amount_3 + formData.payment_amount_4 + formData.payment_amount_5 + formData.payment_amount_6) / 6)}</span>
                         </div>
                      </div>
                   </div>

                   <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
                      <h3 className="text-lg font-bold text-gray-900 mb-6">Payment Behavior</h3>
                      <div className="h-64">
                         <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={paymentBehaviorData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                               <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f3f4f6" />
                               <XAxis dataKey="month" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#6b7280' }} dy={10} />
                               <YAxis tickFormatter={(val) => `₹${val/1000}k`} axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#6b7280' }} />
                               <RechartsTooltip cursor={{fill: '#f9fafb'}} formatter={(value: number) => `{formatINR(value)}`} />
                               <Legend wrapperStyle={{ paddingTop: '20px' }} iconType="circle" />
                               <Bar dataKey="bill" name="Bill Amount" fill="#e0e7ff" radius={[4, 4, 0, 0]} />
                               <Bar dataKey="payment" name="Payment" fill="#4f46e5" radius={[4, 4, 0, 0]} />
                            </BarChart>
                         </ResponsiveContainer>
                      </div>
                   </div>
                </div>
             )}

             {/* RECOVERY PLAN TAB */}
             {activeTab === 'Recovery Plan' && (
                <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden p-8">
                   <div className="flex justify-between items-center mb-10">
                      <h3 className="text-xl font-bold text-gray-900">Recommended Recovery Plan</h3>
                      <span className="px-3 py-1 bg-indigo-50 text-indigo-700 text-sm font-medium rounded-md border border-indigo-100">Policy decision</span>
                   </div>
                   
                   <div className="relative pl-4 space-y-10">
                      {/* Line connecting the steps */}
                      <div className="absolute left-[31px] top-4 bottom-4 w-0.5 bg-gray-200 z-0"></div>

                      <div className="relative z-10 flex gap-6">
                         <div className="w-12 h-12 rounded-full border-2 border-emerald-500 bg-white flex items-center justify-center shrink-0">
                            <CheckCircle2 className="w-6 h-6 text-emerald-500" />
                         </div>
                         <div>
                            <div className="flex items-center gap-3 mb-1">
                               <h4 className="text-lg font-bold text-gray-900">Analyze payment risk</h4>
                               <span className="px-2 py-0.5 bg-emerald-50 text-emerald-700 text-xs font-medium rounded">ML Risk Engine</span>
                            </div>
                            <p className="text-gray-600">Machine learning model evaluates payment history, credit utilization, and behavioral patterns to compute failure probability.</p>
                         </div>
                      </div>

                      <div className="relative z-10 flex gap-6">
                         <div className="w-12 h-12 rounded-full border-2 border-emerald-500 bg-white flex items-center justify-center shrink-0">
                            <CheckCircle2 className="w-6 h-6 text-emerald-500" />
                         </div>
                         <div>
                            <div className="flex items-center gap-3 mb-1">
                               <h4 className="text-lg font-bold text-gray-900">Apply recovery policy</h4>
                               <span className="px-2 py-0.5 bg-emerald-50 text-emerald-700 text-xs font-medium rounded">Policy Engine</span>
                            </div>
                            <p className="text-gray-600">Deterministic rules map risk score to recovery priority, strategy, communication channel, and follow-up interval.</p>
                         </div>
                      </div>

                      <div className="relative z-10 flex gap-6">
                         <div className="w-12 h-12 rounded-full border-2 border-blue-500 bg-blue-50 flex items-center justify-center shrink-0">
                            <span className="text-blue-600 font-bold">03</span>
                         </div>
                         <div>
                            <div className="flex items-center gap-3 mb-1">
                               <h4 className="text-lg font-bold text-gray-900">Contact customer</h4>
                               <span className="px-2 py-0.5 bg-blue-50 text-blue-700 text-xs font-medium rounded">Communication Service</span>
                            </div>
                            <p className="text-gray-600">AI generates a professional recovery {result.communication_channel.toLowerCase()} aligned to the approved recovery strategy. Message reviewed before dispatch.</p>
                         </div>
                      </div>

                      <div className="relative z-10 flex gap-6 opacity-60">
                         <div className="w-12 h-12 rounded-full border-2 border-gray-300 bg-white flex items-center justify-center shrink-0">
                            <span className="text-gray-400 font-bold">04</span>
                         </div>
                         <div>
                            <div className="flex items-center gap-3 mb-1">
                               <h4 className="text-lg font-bold text-gray-900">Follow up in {result.follow_up_days} days</h4>
                               <span className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs font-medium rounded border border-gray-200">Scheduling Engine</span>
                            </div>
                            <p className="text-gray-600">Automated follow-up scheduled per policy. Status updated if customer responds or resolves their balance.</p>
                         </div>
                      </div>

                      <div className="relative z-10 flex gap-6 opacity-60">
                         <div className="w-12 h-12 rounded-full border-2 border-gray-300 bg-white flex items-center justify-center shrink-0">
                            <span className="text-gray-400 font-bold">05</span>
                         </div>
                         <div>
                            <div className="flex items-center gap-3 mb-1">
                               <h4 className="text-lg font-bold text-gray-900">Review resolution</h4>
                               <span className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs font-medium rounded border border-gray-200">Case Manager</span>
                            </div>
                            <p className="text-gray-600">Analyst reviews outcome and closes the case or escalates to the next recovery tier.</p>
                         </div>
                      </div>

                   </div>
                </div>
             )}

             {/* COMMUNICATION TAB */}
             {activeTab === 'Communication' && (
                <div className="space-y-6">
                   <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                      <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
                         <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">Channel</div>
                         <div className="font-bold text-gray-900">{result.communication_channel}</div>
                      </div>
                      <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
                         <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">Purpose</div>
                         <div className="font-bold text-gray-900">{result.strategy.replace('_', ' ')}</div>
                      </div>
                      <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
                         <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">Generated By</div>
                         <div className="font-bold text-gray-900">AI Assistant</div>
                      </div>
                      <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
                         <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">Policy Basis</div>
                         <div className="font-bold text-gray-900">Recovery Policy v3.2</div>
                      </div>
                   </div>
                   
                   <div className="bg-blue-50 p-4 rounded-lg border border-blue-100 flex items-start gap-3">
                      <AlertCircle className="w-5 h-5 text-blue-600 shrink-0 mt-0.5" />
                      <p className="text-sm text-blue-900">
                         <span className="font-bold">Generated from the approved recovery policy.</span> Strategy, channel, and follow-up timing are policy-engine decisions. AI drafts the message only.
                      </p>
                   </div>

                   <div className="border border-gray-200 rounded-xl overflow-hidden bg-white shadow-sm">
                      <div className="p-6 border-b border-gray-100 bg-gray-50/50 space-y-2">
                         <div className="flex text-sm">
                            <span className="w-16 text-gray-400 font-medium">From</span>
                            <span className="text-gray-900">RecoverIQ Platform &lt;noreply@recoveriq.com&gt;</span>
                         </div>
                         <div className="flex text-sm">
                            <span className="w-16 text-gray-400 font-medium">To</span>
                            <span className="text-gray-900">Customer #{result.customer_id}</span>
                         </div>
                         <div className="flex text-sm pt-2">
                            <span className="w-16 text-gray-400 font-medium">Subject</span>
                            <span className="text-gray-900 font-bold">{result.strategy === 'BALANCE_CLARIFICATION' ? 'Please review your recent billing and payment details' : 'Important information regarding your account balance'}</span>
                         </div>
                      </div>
                      <div className="p-8">
                         <div className="prose prose-sm max-w-none text-gray-800 whitespace-pre-wrap font-sans leading-relaxed">
                            {result.customer_message}
                         </div>
                      </div>
                   </div>

                   <div className="flex items-center gap-3 pt-4">
                      <button 
                         onClick={handleCopy}
                         className="px-6 py-2.5 bg-indigo-600 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white hover:bg-indigo-700 flex items-center gap-2 transition-colors"
                      >
                         {copied ? <CheckCircle2 className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                         {copied ? 'Copied' : 'Copy Message'}
                      </button>
                      <button onClick={handleRegenerate} className="px-6 py-2.5 bg-white border border-gray-300 rounded-lg shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50 flex items-center gap-2 transition-colors">
                         <RefreshCcw className="w-4 h-4" /> Regenerate
                      </button>
                      <button onClick={() => setResult(null)} className="px-6 py-2.5 bg-white border border-gray-300 rounded-lg shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50 flex items-center gap-2 transition-colors">
                         <Edit3 className="w-4 h-4" /> Edit
                      </button>
                   </div>
                </div>
             )}
          </div>
        </div>
      </div>
    );
  }

  // The rest of the Form view remains unchanged from previous step...
  // Wait, I will rewrite it clearly so nothing is lost!
  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-20 relative">
      {isLoading && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-sm">
          <div className="bg-white rounded-2xl p-8 max-w-sm w-full mx-4 shadow-xl flex flex-col items-center text-center">
            <div className="w-16 h-16 rounded-full border-2 border-indigo-100 border-t-indigo-600 animate-spin mb-6"></div>
            <h3 className="text-lg font-bold text-gray-900 mb-2">Analyzing customer...</h3>
            <p className="text-sm text-gray-500">Running payment risk analysis and generating recovery recommendations.</p>
          </div>
        </div>
      )}

      <div>
        <h1 className="text-2xl font-bold text-gray-900">Analyze Customer</h1>
        <p className="text-gray-500 mt-1">Evaluate payment risk and generate an intelligent recovery plan.</p>
      </div>

      <form onSubmit={handleSubmit}>
        <Section title="Customer Information" defaultOpen={true}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Customer ID <span className="text-red-500">*</span></label>
              <input type="number" name="customer_id" value={formData.customer_id} onChange={handleChange} required className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Nickname (Optional)</label>
              <input type="text" name="nickname" value={formData.nickname || ''} onChange={handleChange} placeholder="e.g. Acme Corp" className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Credit Limit <span className="text-red-500">*</span> <span className="text-gray-400 font-normal">(INR)</span></label>
              <input type="number" name="credit_limit" value={formData.credit_limit} onChange={handleChange} required className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Gender</label>
              <select name="gender" value={formData.gender} onChange={handleChange} className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500">
                <option value={1}>Male</option>
                <option value={2}>Female</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Education</label>
              <select name="education" value={formData.education} onChange={handleChange} className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500">
                <option value={1}>Graduate School</option>
                <option value={2}>University</option>
                <option value={3}>High School</option>
                <option value={4}>Others</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Marital Status</label>
              <select name="marital_status" value={formData.marital_status} onChange={handleChange} className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500">
                <option value={1}>Married</option>
                <option value={2}>Single</option>
                <option value={3}>Others</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Age <span className="text-red-500">*</span></label>
              <input type="number" name="age" value={formData.age} onChange={handleChange} required className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500" />
            </div>
          </div>
        </Section>

        <div className="bg-blue-50 border-l-4 border-blue-400 p-4 rounded-r-md">
          <div className="flex items-start">
            <div className="flex-shrink-0 mt-0.5">
              <AlertCircle className="h-5 w-5 text-blue-500" />
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-semibold text-blue-800">Data Accuracy Notice</h3>
              <p className="mt-1 text-sm text-blue-700 leading-relaxed">
                Enter accurate historical billing and payment data. Use 0 only when the actual bill or payment amount was zero. Do not use 0 for missing or unavailable records, as this may affect the calculated features and ML risk prediction. ML results are estimates and should be reviewed by an authorized administrator before taking recovery action.
              </p>
            </div>
          </div>
        </div>

        <Section title="Payment Status History" defaultOpen={true}>
           <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
             {[1, 2, 3, 4, 5, 6].map(num => (
               <div key={`pay_status_${num}`}>
                 <label className="block text-sm font-medium text-gray-700 mb-1">
                   Payment Status {num} {num === 1 && <span className="text-gray-400 font-normal">(Most recent)</span>}
                 </label>
                 <select name={`pay_status_${num}`} value={(formData as any)[`pay_status_${num}`]} onChange={handleChange} className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500">
                    <option value={-1}>Pay duly</option>
                    <option value={0}>No delay</option>
                    <option value={1}>1 month delay</option>
                    <option value={2}>2 months delay</option>
                    <option value={3}>3 months delay</option>
                 </select>
               </div>
             ))}
           </div>
        </Section>
        
        <Section title="Billing History">
           <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
             {[1, 2, 3, 4, 5, 6].map(num => (
               <div key={`bill_amount_${num}`}>
                 <label className="block text-sm font-medium text-gray-700 mb-1">
                   Bill Amount {num}
                 </label>
                 <input type="number" name={`bill_amount_${num}`} value={(formData as any)[`bill_amount_${num}`]} onChange={handleChange} className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500" />
               </div>
             ))}
           </div>
        </Section>
        
        <Section title="Payment History Amounts">
           <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
             {[1, 2, 3, 4, 5, 6].map(num => (
               <div key={`payment_amount_${num}`}>
                 <label className="block text-sm font-medium text-gray-700 mb-1">
                   Payment Amount {num}
                 </label>
                 <input type="number" name={`payment_amount_${num}`} value={(formData as any)[`payment_amount_${num}`]} onChange={handleChange} className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500" />
               </div>
             ))}
           </div>
        </Section>
        


        <div className="flex justify-end gap-3 mt-6">
          <button type="button" onClick={() => setFormData(initialFormState)} className="px-6 py-2.5 bg-white border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors">
            Clear Form
          </button>
          <button type="submit" disabled={isLoading} className="px-6 py-2.5 bg-indigo-600 border border-transparent rounded-md shadow-sm text-sm font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 transition-colors">
            Run Analysis
          </button>
        </div>
      </form>

      {error && (
        <div className="bg-red-50 border-l-4 border-red-500 p-4 rounded-md mt-6 shadow-sm">
          <div className="flex">
            <AlertCircle className="h-5 w-5 text-red-500" />
            <div className="ml-3">
              <p className="text-sm text-red-700 font-medium">{error}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
