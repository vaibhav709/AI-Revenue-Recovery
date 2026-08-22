import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getRecoveryCase, completeRecoveryCase } from '../services/api';
import { RecoveryCaseDetailResponse } from '../types';
import clsx from 'clsx';
import { ChevronLeft, FileText, CheckCircle2 } from 'lucide-react';

export default function RecoveryCaseDetail() {
  const { id } = useParams<{ id: string }>();
  const [data, setData] = useState<RecoveryCaseDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('Overview');

  const loadData = async () => {
    try {
      if (id) {
        const result = await getRecoveryCase(parseInt(id));
        setData(result);
      }
    } catch (err) {
      console.error("Unable to load recovery case details", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [id]);

  const handleComplete = async () => {
    if (window.confirm("Are you sure you want to mark this case as completed?")) {
      try {
        await completeRecoveryCase(data!.case.id);
        await loadData(); // refresh case details
      } catch (err) {
        console.error("Failed to mark case as completed", err);
      }
    }
  };

  if (loading) {
     return <div className="p-8 flex justify-center"><div className="w-8 h-8 rounded-full border-2 border-indigo-200 border-t-indigo-600 animate-spin"></div></div>;
  }

  if (!data || !data.case) {
      return <div className="p-8 text-center text-gray-500">Case not found.</div>;
  }

  const { case: caseData, customer } = data;

  const tabs = ['Overview', 'Risk Analysis', 'Recovery Plan', 'Communication'];

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
         <Link to="/cases" className="inline-flex items-center text-sm font-medium text-gray-500 hover:text-gray-900 transition-colors">
           <ChevronLeft className="w-4 h-4 mr-1" />
           Back to Cases
         </Link>
         <span className="text-sm text-gray-400">Updated {new Date(caseData.updated_at).toLocaleString()}</span>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <div className="p-6 border-b border-gray-200 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
           <div>
              <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                 Customer {customer?.customer_id || caseData.customer_id}
                 {customer?.nickname && <span className="text-gray-500 font-medium">({customer.nickname})</span>}
                 <span className={clsx(
                      "px-2.5 py-1 rounded-full text-xs font-bold border uppercase",
                      caseData.risk_level === 'LOW' && "bg-emerald-50 text-emerald-700 border-emerald-200",
                      caseData.risk_level === 'PROACTIVE' && "bg-blue-50 text-blue-700 border-blue-200",
                      caseData.risk_level === 'HIGH' && "bg-amber-50 text-amber-700 border-amber-200"
                    )}>{caseData.risk_level}</span>
              </h1>
              <p className="text-gray-500 text-sm mt-1">Recovery Case #{caseData.id}</p>
           </div>
           <div className="flex items-center gap-3">
              {caseData.status !== 'Completed' && (
                <button 
                  onClick={handleComplete}
                  className="px-4 py-2 bg-emerald-600 text-white rounded-lg text-sm font-medium hover:bg-emerald-700 transition-colors"
                >
                  Mark as Completed
                </button>
              )}
              <Link to={`/customers/${caseData.customer_id}`} className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50">View Customer Profile</Link>
           </div>
        </div>

        <div className="border-b border-gray-200 bg-gray-50 px-6">
          <nav className="flex gap-6">
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

        <div className="p-6">
           {activeTab === 'Overview' && (
              <div className="space-y-6">
                 <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                    <div>
                       <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Status</div>
                       <div className="font-medium text-gray-900">{caseData.status}</div>
                    </div>
                    <div>
                       <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Predicted Failure</div>
                       <div className="font-medium text-gray-900">{caseData.predicted_failure ? 'Yes' : 'No'}</div>
                    </div>
                    <div>
                       <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Failure Probability</div>
                       <div className="font-medium text-gray-900">{(caseData.failure_probability * 100).toFixed(1)}%</div>
                    </div>
                 </div>
              </div>
           )}
           {activeTab === 'Recovery Plan' && (
              <div className="space-y-6">
                 <div className="grid grid-cols-2 gap-6 bg-gray-50 p-6 rounded-lg border border-gray-100">
                    <div>
                       <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Priority</div>
                       <div className="font-medium text-gray-900">{caseData.priority}</div>
                    </div>
                    <div>
                       <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Strategy</div>
                       <div className="font-medium text-gray-900">{caseData.strategy.replace('_', ' ')}</div>
                    </div>
                 </div>
                 
                 <div>
                    <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2"><CheckCircle2 className="w-5 h-5 text-indigo-600"/> Recommended Action</h3>
                    <div className="bg-indigo-50 text-indigo-900 p-4 rounded-lg border border-indigo-100">
                       {caseData.final_action}
                    </div>
                 </div>
              </div>
           )}
           {activeTab === 'Communication' && (
              <div className="space-y-6">
                 <div className="grid grid-cols-3 gap-6 mb-6">
                    <div>
                       <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Channel</div>
                       <div className="font-medium text-gray-900">{caseData.communication_channel}</div>
                    </div>
                    <div>
                       <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Follow up</div>
                       <div className="font-medium text-gray-900">{caseData.follow_up_days} days</div>
                    </div>
                 </div>
                 <div className="border border-gray-200 rounded-lg overflow-hidden">
                    <div className="bg-gray-50 p-3 border-b border-gray-200 flex items-center gap-2 text-sm font-medium text-gray-700">
                       <FileText className="w-4 h-4 text-gray-400" /> Draft Message
                    </div>
                    <div className="p-4 whitespace-pre-wrap text-sm text-gray-700">
                       {caseData.customer_message}
                    </div>
                 </div>
              </div>
           )}
           {activeTab === 'Risk Analysis' && (
              <div>
                 <p className="text-gray-500">Risk outputs have been persisted and apply to this historical record.</p>
              </div>
           )}
        </div>
      </div>
    </div>
  );
}
