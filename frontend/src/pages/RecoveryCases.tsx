import { useState, useEffect } from 'react';
import { Search, Filter, MoreHorizontal, AlertCircle, X } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import clsx from 'clsx';
import { getRecoveryCases } from '../services/api';
import { RecoveryCaseItem } from '../types';

export default function RecoveryCases() {
  const [search, setSearch] = useState('');
  const [riskFilter, setRiskFilter] = useState('All');
  const [statusFilter, setStatusFilter] = useState('All');
  const [channelFilter, setChannelFilter] = useState('All');
  const [strategyFilter, setStrategyFilter] = useState('All');
  
  const [cases, setCases] = useState<RecoveryCaseItem[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    async function loadCases() {
      try {
        setLoading(true);
        const data = await getRecoveryCases({
          search, risk: riskFilter, status: statusFilter, channel: channelFilter, strategy: strategyFilter
        });
        setCases(data);
      } catch (err) {
        console.error("Unable to load recovery cases.", err);
      } finally {
        setLoading(false);
      }
    }
    const delayDebounceFn = setTimeout(() => {
      loadCases();
    }, 300);
    return () => clearTimeout(delayDebounceFn);
  }, [search, riskFilter, statusFilter, channelFilter, strategyFilter]);

  const hasActiveFilters = riskFilter !== 'All' || statusFilter !== 'All' || channelFilter !== 'All' || strategyFilter !== 'All' || search !== '';

  const clearFilters = () => {
    setSearch('');
    setRiskFilter('All');
    setStatusFilter('All');
    setChannelFilter('All');
    setStrategyFilter('All');
  };

  const FilterDropdown = ({ label, value, options, onChange }: any) => {
    const [isOpen, setIsOpen] = useState(false);
    return (
      <div className="relative">
        <button 
          onClick={() => setIsOpen(!isOpen)}
          className={clsx(
            "flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium border transition-colors",
            value !== 'All' 
              ? "bg-indigo-50 border-indigo-200 text-indigo-700" 
              : "bg-white border-gray-200 text-gray-700 hover:bg-gray-50"
          )}
        >
          {label}: {value}
        </button>
        {isOpen && (
          <div className="absolute top-full mt-1 left-0 w-48 bg-white border border-gray-200 rounded-lg shadow-lg py-1 z-10">
            <button 
              onClick={() => { onChange('All'); setIsOpen(false); }}
              className={clsx(
                "w-full text-left px-4 py-2 text-sm",
                value === 'All' ? "bg-indigo-50 text-indigo-700 font-medium" : "text-gray-700 hover:bg-gray-50"
              )}
            >
              All
            </button>
            {options.map((opt: string) => (
              <button 
                key={opt}
                onClick={() => { onChange(opt); setIsOpen(false); }}
                className={clsx(
                  "w-full text-left px-4 py-2 text-sm",
                  value === opt ? "bg-indigo-50 text-indigo-700 font-medium" : "text-gray-700 hover:bg-gray-50"
                )}
              >
                {opt}
              </button>
            ))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Recovery Cases</h1>
          <p className="text-gray-500 text-sm mt-1">Manage and track active recovery workflows.</p>
        </div>
        <Link to="/analyze" className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-lg shadow-sm">
          New Analysis
        </Link>
      </div>

      <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm flex flex-col sm:flex-row items-center gap-4">
        <div className="relative flex-1 w-full">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input 
            type="text" 
            placeholder="Search cases by customer ID..." 
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-8 py-2 bg-gray-50 border border-gray-200 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
          {search && (
            <button 
              onClick={() => setSearch('')}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
        <div className="flex items-center gap-3 flex-wrap w-full sm:w-auto z-10">
          <Filter className="w-4 h-4 text-gray-400 hidden sm:block" />
          <FilterDropdown label="Risk" value={riskFilter} options={['LOW', 'PROACTIVE', 'HIGH']} onChange={setRiskFilter} />
          <FilterDropdown label="Status" value={statusFilter} options={['Proactive', 'Escalated', 'Pending', 'Completed']} onChange={setStatusFilter} />
          <FilterDropdown label="Channel" value={channelFilter} options={['EMAIL', 'SMS', 'PHONE']} onChange={setChannelFilter} />
          <FilterDropdown label="Strategy" value={strategyFilter} options={['BALANCE_CLARIFICATION', 'ESCALATED_RECOVERY']} onChange={setStrategyFilter} />
          
          {hasActiveFilters && (
            <button 
              onClick={clearFilters}
              className="text-sm text-gray-500 hover:text-gray-700 font-medium whitespace-nowrap px-2"
            >
              Clear filters
            </button>
          )}
        </div>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="text-xs text-gray-500 bg-gray-50 uppercase border-b border-gray-200">
              <tr>
                <th className="px-6 py-4 font-medium">Customer ID</th>
                <th className="px-6 py-4 font-medium">Risk</th>
                <th className="px-6 py-4 font-medium">Strategy</th>
                <th className="px-6 py-4 font-medium">Channel</th>
                <th className="px-6 py-4 font-medium">Status</th>
                <th className="px-6 py-4 font-medium">Date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 bg-white">
              {loading ? (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-gray-500">
                    Loading cases...
                  </td>
                </tr>
              ) : cases.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center flex flex-col items-center">
                    <AlertCircle className="w-8 h-8 text-gray-400 mb-2" />
                    <span className="text-gray-500 font-medium">No recovery cases found.</span>
                    {hasActiveFilters && <span className="text-gray-400 text-sm mt-1">Try adjusting your filters.</span>}
                  </td>
                </tr>
              ) : cases.map((c) => (
                <tr key={c.id} onClick={() => navigate(`/cases/${c.id}`)} className="hover:bg-gray-50 transition-colors cursor-pointer">
                  <td className="px-6 py-4">
                    <div className="font-bold text-gray-900">{c.customer_id}</div>
                    {c.nickname && <div className="text-xs text-gray-500 mt-0.5">{c.nickname}</div>}
                  </td>
                  <td className="px-6 py-4">
                    <span className={clsx(
                      "px-2 py-0.5 rounded text-xs font-bold border uppercase",
                      c.risk_level === 'LOW' && "bg-emerald-50 text-emerald-700 border-emerald-200",
                      c.risk_level === 'PROACTIVE' && "bg-blue-50 text-blue-700 border-blue-200",
                      c.risk_level === 'HIGH' && "bg-amber-50 text-amber-700 border-amber-200"
                    )}>{c.risk_level}</span>
                  </td>
                  <td className="px-6 py-4 text-gray-700">{c.strategy.replace('_', ' ')}</td>
                  <td className="px-6 py-4 text-gray-700">{c.communication_channel}</td>
                  <td className="px-6 py-4">
                    <span className={clsx(
                      "px-2.5 py-1 rounded-full text-xs font-medium border",
                      c.status === 'Proactive' && "bg-blue-50 text-blue-700 border-blue-200",
                      c.status === 'Escalated' && "bg-amber-50 text-amber-700 border-amber-200",
                      c.status === 'Pending' && "bg-gray-100 text-gray-700 border-gray-200",
                      c.status === 'Completed' && "bg-emerald-50 text-emerald-700 border-emerald-200"
                    )}>
                      {c.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-gray-500">
                    {new Date(c.created_at).toLocaleDateString()}
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
