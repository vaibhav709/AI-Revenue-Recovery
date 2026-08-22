import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  Users, AlertTriangle, ShieldCheck, TrendingUp, ChevronRight 
} from 'lucide-react';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer,
  PieChart, Pie, Cell 
} from 'recharts';
import clsx from 'clsx';
import { getDashboardMetrics, getRecoveryCases } from '../services/api';
import { DashboardMetrics, RecoveryCaseItem } from '../types';

const RiskBadge = ({ risk }: { risk: string }) => {
  const styles = {
    LOW: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    PROACTIVE: 'bg-blue-50 text-blue-700 border-blue-200',
    HIGH: 'bg-amber-50 text-amber-700 border-amber-200'
  };
  const color = styles[risk as keyof typeof styles] || 'bg-gray-50 text-gray-700 border-gray-200';
  return <span className={clsx("px-2.5 py-1 rounded-full text-xs font-bold border", color)}>{risk}</span>;
};

// Fallback empty charts if no data
const emptyLineData = [{ name: 'Today', low: 0, proactive: 0, high: 0 }];
const emptyPieData = [{ name: 'No Data', value: 100, color: '#e5e7eb' }];

export default function Dashboard() {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [recentCases, setRecentCases] = useState<RecoveryCaseItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [dashMetrics, casesData] = await Promise.all([
          getDashboardMetrics(),
          getRecoveryCases()
        ]);
        setMetrics(dashMetrics);
        setRecentCases(casesData.slice(0, 5));
      } catch (err) {
        console.error("Failed to load dashboard data", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  if (loading) {
    return <div className="p-8 flex justify-center"><div className="w-8 h-8 rounded-full border-2 border-indigo-200 border-t-indigo-600 animate-spin"></div></div>;
  }

  const summaryData = [
    { title: 'Customers Analyzed', value: metrics?.total_analyzed ?? 0, change: 'Lifetime', warning: false, icon: Users, bg: 'bg-blue-50', color: 'text-blue-600' },
    { title: 'High Risk', value: metrics?.high_risk ?? 0, change: 'Current', warning: true, icon: AlertTriangle, bg: 'bg-amber-50', color: 'text-amber-600' },
    { title: 'Proactive Cases', value: metrics?.proactive ?? 0, change: 'Current', warning: false, icon: ShieldCheck, bg: 'bg-emerald-50', color: 'text-emerald-600' },
    { title: 'Escalated', value: metrics?.escalated ?? 0, change: 'Current', warning: false, icon: TrendingUp, bg: 'bg-purple-50', color: 'text-purple-600' },
  ];

  // We are not calculating actual historical chart data for simplicity unless the API provides it.
  // We'll show empty states for the charts if they were hardcoded before, to avoid fabricating data.
  // We can calculate current pie chart data though!
  let pieData = emptyPieData;
  if (metrics && metrics.total_analyzed > 0) {
     const low = metrics.total_analyzed - (metrics.high_risk + metrics.proactive);
     pieData = [
       { name: 'Low Risk', value: low > 0 ? low : 0, color: '#10b981' },
       { name: 'Proactive', value: metrics.proactive, color: '#3b82f6' },
       { name: 'High Risk', value: metrics.high_risk, color: '#f59e0b' }
     ].filter(item => item.value > 0);
  }

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-500 text-sm mt-1">Overview of your recovery operations.</p>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-sm text-gray-500">Last updated just now</span>
          <Link to="/analyze" className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-lg shadow-sm transition-colors">
            New Analysis
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {summaryData.map((item) => (
          <div key={item.title} className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-medium text-gray-500">{item.title}</h3>
              <div className={clsx("p-2 rounded-lg", item.bg, item.color)}>
                <item.icon className="w-5 h-5" />
              </div>
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-bold text-gray-900">{item.value}</span>
            </div>
            <div className="mt-2 text-sm">
              <span className={clsx("font-medium", item.warning ? "text-amber-600" : "text-emerald-600")}>
                {item.change}
              </span>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Line Chart */}
        <div className="lg:col-span-2 bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h3 className="text-base font-semibold text-gray-900">Recovery Overview</h3>
              <p className="text-sm text-gray-500">Cases by risk level over time</p>
            </div>
          </div>
          <div className="h-64 flex items-center justify-center text-gray-400">
             {metrics?.total_analyzed === 0 ? "No historical data available" : (
               <ResponsiveContainer width="100%" height="100%">
                 <LineChart data={emptyLineData} margin={{ top: 5, right: 20, bottom: 5, left: -20 }}>
                   <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
                   <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#6b7280' }} dy={10} />
                   <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#6b7280' }} />
                   <RechartsTooltip />
                   <Line type="monotone" dataKey="low" stroke="#10b981" strokeWidth={2} dot={false} />
                 </LineChart>
               </ResponsiveContainer>
             )}
          </div>
        </div>

        {/* Donut Chart */}
        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
          <div className="mb-6">
            <h3 className="text-base font-semibold text-gray-900">Risk Distribution</h3>
            <p className="text-sm text-gray-500">Current portfolio breakdown</p>
          </div>
          <div className="h-48 relative">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={2}
                  dataKey="value"
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <RechartsTooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-6 space-y-3">
            {pieData.map((item) => (
              <div key={item.name} className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: item.color }}></div>
                  <span className="text-gray-700">{item.name}</span>
                </div>
                <span className="font-medium text-gray-900">{item.value} {metrics?.total_analyzed && metrics.total_analyzed > 0 ? `(${Math.round((item.value / metrics.total_analyzed) * 100)}%)` : ''}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <div className="p-6 border-b border-gray-200 flex justify-between items-center">
          <div>
            <h3 className="text-base font-semibold text-gray-900">Recent Recovery Cases</h3>
            <p className="text-sm text-gray-500">Latest cases from the recovery pipeline</p>
          </div>
          <Link to="/cases" className="text-sm font-medium text-gray-700 hover:text-gray-900 flex items-center gap-1 py-1.5 px-3 border border-gray-200 rounded-lg shadow-sm bg-white hover:bg-gray-50 transition-colors">
            View all cases
            <ChevronRight className="w-4 h-4" />
          </Link>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="text-xs text-gray-500 bg-gray-50 uppercase border-b border-gray-200">
              <tr>
                <th className="px-6 py-3 font-medium">Customer ID</th>
                <th className="px-6 py-3 font-medium">Risk</th>
                <th className="px-6 py-3 font-medium">Strategy</th>
                <th className="px-6 py-3 font-medium">Channel</th>
                <th className="px-6 py-3 font-medium">Follow-up</th>
                <th className="px-6 py-3 font-medium">Status</th>
                <th className="px-6 py-3 font-medium">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 bg-white">
              {recentCases.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-8 text-center text-gray-500">
                    No recovery cases generated yet.
                  </td>
                </tr>
              ) : recentCases.map((caseItem) => (
                <tr key={caseItem.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4">
                    <div className="font-bold text-gray-900">{caseItem.customer_id}</div>
                    {caseItem.nickname && <div className="text-xs text-gray-500 mt-0.5">{caseItem.nickname}</div>}
                  </td>
                  <td className="px-6 py-4">
                    <RiskBadge risk={caseItem.risk_level} />
                  </td>
                  <td className="px-6 py-4 text-gray-700">{caseItem.strategy.replace('_', ' ')}</td>
                  <td className="px-6 py-4 text-gray-700">{caseItem.communication_channel}</td>
                  <td className="px-6 py-4 text-gray-700">{caseItem.follow_up_days} days</td>
                  <td className="px-6 py-4">
                    <span className={clsx(
                      "px-2.5 py-1 rounded-full text-xs font-medium border",
                      caseItem.status === 'Proactive' && "bg-blue-50 text-blue-700 border-blue-200",
                      caseItem.status === 'Escalated' && "bg-amber-50 text-amber-700 border-amber-200",
                      caseItem.status === 'Pending' && "bg-gray-100 text-gray-700 border-gray-200"
                    )}>
                      {caseItem.status}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <Link to={`/cases/${caseItem.id}`} className="text-indigo-600 font-medium hover:text-indigo-800">
                      View
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
