import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getRecoveryCase, completeRecoveryCase, updateRecoveryOutcome, recordRecoveryAttempt, generateAiAction } from '../services/api';
import { RecoveryCaseDetailResponse } from '../types';
import clsx from 'clsx';
import { ChevronLeft, FileText, CheckCircle2 } from 'lucide-react';

export default function RecoveryCaseDetail() {
  const { id } = useParams<{ id: string }>();
  const [data, setData] = useState<RecoveryCaseDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('Overview');
  const [outcomeForm, setOutcomeForm] = useState({ amount_recovered: 0, recovery_status: 'Pending' });
  const [isUpdatingOutcome, setIsUpdatingOutcome] = useState(false);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [confirmMessage, setConfirmMessage] = useState<string | React.ReactNode>("");
  const [isGeneratingAi, setIsGeneratingAi] = useState(false);
  const [aiError, setAiError] = useState<string | null>(null);

  const loadData = async () => {
    try {
      if (id) {
        const result = await getRecoveryCase(parseInt(id));
        setData(result);
        setOutcomeForm({ 
          amount_recovered: result.case.amount_recovered || 0, 
          recovery_status: result.case.recovery_status || 'Pending' 
        });
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

  const handleUpdateOutcome = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsUpdatingOutcome(true);
    try {
      await updateRecoveryOutcome(data!.case.id, outcomeForm);
      await loadData();
    } catch (err) {
      console.error("Failed to update outcome", err);
    } finally {
      setIsUpdatingOutcome(false);
    }
  };

  const handleGenerateAiAction = async () => {
    setIsGeneratingAi(true);
    setAiError(null);
    try {
      await generateAiAction(data!.case.id);
      await loadData();
    } catch (err: any) {
      console.error("Failed to generate AI action", err);
      setAiError(err.response?.data?.detail || "Unable to generate AI recommendation. Please try again.");
    } finally {
      setIsGeneratingAi(false);
    }
  };

  const handleRecordAttempt = async () => {
    try {
      await recordRecoveryAttempt(data!.case.id);
      await loadData();
    } catch (err) {
      console.error("Failed to record attempt", err);
    }
  };

  const executeCompletion = async () => {
    try {
      await completeRecoveryCase(data!.case.id);
      await loadData(); // refresh case details
    } catch (err) {
      console.error("Failed to mark case as completed", err);
    }
  };

  const handleCompleteClick = () => {
    const atRisk = caseData.amount_at_risk || 0;
    const recovered = caseData.amount_recovered || 0;
    const diff = atRisk - recovered;

    if (Math.abs(diff) < 0.01) {
      executeCompletion();
    } else if (recovered === 0) {
      setConfirmMessage("No recovery amount has been recorded.\nAre you sure you want to mark this recovery case as completed?");
      setShowConfirmModal(true);
    } else {
      setConfirmMessage(
        <>
          Amount not fully recovered.<br />
          <span className="font-semibold text-gray-900">₹{diff.toLocaleString()}</span> is still outstanding. Are you sure you want to mark this recovery case as completed?
        </>
      );
      setShowConfirmModal(true);
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

  let outcomeError = null;
  if (outcomeForm.amount_recovered < 0) {
    outcomeError = "Error: Recovered amount cannot be negative.";
  } else if (outcomeForm.amount_recovered > (caseData.amount_at_risk || 0)) {
    outcomeError = `Error: Recovered amount cannot be greater than the amount at risk (₹${(caseData.amount_at_risk || 0).toLocaleString()}).`;
  }

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
                  onClick={handleCompleteClick}
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
                 
                 <div className="mt-8 border-t border-gray-200 pt-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Financial Outcome</h3>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                       <div className="space-y-4">
                          <div className="flex justify-between items-center py-2 border-b border-gray-100">
                             <span className="text-gray-600">Amount at Risk:</span>
                             <span className="font-semibold text-gray-900">₹{(caseData.amount_at_risk || 0).toLocaleString()}</span>
                          </div>
                          <div className="flex justify-between items-center py-2 border-b border-gray-100">
                             <span className="text-gray-600">Amount Recovered:</span>
                             <span className="font-semibold text-gray-900">₹{(caseData.amount_recovered || 0).toLocaleString()}</span>
                          </div>
                          <div className="flex justify-between items-center py-2 border-b border-gray-100">
                             <span className="text-gray-600">Recovery Status:</span>
                             <span className="font-semibold text-gray-900">{caseData.recovery_status}</span>
                          </div>
                       </div>
                       
                       <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                          <h4 className="text-sm font-medium text-gray-900 mb-3">Update Outcome</h4>
                          <form onSubmit={handleUpdateOutcome} className="space-y-4">
                             <div>
                                <label className="block text-xs font-medium text-gray-700 mb-1">Recovered Amount (₹)</label>
                                <input 
                                  type="number" 
                                  value={outcomeForm.amount_recovered}
                                  onChange={(e) => setOutcomeForm({...outcomeForm, amount_recovered: Number(e.target.value)})}
                                  className={clsx(
                                    "w-full px-3 py-2 border rounded-md text-sm",
                                    outcomeError 
                                      ? "border-red-500 text-red-900 focus:ring-red-500 focus:border-red-500 bg-red-50" 
                                      : "border-gray-300 focus:ring-indigo-500 focus:border-indigo-500"
                                  )}
                                  required
                                />
                                {outcomeError && (
                                  <p className="mt-1 text-xs text-red-600">{outcomeError}</p>
                                )}
                             </div>
                             <div>
                                <label className="block text-xs font-medium text-gray-700 mb-1">Recovery Status</label>
                                <select 
                                  value={outcomeForm.recovery_status}
                                  onChange={(e) => setOutcomeForm({...outcomeForm, recovery_status: e.target.value})}
                                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                                >
                                  <option value="Pending">Pending</option>
                                  <option value="In Progress">In Progress</option>
                                  <option value="Recovered">Recovered</option>
                                  <option value="Partially Recovered">Partially Recovered</option>
                                  <option value="Failed">Failed</option>
                                </select>
                             </div>
                             <button 
                               type="submit" 
                               disabled={isUpdatingOutcome || !!outcomeError}
                               className={clsx(
                                 "w-full px-4 py-2 text-white rounded-md text-sm font-medium transition-colors",
                                 (isUpdatingOutcome || !!outcomeError) ? "bg-indigo-400 cursor-not-allowed" : "bg-indigo-600 hover:bg-indigo-700"
                               )}
                             >
                               {isUpdatingOutcome ? 'Updating...' : 'Save Outcome'}
                             </button>
                          </form>
                       </div>
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
                    <div className="flex items-center justify-between mb-3">
                       <h3 className="font-semibold text-gray-900 flex items-center gap-2"><CheckCircle2 className="w-5 h-5 text-indigo-600"/> AI Recommended Action</h3>
                       {!caseData.ai_recommended_action && (
                          <button 
                             onClick={handleGenerateAiAction} 
                             disabled={isGeneratingAi}
                             className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-medium rounded-md transition-colors disabled:opacity-50"
                          >
                             {isGeneratingAi ? 'Analyzing recovery case...' : 'Generate AI Recommendation'}
                          </button>
                       )}
                       {caseData.ai_recommended_action && (
                          <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-semibold rounded">
                             Generated
                          </span>
                       )}
                    </div>
                    
                    {aiError && (
                       <div className="mb-4 p-3 bg-red-50 text-red-700 border border-red-200 rounded-md text-sm">
                          {aiError}
                       </div>
                    )}
                    
                    {caseData.ai_recommended_action ? (
                       <div className="bg-indigo-50 text-indigo-900 p-5 rounded-lg border border-indigo-100 space-y-4">
                          <div>
                             <div className="text-lg font-medium">{caseData.ai_recommended_action}</div>
                          </div>
                          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-4 border-t border-indigo-200/60">
                             <div className="sm:col-span-3">
                                <div className="text-xs font-semibold text-indigo-800/70 uppercase tracking-wider mb-1">Why this action?</div>
                                <div className="text-sm">{caseData.ai_reasoning}</div>
                             </div>
                             <div>
                                <div className="text-xs font-semibold text-indigo-800/70 uppercase tracking-wider mb-1">Decision</div>
                                <div className="text-sm font-bold">{caseData.ai_decision}</div>
                             </div>
                             <div>
                                <div className="text-xs font-semibold text-indigo-800/70 uppercase tracking-wider mb-1">Confidence</div>
                                <div className="text-sm font-bold">{Math.round((caseData.ai_confidence || 0) * 100)}%</div>
                             </div>
                          </div>
                       </div>
                    ) : (
                       <div className="bg-gray-50 text-gray-500 p-5 rounded-lg border border-gray-200 italic text-sm text-center">
                          {isGeneratingAi ? 'Analyzing recovery case...' : 'No AI recommendation generated yet. Click the button above to generate.'}
                       </div>
                    )}
                    
                    {caseData.ai_recommended_action && (
                       <div className="mt-2 text-xs text-gray-400 flex items-center justify-end">
                          AI recommendation generated using GPT-5.6 Luna.
                       </div>
                    )}
                 </div>
                 
                 <div className="mt-8 border-t border-gray-200 pt-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Recovery Progress</h3>
                    
                    {(() => {
                       const atRisk = caseData.amount_at_risk || 0;
                       const recovered = caseData.amount_recovered || 0;
                       const diff = Math.max(0, atRisk - recovered);
                       const isFullyRecovered = recovered >= atRisk;
                       const isEscalated = caseData.status === 'Escalated' || caseData.recovery_status === 'Escalated';
                       const isCompleted = caseData.status === 'Completed';
                       const maxAttempts = caseData.max_attempts || 5;
                       const attemptCount = caseData.attempt_count || 0;
                       const progressPercentage = atRisk > 0 ? Math.min(100, Math.round((recovered / atRisk) * 100)) : 0;
                       
                       let nextAction = "Recovery Attempt Allowed";
                       let canAttempt = true;
                       let alertStatus = null;
                       
                       if (isFullyRecovered) {
                         nextAction = "Stop (Fully Recovered)";
                         canAttempt = false;
                         alertStatus = 'RECOVERED';
                       } else if (isCompleted) {
                         nextAction = "Stop (Case Completed)";
                         canAttempt = false;
                       } else if (isEscalated || attemptCount >= maxAttempts) {
                         nextAction = "Stop (Escalated)";
                         canAttempt = false;
                         alertStatus = 'ESCALATED';
                       }
                       
                       return (
                         <div className="space-y-6">
                           {alertStatus === 'RECOVERED' && (
                             <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-4">
                               <div className="flex items-center gap-2 mb-1">
                                 <span className="text-emerald-700 font-bold">✓ Recovery Target Reached</span>
                               </div>
                               <p className="text-sm text-emerald-600">Full recovery achieved. Further recovery attempts have been stopped.</p>
                             </div>
                           )}
                           
                           {alertStatus === 'ESCALATED' && (
                             <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                               <div className="flex items-center gap-2 mb-1">
                                 <span className="text-red-700 font-bold">⚠ Recovery Escalated</span>
                               </div>
                               <p className="text-sm text-red-600 mb-1">Maximum automated recovery attempts reached. Further recovery attempts have been stopped.</p>
                               <p className="text-sm text-red-700 font-medium">Reason: {caseData.escalation_reason || "Maximum recovery attempts reached without full recovery."}</p>
                             </div>
                           )}
                           
                           <div className="grid grid-cols-1 md:grid-cols-4 gap-6 bg-gray-50 p-6 rounded-lg border border-gray-100">
                             <div>
                               <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Recovery Attempts</div>
                               <div className="font-medium text-gray-900">{attemptCount} / {maxAttempts}</div>
                             </div>
                             <div>
                               <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Amount at Risk</div>
                               <div className="font-medium text-gray-900">₹{atRisk.toLocaleString()}</div>
                             </div>
                             <div>
                               <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Amount Recovered</div>
                               <div className="font-medium text-emerald-600">₹{recovered.toLocaleString()}</div>
                             </div>
                             <div>
                               <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Remaining</div>
                               <div className="font-medium text-red-600">₹{diff.toLocaleString()}</div>
                             </div>
                           </div>
                           
                                                      <div className="mb-2">
                             <div className="flex justify-between text-xs mb-2">
                               <span className="font-medium text-gray-500">Financial Progress</span>
                               <span className="font-medium text-gray-900">{progressPercentage}%</span>
                             </div>
                             <div className="w-full bg-gray-200 rounded-full h-2.5">
                               <div className="bg-emerald-500 h-2.5 rounded-full" style={{ width: `${progressPercentage}%` }}></div>
                             </div>
                           </div>
                           
                           <div className="flex items-center justify-between border-t border-gray-100 pt-6 pb-2">
                             <div>
                               <span className="text-gray-600 text-sm font-medium mr-2">Next Action:</span>
                               <span className="text-gray-900 text-sm">{nextAction}</span>
                             </div>
                             {canAttempt && (
                               <button 
                                 onClick={handleRecordAttempt}
                                 className="px-4 py-2 bg-indigo-600 text-white rounded-md text-sm font-medium hover:bg-indigo-700 transition-colors"
                               >
                                 Record Recovery Attempt
                               </button>
                             )}
                           </div>
                         </div>
                       );
                    })()}
                 </div>


              </div>
           )}
           {activeTab === 'Communication' && (
      <div className="space-y-6">
         <div className="mb-4 flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">Communication</h2>
              <p className="text-sm text-gray-500">
                 {caseData.ai_customer_message ? "AI-generated recovery communication" : "Recommended communication draft"}
              </p>
            </div>
         </div>

         {caseData.ai_customer_message ? (
           <>
             <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
                   <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Channel</div>
                   <div className="font-medium text-gray-900">{caseData.ai_communication_channel || caseData.communication_channel}</div>
                </div>
                <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
                   <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Follow up</div>
                   <div className="font-medium text-gray-900">{caseData.ai_follow_up_days || caseData.follow_up_days} days</div>
                </div>
                <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
                   <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Decision</div>
                   <div className="font-medium text-indigo-700">{caseData.ai_decision}</div>
                </div>
                <div className="bg-indigo-50 p-4 rounded-lg border border-indigo-100 shadow-sm">
                   <div className="text-xs font-semibold text-indigo-800/70 uppercase tracking-wider mb-1">Status</div>
                   <div className="font-medium text-indigo-900">Draft — Not Sent</div>
                </div>
             </div>

             <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
                <div className="bg-gray-50 px-6 py-4 border-b border-gray-200 flex justify-between items-center">
                   <div className="font-medium text-gray-700 flex items-center gap-2">
                     <FileText className="w-4 h-4 text-gray-500"/>
                     {caseData.ai_communication_channel || caseData.communication_channel}
                   </div>
                   <span className="text-xs font-medium text-gray-500 bg-white px-2 py-1 rounded border border-gray-200 shadow-sm">
                     DRAFT — NOT SENT
                   </span>
                </div>
                
                <div className="p-8">
                   <div className="mb-6 pb-6 border-b border-gray-100">
                     <div className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-2">Subject</div>
                     <div className="text-lg font-medium text-gray-900">Action required regarding your account</div>
                   </div>
                   
                   <div>
                     <div className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-4">Message</div>
                     <div className="text-gray-800 whitespace-pre-wrap leading-relaxed">
                        {caseData.ai_customer_message}
                     </div>
                   </div>
                </div>
                
                <div className="bg-gray-50 px-6 py-3 border-t border-gray-200 flex justify-between items-center text-xs text-gray-500">
                   <span>Generated by GPT-5.6 Luna • Draft — Not Sent</span>
                </div>
             </div>
           </>
         ) : (
           <div className="space-y-6">
             <div className="bg-gray-50 rounded-xl border border-gray-200 p-10 text-center flex flex-col items-center">
                <div className="w-12 h-12 bg-white rounded-full flex items-center justify-center border border-gray-200 shadow-sm mb-4">
                  <FileText className="w-6 h-6 text-gray-400" />
                </div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">No AI communication generated</h3>
                <p className="text-gray-500 max-w-sm mb-6">
                  Generate an AI recommendation in the Recovery Plan tab to create the recommended customer communication.
                </p>
                <button 
                  onClick={() => setActiveTab('Recovery Plan')}
                  className="px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-50 transition-colors shadow-sm"
                >
                  Go to Recovery Plan
                </button>
             </div>
             
             {caseData.customer_message && (
               <div className="mt-8">
                  <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-4">Existing Draft</h3>
                  <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm whitespace-pre-wrap text-gray-700 leading-relaxed text-sm">
                    {caseData.customer_message}
                  </div>
               </div>
             )}
           </div>
         )}
      </div>
    )}
           {activeTab === 'Risk Analysis' && (
              <div>
                 <p className="text-gray-500">Risk outputs have been persisted and apply to this historical record.</p>
              </div>
           )}
        </div>
      </div>

      {showConfirmModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full shadow-xl">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Confirm Completion</h3>
            <p className="text-gray-600 mb-6 whitespace-pre-wrap">{confirmMessage}</p>
            <div className="flex justify-end gap-3">
              <button 
                onClick={() => setShowConfirmModal(false)}
                className="px-4 py-2 text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-md text-sm font-medium transition-colors"
              >
                Cancel
              </button>
              <button 
                onClick={() => {
                  setShowConfirmModal(false);
                  executeCompletion();
                }}
                className="px-4 py-2 bg-emerald-600 text-white hover:bg-emerald-700 rounded-md text-sm font-medium transition-colors"
              >
                Confirm
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
