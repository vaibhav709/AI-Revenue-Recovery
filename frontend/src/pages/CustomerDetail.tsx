import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { formatINR } from '../utils/formatters';
import { getCustomer } from '../services/api';
import { CustomerDetailResponse } from '../types';
import clsx from 'clsx';
import { ChevronLeft } from 'lucide-react';

export default function CustomerDetail() {
  const { id } = useParams<{ id: string }>();
  const [data, setData] = useState<CustomerDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        if (id) {
          const result = await getCustomer(parseInt(id));
          setData(result);
        }
      } catch (err) {
        console.error("Unable to load customer details", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [id]);

  if (loading) {
     return <div className="p-8 flex justify-center"><div className="w-8 h-8 rounded-full border-2 border-indigo-200 border-t-indigo-600 animate-spin"></div></div>;
  }

  if (!data || !data.customer) {
      return <div className="p-8 text-center text-gray-500">Customer not found.</div>;
  }

  const { customer, latest_case, history } = data;

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <Link to="/customers" className="inline-flex items-center text-sm font-medium text-gray-500 hover:text-gray-900 transition-colors">
        <ChevronLeft className="w-4 h-4 mr-1" />
        Back to Customers
      </Link>
      
      <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm flex justify-between items-start">
        <div>
           <h1 className="text-2xl font-bold text-gray-900">Customer {customer.customer_id} {customer.nickname && <span className="text-gray-500 font-medium">({customer.nickname})</span>}</h1>
           <p className="text-gray-500 text-sm mt-1">Last analyzed: {customer.updated_at ? new Date(customer.updated_at).toLocaleString() : 'Never'}</p>
        </div>
        <div className="text-right">
           <div className="text-sm text-gray-500 mb-1">Credit Limit</div>
           <div className="text-xl font-bold text-gray-900">{formatINR(customer.credit_limit)}</div>
        </div>
      </div>

      {latest_case && (
        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Latest Analysis Overview</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
             <div>
                <div className="text-xs text-gray-500 uppercase font-semibold mb-1">Risk Level</div>
                <span className={clsx(
                      "px-2 py-0.5 rounded text-xs font-bold border",
                      latest_case.risk_level === 'LOW' && "bg-emerald-50 text-emerald-700 border-emerald-200",
                      latest_case.risk_level === 'PROACTIVE' && "bg-blue-50 text-blue-700 border-blue-200",
                      latest_case.risk_level === 'HIGH' && "bg-amber-50 text-amber-700 border-amber-200"
                    )}>{latest_case.risk_level}</span>
             </div>
             <div>
                <div className="text-xs text-gray-500 uppercase font-semibold mb-1">Priority</div>
                <div className="font-medium text-gray-900">{latest_case.priority}</div>
             </div>
             <div>
                <div className="text-xs text-gray-500 uppercase font-semibold mb-1">Strategy</div>
                <div className="font-medium text-gray-900">{latest_case.strategy.replace('_', ' ')}</div>
             </div>
             <div>
                <div className="text-xs text-gray-500 uppercase font-semibold mb-1">Channel</div>
                <div className="font-medium text-gray-900">{latest_case.communication_channel}</div>
             </div>
          </div>
        </div>
      )}

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <div className="p-4 border-b border-gray-200">
           <h2 className="text-base font-semibold text-gray-900">Analysis History</h2>
        </div>
        <table className="w-full text-sm text-left">
            <thead className="text-xs text-gray-500 bg-gray-50 uppercase border-b border-gray-200">
              <tr>
                <th className="px-6 py-4 font-medium">Date</th>
                <th className="px-6 py-4 font-medium">Risk</th>
                <th className="px-6 py-4 font-medium">Strategy</th>
                <th className="px-6 py-4 font-medium">Status</th>
                <th className="px-6 py-4 font-medium">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 bg-white">
              {history.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-gray-500">
                    No history found.
                  </td>
                </tr>
              ) : history.map((caseItem) => (
                <tr key={caseItem.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4 text-gray-900">{new Date(caseItem.created_at).toLocaleString()}</td>
                  <td className="px-6 py-4 font-bold">{caseItem.risk_level}</td>
                  <td className="px-6 py-4 text-gray-700">{caseItem.strategy.replace('_', ' ')}</td>
                  <td className="px-6 py-4">{caseItem.status}</td>
                  <td className="px-6 py-4">
                    <Link to={`/cases/${caseItem.id}`} className="text-indigo-600 font-medium hover:text-indigo-800">
                      View Case
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
      </div>
    </div>
  );
}
