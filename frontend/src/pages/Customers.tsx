import { useState, useEffect } from 'react';
import { Search, MoreHorizontal, X } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import clsx from 'clsx';
import { formatINR } from '../utils/formatters';
import { getCustomers } from '../services/api';
import { CustomerListItem } from '../types';

export default function Customers() {
  const [search, setSearch] = useState('');
  const [customers, setCustomers] = useState<CustomerListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    async function loadCustomers() {
      try {
        setLoading(true);
        const data = await getCustomers(search);
        setCustomers(data);
      } catch (err) {
        console.error("Unable to load customers.", err);
      } finally {
        setLoading(false);
      }
    }
    const delayDebounceFn = setTimeout(() => {
      loadCustomers();
    }, 300);
    return () => clearTimeout(delayDebounceFn);
  }, [search]);

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Customers</h1>
          <p className="text-gray-500 text-sm mt-1">Manage and monitor your customer portfolio.</p>
        </div>
      </div>

      <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm flex items-center gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input 
            type="text" 
            placeholder="Search customers by ID..." 
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
      </div>

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="text-xs text-gray-500 bg-gray-50 uppercase border-b border-gray-200">
              <tr>
                <th className="px-6 py-4 font-medium">Customer ID</th>
                <th className="px-6 py-4 font-medium">Credit Limit</th>
                <th className="px-6 py-4 font-medium">Latest Risk Status</th>
                <th className="px-6 py-4 font-medium">Latest Account Status</th>
                <th className="px-6 py-4 font-medium">Last Updated</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 bg-white">
              {loading ? (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-gray-500">
                    Loading customers...
                  </td>
                </tr>
              ) : customers.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-gray-500">
                    No customers match your search.
                  </td>
                </tr>
              ) : customers.map((c) => (
                <tr key={c.customer_id} onClick={() => navigate(`/customers/${c.customer_id}`)} className="hover:bg-gray-50 transition-colors cursor-pointer">
                  <td className="px-6 py-4">
                    <div className="font-bold text-gray-900">{c.customer_id}</div>
                    {c.nickname && <div className="text-xs text-gray-500 mt-0.5">{c.nickname}</div>}
                  </td>
                  <td className="px-6 py-4 font-medium text-gray-900">{formatINR(c.credit_limit)}</td>
                  <td className="px-6 py-4">
                    <span className={clsx(
                      "px-2 py-0.5 rounded text-xs font-bold border uppercase",
                      c.risk === 'LOW' && "bg-emerald-50 text-emerald-700 border-emerald-200",
                      c.risk === 'PROACTIVE' && "bg-blue-50 text-blue-700 border-blue-200",
                      c.risk === 'HIGH' && "bg-amber-50 text-amber-700 border-amber-200",
                      c.risk === 'UNKNOWN' && "bg-gray-50 text-gray-700 border-gray-200"
                    )}>{c.risk}</span>
                  </td>
                  <td className="px-6 py-4">
                    <span className={clsx(
                      "px-2.5 py-1 rounded-full text-xs font-medium border",
                      c.status === 'Proactive' && "bg-blue-50 text-blue-700 border-blue-200",
                      c.status === 'Escalated' && "bg-amber-50 text-amber-700 border-amber-200",
                      c.status === 'Pending' && "bg-gray-100 text-gray-700 border-gray-200",
                      c.status === 'Active' && "bg-emerald-50 text-emerald-700 border-emerald-200"
                    )}>
                      {c.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-gray-500">
                    {new Date(c.updated_at).toLocaleString()}
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
