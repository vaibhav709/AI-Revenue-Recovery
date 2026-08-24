import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer,
  PieChart, Pie, Cell
} from 'recharts';
import { RefreshCw, AlertCircle, TrendingUp, CheckCircle, Clock, ShieldAlert, Activity, Sparkles } from 'lucide-react';
import { getPortfolioAnalytics, generatePortfolioInsights } from '../services/api';

const formatINR = (amount: number | null | undefined) => {
  if (amount == null || isNaN(amount)) return '₹0';
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0
  }).format(amount);
};

const formatDate = (dateString: string | null) => {
  if (!dateString) return 'Not scheduled';
  return new Date(dateString).toLocaleString('en-IN', {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
  });
};

const RISK_COLORS: Record<string, string> = {
  'HIGH': '#ef4444',
  'MEDIUM': '#f59e0b',
  'LOW': '#10b981',
  'UNKNOWN': '#9ca3af'
};

export default function Analytics() {
  const navigate = useNavigate();
  
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [aiInsights, setAiInsights] = useState<any>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [aiError, setAiError] = useState<string | null>(null);

  const handleAnalyzePortfolio = async () => {
    setIsAnalyzing(true);
    setAiError(null);
    try {
      const res = await generatePortfolioInsights();
      if (res.success && res.available) {
        setAiInsights(res.insights);
      } else {
        setAiError(res.reason || "AI insights not available.");
      }
    } catch (err: any) {
      setAiError(err.response?.data?.detail || "Failed to generate AI insights.");
    } finally {
      setIsAnalyzing(false);
    }
  };


  const fetchAnalytics = async () => {
    setLoading(true);
    try {
      const response = await getPortfolioAnalytics();
      setData(response);
    } catch (err) {
      console.error("Unable to load portfolio analytics.", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, []);

  if (loading && !data) {
    return <div className="p-8 flex justify-center"><div className="w-8 h-8 rounded-full border-2 border-indigo-200 border-t-indigo-600 animate-spin"></div></div>;
  }

  const kpis = data?.kpis || {};
  const riskDistObj = data?.distributions?.risk || {};
  const riskDistData = Object.keys(riskDistObj).map(k => ({ name: k, value: riskDistObj[k] }));
  const topCases = data?.lists?.top_cases || [];
  const pendingActions = data?.lists?.pending_actions || [];
  const recentActivity = data?.lists?.recent_activity || [];

  return (
    <div className="space-y-6 pb-12">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Portfolio Monitoring</h1>
          <p className="text-gray-500 text-sm mt-1">Read-only overview of the entire recovery portfolio.</p>
        </div>
        <button 
          onClick={fetchAnalytics}
          className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors shadow-sm"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-indigo-600' : 'text-gray-400'}`} />
          Refresh
        </button>
      </div>


      {/* AI Portfolio Intelligence */}
      <div className="bg-indigo-50/50 p-6 rounded-xl border border-indigo-100 shadow-sm">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
          <div>
            <h2 className="text-lg font-bold text-indigo-900 flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-indigo-600" />
              AI Portfolio Intelligence
            </h2>
            <p className="text-sm text-indigo-700/80 mt-1">Advisory AI-generated recommendation layer (GPT-5.6 Luna).</p>
          </div>
          <button 
            onClick={handleAnalyzePortfolio}
            disabled={isAnalyzing}
            className="flex items-center gap-2 px-5 py-2.5 bg-indigo-600 text-white rounded-lg text-sm font-semibold hover:bg-indigo-700 disabled:opacity-70 disabled:cursor-not-allowed transition-colors shadow-sm"
          >
            {isAnalyzing ? (
              <><RefreshCw className="w-4 h-4 animate-spin" /> Analyzing Portfolio...</>
            ) : (
              <><Sparkles className="w-4 h-4" /> Analyze Portfolio</>
            )}
          </button>
        </div>

        {aiError && (
          <div className="mb-6 p-4 bg-red-50 text-red-700 border border-red-200 rounded-lg flex items-center gap-2 text-sm font-medium">
            <AlertCircle className="w-5 h-5" />
            {aiError}
          </div>
        )}

        {aiInsights && (
          <div className="space-y-6">
            <div className="bg-white p-5 rounded-lg border border-indigo-100">
              <h3 className="text-sm font-bold text-gray-500 uppercase tracking-wider mb-2">AI Portfolio Assessment</h3>
              <p className="text-gray-800 font-medium">{aiInsights.portfolio_summary}</p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-white p-5 rounded-lg border border-indigo-100 space-y-4">
                <h3 className="text-sm font-bold text-gray-500 uppercase tracking-wider">Key Findings</h3>
                {aiInsights.key_findings.map((kf: any, i: number) => (
                  <div key={i} className="flex gap-3">
                    <div className="mt-0.5">
                      {kf.severity === 'HIGH' ? '🔴' : kf.severity === 'MEDIUM' ? '🟠' : '🟡'}
                    </div>
                    <div>
                      <div className="font-semibold text-gray-900">{kf.title}</div>
                      <div className="text-sm text-gray-600 mt-0.5">{kf.description}</div>
                    </div>
                  </div>
                ))}
              </div>

              <div className="bg-white p-5 rounded-lg border border-indigo-100 space-y-4">
                <h3 className="text-sm font-bold text-gray-500 uppercase tracking-wider">Recommended Focus</h3>
                {aiInsights.recommended_focus.map((rf: any, i: number) => (
                  <div key={i} className="border-l-2 pl-3 border-indigo-300">
                    <div className="font-semibold text-indigo-900 cursor-pointer hover:underline" onClick={() => navigate(`/cases/${rf.case_id}`)}>
                      Customer {rf.case_id}
                    </div>
                    <div className="text-sm text-gray-600 mt-0.5">{rf.reason}</div>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-white p-5 rounded-lg border border-indigo-100">
              <h3 className="text-sm font-bold text-gray-500 uppercase tracking-wider mb-3">Human Review Required</h3>
              <ul className="list-disc list-inside space-y-2 text-sm text-gray-700">
                {aiInsights.human_actions.map((act: string, i: number) => (
                  <li key={i}>{act}</li>
                ))}
              </ul>
            </div>

            <div className="flex justify-end text-xs font-semibold text-indigo-400">
              AI Confidence: {Math.round(aiInsights.confidence * 100)}%
            </div>
          </div>
        )}
      </div>

      {/* Main KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
          <div className="text-gray-500 text-sm font-medium mb-1">Revenue at Risk</div>
          <div className="text-2xl font-bold text-gray-900">{formatINR(kpis.total_amount_at_risk)}</div>
        </div>
        <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
          <div className="text-gray-500 text-sm font-medium mb-1">Revenue Recovered</div>
          <div className="text-2xl font-bold text-emerald-600">{formatINR(kpis.total_amount_recovered)}</div>
        </div>
        <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
          <div className="text-gray-500 text-sm font-medium mb-1">Recovery Rate</div>
          <div className="text-2xl font-bold text-indigo-600">
            {isNaN(kpis.recovery_rate) ? '0' : Number(kpis.recovery_rate).toFixed(1)}%
          </div>
        </div>
        <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
          <div className="text-gray-500 text-sm font-medium mb-1">Active Cases</div>
          <div className="text-2xl font-bold text-gray-900">{kpis.active_cases || 0}</div>
        </div>
      </div>

      {/* Secondary Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm flex items-center gap-4">
          <div className="p-3 bg-red-100 text-red-600 rounded-lg"><ShieldAlert className="w-5 h-5" /></div>
          <div>
            <div className="text-gray-500 text-xs font-medium uppercase tracking-wider">High Risk Cases</div>
            <div className="text-lg font-bold text-gray-900">{riskDistObj['HIGH'] || 0}</div>
          </div>
        </div>
        <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm flex items-center gap-4">
          <div className="p-3 bg-blue-100 text-blue-600 rounded-lg"><Clock className="w-5 h-5" /></div>
          <div>
            <div className="text-gray-500 text-xs font-medium uppercase tracking-wider">Pending Actions</div>
            <div className="text-lg font-bold text-gray-900">{kpis.pending_actions || 0}</div>
          </div>
        </div>
        <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm flex items-center gap-4">
          <div className="p-3 bg-emerald-100 text-emerald-600 rounded-lg"><CheckCircle className="w-5 h-5" /></div>
          <div>
            <div className="text-gray-500 text-xs font-medium uppercase tracking-wider">Executed Actions</div>
            <div className="text-lg font-bold text-gray-900">{kpis.executed_actions || 0}</div>
          </div>
        </div>
        <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm flex items-center gap-4">
          <div className="p-3 bg-orange-100 text-orange-600 rounded-lg"><TrendingUp className="w-5 h-5" /></div>
          <div>
            <div className="text-gray-500 text-xs font-medium uppercase tracking-wider">Escalations</div>
            <div className="text-lg font-bold text-gray-900">{kpis.escalated_cases || 0}</div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Risk Distribution */}
        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm lg:col-span-1">
          <h3 className="text-base font-semibold text-gray-900 mb-6">Risk Distribution</h3>
          <div className="h-64">
            {riskDistData.length === 0 ? (
              <div className="h-full flex items-center justify-center text-gray-400">No cases available</div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={riskDistData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {riskDistData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={RISK_COLORS[entry.name] || RISK_COLORS.UNKNOWN} />
                    ))}
                  </Pie>
                  <RechartsTooltip />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>
          <div className="flex justify-center gap-4 mt-2">
            {riskDistData.map(r => (
               <div key={r.name} className="flex items-center gap-2">
                 <div className="w-3 h-3 rounded-full" style={{ backgroundColor: RISK_COLORS[r.name] || RISK_COLORS.UNKNOWN }}></div>
                 <span className="text-xs text-gray-600">{r.name}</span>
               </div>
            ))}
          </div>
        </div>

        {/* Recovery Pipeline */}
        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm lg:col-span-2 flex flex-col">
          <h3 className="text-base font-semibold text-gray-900 mb-2">Recovery Pipeline</h3>
          <p className="text-xs text-gray-500 mb-8">Note: An Executed action represents a sent communication, NOT a successful payment.</p>
          
          <div className="flex-1 flex items-center justify-between relative px-4">
            {/* Connecting Line */}
            <div className="absolute top-1/2 left-8 right-8 h-1 bg-gray-100 -translate-y-1/2 z-0"></div>
            
            {[
              { label: 'At Risk', value: formatINR(kpis.total_amount_at_risk), color: 'bg-red-100 text-red-600' },
              { label: 'Active Cases', value: kpis.active_cases || 0, color: 'bg-orange-100 text-orange-600' },
              { label: 'Pending Actions', value: kpis.pending_actions || 0, color: 'bg-blue-100 text-blue-600' },
              { label: 'Executed', value: kpis.executed_actions || 0, color: 'bg-indigo-100 text-indigo-600', note: '≠ Recovered' },
              { label: 'Recovered', value: formatINR(kpis.total_amount_recovered), color: 'bg-emerald-100 text-emerald-600' },
            ].map((step, i) => (
              <div key={step.label} className="relative z-10 flex flex-col items-center group">
                <div className={`w-16 h-16 rounded-full flex items-center justify-center font-bold text-sm border-4 border-white shadow-md ${step.color} transition-transform group-hover:scale-110`}>
                  {step.value}
                </div>
                <div className="mt-3 text-sm font-semibold text-gray-700">{step.label}</div>
                {step.note && <div className="text-[10px] text-gray-400 font-medium absolute -bottom-4">{step.note}</div>}
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Pending Actions */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden flex flex-col">
          <div className="p-4 border-b border-gray-100 bg-gray-50/50">
            <h3 className="text-sm font-semibold text-gray-900 flex items-center gap-2">
              <Clock className="w-4 h-4 text-blue-500" />
              Pending Actions
            </h3>
          </div>
          <div className="overflow-x-auto flex-1">
            <table className="w-full text-left text-sm whitespace-nowrap">
              <thead className="bg-gray-50 text-gray-500">
                <tr>
                  <th className="px-4 py-3 font-medium">Customer</th>
                  <th className="px-4 py-3 font-medium">Action</th>
                  <th className="px-4 py-3 font-medium">Scheduled</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {pendingActions.length === 0 ? (
                  <tr>
                    <td colSpan={3} className="px-4 py-8 text-center text-gray-400">No pending actions</td>
                  </tr>
                ) : (
                  pendingActions.map((act: any) => (
                    <tr key={act.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 font-medium text-gray-900">{act.customer_name}</td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-1.5">
                          <span className="text-xs font-medium bg-gray-100 text-gray-700 px-2 py-0.5 rounded">{act.action_type}</span>
                          <span className="text-xs text-gray-500">via {act.channel}</span>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`text-xs ${act.is_overdue ? 'text-red-600 font-semibold' : 'text-gray-500'}`}>
                          {formatDate(act.scheduled_for)}
                          {act.is_overdue && ' (Overdue)'}
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Recent Execution Activity */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden flex flex-col">
          <div className="p-4 border-b border-gray-100 bg-gray-50/50">
            <h3 className="text-sm font-semibold text-gray-900 flex items-center gap-2">
              <Activity className="w-4 h-4 text-indigo-500" />
              Recent Execution Activity
            </h3>
          </div>
          <div className="overflow-x-auto flex-1">
            <table className="w-full text-left text-sm whitespace-nowrap">
              <thead className="bg-gray-50 text-gray-500">
                <tr>
                  <th className="px-4 py-3 font-medium">Time</th>
                  <th className="px-4 py-3 font-medium">Customer</th>
                  <th className="px-4 py-3 font-medium">Action</th>
                  <th className="px-4 py-3 font-medium">Result</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {recentActivity.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="px-4 py-8 text-center text-gray-400">No execution activity yet</td>
                  </tr>
                ) : (
                  recentActivity.map((act: any) => (
                    <tr key={act.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-xs text-gray-500">{formatDate(act.time)}</td>
                      <td className="px-4 py-3 font-medium text-gray-900">{act.customer_name}</td>
                      <td className="px-4 py-3 text-gray-600 text-xs">{act.action_type}</td>
                      <td className="px-4 py-3">
                        <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                          act.result === 'SUCCESS' ? 'bg-emerald-100 text-emerald-700' :
                          act.result === 'FAILED' ? 'bg-red-100 text-red-700' :
                          'bg-gray-100 text-gray-700'
                        }`}>
                          {act.result}
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Top Cases Requiring Attention */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <div className="p-4 border-b border-gray-100 bg-gray-50/50">
          <h3 className="text-sm font-semibold text-gray-900 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-orange-500" />
            Top Cases Requiring Attention
          </h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm whitespace-nowrap">
            <thead className="bg-gray-50 text-gray-500">
              <tr>
                <th className="px-6 py-4 font-medium">Customer</th>
                <th className="px-6 py-4 font-medium">Risk</th>
                <th className="px-6 py-4 font-medium">Priority</th>
                <th className="px-6 py-4 font-medium">Amount at Risk</th>
                <th className="px-6 py-4 font-medium">Recovered</th>
                <th className="px-6 py-4 font-medium text-center">Attempts</th>
                <th className="px-6 py-4 font-medium">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {topCases.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center text-gray-400">No recovery cases yet</td>
                </tr>
              ) : (
                topCases.map((c: any) => (
                  <tr 
                    key={c.id} 
                    onClick={() => navigate(`/cases/${c.id}`)}
                    className="hover:bg-gray-50 cursor-pointer transition-colors"
                  >
                    <td className="px-6 py-4 font-medium text-gray-900">{c.customer_name}</td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                        c.risk_level === 'HIGH' ? 'bg-red-100 text-red-700' :
                        c.risk_level === 'MEDIUM' ? 'bg-orange-100 text-orange-700' :
                        'bg-emerald-100 text-emerald-700'
                      }`}>
                        {c.risk_level}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${
                        c.priority === 'HIGH' ? 'border-red-200 text-red-700 bg-red-50' :
                        c.priority === 'MEDIUM' ? 'border-orange-200 text-orange-700 bg-orange-50' :
                        'border-gray-200 text-gray-700 bg-gray-50'
                      }`}>
                        {c.priority}
                      </span>
                    </td>
                    <td className="px-6 py-4 font-medium text-gray-900">{formatINR(c.amount_at_risk)}</td>
                    <td className="px-6 py-4 text-emerald-600 font-medium">{formatINR(c.amount_recovered)}</td>
                    <td className="px-6 py-4 text-center">
                      <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-gray-100 text-xs font-medium text-gray-700">
                        {c.attempt_count}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                        c.status === 'Completed' ? 'bg-emerald-100 text-emerald-700' :
                        c.status === 'Escalated' ? 'bg-red-100 text-red-700' :
                        'bg-blue-100 text-blue-700'
                      }`}>
                        {c.status}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
