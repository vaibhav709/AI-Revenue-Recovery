import { useState, useEffect } from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer,
  PieChart, Pie, Cell, LineChart, Line
} from 'recharts';
import { getAnalyticsMetrics, getRecoveryCases } from '../services/api';

export default function Analytics() {
  const [data, setData] = useState<any>(null);
  const [cases, setCases] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [metrics, casesList] = await Promise.all([
           getAnalyticsMetrics(),
           getRecoveryCases()
        ]);
        setData(metrics);
        setCases(casesList);
      } catch (err) {
        console.error("Unable to load analytics.", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  if (loading) {
    return <div className="p-8 flex justify-center"><div className="w-8 h-8 rounded-full border-2 border-indigo-200 border-t-indigo-600 animate-spin"></div></div>;
  }

  // Use real backend data for distributions
  const riskDist = data?.risk_distribution || [];
  const strategyDist = data?.strategy_distribution ? data.strategy_distribution.map((s:any) => ({...s, name: s.name.replace('_', ' ')})) : [];
  
  const totalCases = data?.channel_distribution?.reduce((acc: number, val: any) => acc + val.value, 0) || 0;
  
  const getChannelPercentage = (channel: string) => {
    if (totalCases === 0) return 0;
    const item = data?.channel_distribution?.find((c: any) => c.name === channel);
    return item ? Math.round((item.value / totalCases) * 100) : 0;
  };

  const emailPct = getChannelPercentage('EMAIL');
  const phonePct = getChannelPercentage('PHONE');
  const smsPct = getChannelPercentage('SMS'); 
  const portalPct = getChannelPercentage('PORTAL');

  // Compute time-series data from real cases
  const sortedCases = [...cases].sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime());
  
  const trendsMap = sortedCases.reduce((acc, c) => {
    const dateObj = new Date(c.created_at);
    const date = dateObj.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    
    if (!acc[date]) {
      acc[date] = { name: date, low: 0, risk_proactive: 0, high: 0, high_cases: 0, res_proactive: 0, res_escalated: 0 };
    }
    
    const risk = (c.risk_level || '').toUpperCase();
    if (risk === 'LOW') acc[date].low++;
    else if (risk === 'HIGH') acc[date].high++;
    else acc[date].risk_proactive++;

    if (risk === 'HIGH') acc[date].high_cases++;
    
    const status = (c.status || '').toUpperCase();
    if (status === 'ESCALATED') acc[date].res_escalated++;
    else acc[date].res_proactive++;
    
    return acc;
  }, {} as Record<string, any>);

  const timeSeriesData = Object.values(trendsMap);
  const lineChartData = timeSeriesData.map((d: any) => ({ name: d.name, low: d.low, proactive: d.risk_proactive, high: d.high }));
  const highRiskTrend = timeSeriesData.map((d: any) => ({ name: d.name, cases: d.high_cases }));
  const resolutionPaths = timeSeriesData.map((d: any) => ({ name: d.name, proactive: d.res_proactive, escalated: d.res_escalated }));
  
  const hasEnoughData = timeSeriesData.length >= 2;

  return (
    <div className="max-w-7xl mx-auto space-y-6 pb-12">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Analytics</h1>
        <p className="text-gray-500 text-sm mt-1">Deep insights into your recovery operations.</p>
      </div>

      {/* Financial KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
          <h3 className="text-sm font-medium text-gray-500 mb-1">Total Cases</h3>
          <div className="text-2xl font-bold text-gray-900">{data?.total_cases || 0}</div>
        </div>
        <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
          <h3 className="text-sm font-medium text-gray-500 mb-1">Revenue at Risk</h3>
          <div className="text-2xl font-bold text-gray-900">₹{(data?.total_amount_at_risk || 0).toLocaleString(undefined, {minimumFractionDigits: 0, maximumFractionDigits: 0})}</div>
        </div>
        <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
          <h3 className="text-sm font-medium text-gray-500 mb-1">Revenue Recovered</h3>
          <div className="text-2xl font-bold text-emerald-600">₹{(data?.total_amount_recovered || 0).toLocaleString(undefined, {minimumFractionDigits: 0, maximumFractionDigits: 0})}</div>
        </div>
        <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
          <h3 className="text-sm font-medium text-gray-500 mb-1">Recovery Rate</h3>
          <div className="text-2xl font-bold text-gray-900">{(data?.recovery_rate || 0).toFixed(1)}%</div>
          <p className="text-xs text-gray-500 mt-1">{data?.recovered_cases || 0} cases recovered</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Risk Distribution */}
        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm flex flex-col justify-between">
          <div>
             <h3 className="text-base font-semibold text-gray-900">Risk Distribution</h3>
             <p className="text-sm text-gray-500 mb-6">Current portfolio breakdown</p>
          </div>
          <div className="h-48 relative flex-1">
            {totalCases === 0 ? (
              <div className="h-full flex items-center justify-center text-gray-400">No historical data available</div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={riskDist}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={2}
                    dataKey="value"
                  >
                    {riskDist.map((entry: any, index: number) => {
                      let color = '#e5e7eb';
                      if (entry.name === 'HIGH') color = '#f59e0b';
                      if (entry.name === 'PROACTIVE') color = '#3b82f6';
                      if (entry.name === 'LOW') color = '#10b981';
                      return <Cell key={`cell-${index}`} fill={color} />;
                    })}
                  </Pie>
                  <RechartsTooltip />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>
          <div className="mt-4 space-y-2">
             {riskDist.map((r: any) => {
                let color = 'bg-gray-300';
                if (r.name === 'HIGH') color = 'bg-amber-500';
                if (r.name === 'PROACTIVE') color = 'bg-blue-500';
                if (r.name === 'LOW') color = 'bg-emerald-500';
                return (
                   <div key={r.name} className="flex justify-between text-sm">
                      <div className="flex items-center gap-2"><div className={`w-2.5 h-2.5 rounded-full ${color}`}></div> {r.name.charAt(0) + r.name.slice(1).toLowerCase()}</div>
                      <div className="font-semibold">{Math.round((r.value / totalCases) * 100) || 0}%</div>
                   </div>
                );
             })}
          </div>
        </div>

        {/* Recovery Strategy Distribution */}
        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
          <h3 className="text-base font-semibold text-gray-900">Recovery Strategy Distribution</h3>
          <p className="text-sm text-gray-500 mb-6">Cases by assigned strategy</p>
          <div className="h-64">
            {totalCases === 0 ? (
              <div className="h-full flex items-center justify-center text-gray-400">No historical data available</div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart layout="vertical" data={strategyDist} margin={{ top: 0, right: 30, bottom: 0, left: 40 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} stroke="#f3f4f6" />
                  <XAxis type="number" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#9ca3af' }} />
                  <YAxis dataKey="name" type="category" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#4b5563' }} width={140} />
                  <RechartsTooltip cursor={{ fill: 'transparent' }} />
                  <Bar dataKey="value" fill="#4f46e5" radius={[0, 4, 4, 0]} barSize={24} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Communication Channel */}
        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm flex flex-col">
          <h3 className="text-base font-semibold text-gray-900">Communication Channel</h3>
          <p className="text-sm text-gray-500 mb-6">Channel usage across cases</p>
          <div className="space-y-6 flex-1 flex flex-col justify-center">
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span className="font-medium text-gray-700">Email</span>
                <span className="font-bold text-gray-900">{emailPct}%</span>
              </div>
              <div className="w-full bg-gray-100 rounded-full h-2.5">
                <div className="bg-indigo-600 h-2.5 rounded-full" style={{ width: `${emailPct}%` }}></div>
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span className="font-medium text-gray-700">Phone</span>
                <span className="font-bold text-gray-900">{phonePct}%</span>
              </div>
              <div className="w-full bg-gray-100 rounded-full h-2.5">
                <div className="bg-blue-500 h-2.5 rounded-full" style={{ width: `${phonePct}%` }}></div>
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span className="font-medium text-gray-700">SMS</span>
                <span className="font-bold text-gray-900">{smsPct}%</span>
              </div>
              <div className="w-full bg-gray-100 rounded-full h-2.5">
                <div className="bg-emerald-500 h-2.5 rounded-full" style={{ width: `${smsPct}%` }}></div>
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span className="font-medium text-gray-700">Portal</span>
                <span className="font-bold text-gray-900">{portalPct}%</span>
              </div>
              <div className="w-full bg-gray-100 rounded-full h-2.5">
                <div className="bg-amber-500 h-2.5 rounded-full" style={{ width: `${portalPct}%` }}></div>
              </div>
            </div>
          </div>
        </div>

        {/* Recovery Cases Over Time */}
        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
          <h3 className="text-base font-semibold text-gray-900">Recovery Cases Over Time</h3>
          <p className="text-sm text-gray-500 mb-6">Cases opened by risk level</p>
          <div className="h-64">
            {!hasEnoughData ? (
              <div className="h-full flex items-center justify-center text-gray-400">Not enough data</div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={lineChartData} margin={{ top: 5, right: 20, bottom: 5, left: -20 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
                  <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#6b7280' }} dy={10} />
                  <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#6b7280' }} />
                  <RechartsTooltip />
                  <Line type="monotone" dataKey="low" stroke="#10b981" strokeWidth={2} dot={false} />
                  <Line type="monotone" dataKey="proactive" stroke="#3b82f6" strokeWidth={2} dot={false} />
                  <Line type="monotone" dataKey="high" stroke="#f59e0b" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* High-Risk Customer Trend */}
        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
          <h3 className="text-base font-semibold text-gray-900">High-Risk Customer Trend</h3>
          <p className="text-sm text-gray-500 mb-6">New high-risk cases per period</p>
          <div className="h-64">
            {!hasEnoughData ? (
              <div className="h-full flex items-center justify-center text-gray-400">Not enough data</div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={highRiskTrend} margin={{ top: 5, right: 20, bottom: 5, left: -20 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
                  <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#6b7280' }} dy={10} />
                  <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#6b7280' }} />
                  <RechartsTooltip />
                  <Line type="monotone" dataKey="cases" stroke="#d97706" strokeWidth={2} activeDot={{ r: 6 }} />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Proactive vs. Escalated Recovery */}
        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
          <h3 className="text-base font-semibold text-gray-900">Proactive vs. Escalated Recovery</h3>
          <p className="text-sm text-gray-500 mb-6">Case resolution paths over time</p>
          <div className="h-64">
            {!hasEnoughData ? (
              <div className="h-full flex items-center justify-center text-gray-400">Not enough data</div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={resolutionPaths} margin={{ top: 5, right: 20, bottom: 5, left: -20 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
                  <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#6b7280' }} dy={10} />
                  <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#6b7280' }} />
                  <RechartsTooltip cursor={{fill: '#f3f4f6'}} />
                  <Bar dataKey="proactive" stackId="a" fill="#3b82f6" radius={[0, 0, 0, 0]} barSize={32} />
                  <Bar dataKey="escalated" stackId="a" fill="#ea580c" radius={[4, 4, 0, 0]} barSize={32} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
          <div className="flex justify-center gap-6 mt-4">
             <div className="flex items-center gap-2"><div className="w-3 h-3 rounded-full bg-blue-500"></div><span className="text-sm text-gray-600">Proactive</span></div>
             <div className="flex items-center gap-2"><div className="w-3 h-3 rounded-full bg-orange-600"></div><span className="text-sm text-gray-600">Escalated</span></div>
          </div>
        </div>

      </div>
    </div>
  );
}
