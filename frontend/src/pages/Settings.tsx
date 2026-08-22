import { useState } from 'react';
import { Save, Bell, Shield, Key, Users, Settings as SettingsIcon, CheckCircle2 } from 'lucide-react';
import clsx from 'clsx';

export default function Settings() {
  const [activeTab, setActiveTab] = useState('General');
  const [saved, setSaved] = useState(false);
  
  const [general, setGeneral] = useState({
    companyName: 'Fintech Solutions Inc.',
    adminEmail: 'alex@fintech.com',
    timezone: 'UTC',
    defaultCurrency: 'USD'
  });

  const [policy, setPolicy] = useState({
    autoEscalate: true,
    highRiskThreshold: 0.15,
    proactiveThreshold: 0.05,
    emailEnabled: true,
    smsEnabled: true
  });

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  const tabs = ['General', 'Recovery Policy', 'Notifications', 'API Keys', 'Team'];

  return (
    <div className="max-w-5xl mx-auto space-y-6 pb-20">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Platform Settings</h1>
        <p className="text-gray-500 text-sm mt-1">Configure your recovery policies, team access, and integrations.</p>
      </div>

      <div className="flex flex-col md:flex-row gap-8 items-start">
        {/* Settings Navigation */}
        <div className="w-full md:w-64 shrink-0 flex md:flex-col gap-1 overflow-x-auto pb-2 md:pb-0">
           {tabs.map(tab => (
              <button
                 key={tab}
                 onClick={() => setActiveTab(tab)}
                 className={clsx(
                    "flex items-center px-4 py-2.5 text-sm font-medium rounded-lg transition-colors whitespace-nowrap",
                    activeTab === tab 
                      ? "bg-indigo-50 text-indigo-700" 
                      : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                 )}
              >
                 {tab === 'General' && <SettingsIcon className="w-4 h-4 mr-3 opacity-70" />}
                 {tab === 'Recovery Policy' && <Shield className="w-4 h-4 mr-3 opacity-70" />}
                 {tab === 'Notifications' && <Bell className="w-4 h-4 mr-3 opacity-70" />}
                 {tab === 'API Keys' && <Key className="w-4 h-4 mr-3 opacity-70" />}
                 {tab === 'Team' && <Users className="w-4 h-4 mr-3 opacity-70" />}
                 {tab}
              </button>
           ))}
        </div>

        {/* Settings Content */}
        <div className="flex-1 w-full bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
           <form onSubmit={handleSave}>
             <div className="p-6 md:p-8">
                
                {activeTab === 'General' && (
                   <div className="space-y-6 max-w-2xl">
                      <h2 className="text-lg font-bold text-gray-900 mb-4">General Settings</h2>
                      
                      <div>
                         <label className="block text-sm font-medium text-gray-700 mb-1">Company Name</label>
                         <input type="text" value={general.companyName} onChange={e => setGeneral({...general, companyName: e.target.value})} className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500" />
                      </div>
                      
                      <div>
                         <label className="block text-sm font-medium text-gray-700 mb-1">Admin Email Address</label>
                         <input type="email" value={general.adminEmail} onChange={e => setGeneral({...general, adminEmail: e.target.value})} className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500" />
                      </div>

                      <div className="grid grid-cols-2 gap-6">
                         <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Timezone</label>
                            <select value={general.timezone} onChange={e => setGeneral({...general, timezone: e.target.value})} className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500">
                               <option>UTC</option>
                               <option>America/New_York</option>
                               <option>America/Los_Angeles</option>
                               <option>Europe/London</option>
                            </select>
                         </div>
                         <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Default Currency</label>
                            <select value={general.defaultCurrency} onChange={e => setGeneral({...general, defaultCurrency: e.target.value})} className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500">
                               <option>USD</option>
                               <option>EUR</option>
                               <option>GBP</option>
                            </select>
                         </div>
                      </div>
                   </div>
                )}

                {activeTab === 'Recovery Policy' && (
                   <div className="space-y-6 max-w-2xl">
                      <h2 className="text-lg font-bold text-gray-900 mb-4">Recovery Policy Engine</h2>
                      <p className="text-sm text-gray-500 mb-6">Configure the deterministic rules that map ML predictions to recovery strategies.</p>

                      <div className="border-b border-gray-200 pb-6 mb-6">
                         <label className="flex items-center gap-3">
                            <input type="checkbox" checked={policy.autoEscalate} onChange={e => setPolicy({...policy, autoEscalate: e.target.checked})} className="w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500" />
                            <div>
                               <div className="text-sm font-medium text-gray-900">Auto-Escalation</div>
                               <div className="text-xs text-gray-500">Automatically flag high-risk accounts for manual review.</div>
                            </div>
                         </label>
                      </div>

                      <div className="grid grid-cols-2 gap-6">
                         <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">High Risk Threshold (Prob &gt; X)</label>
                            <input type="number" step="0.01" value={policy.highRiskThreshold} onChange={e => setPolicy({...policy, highRiskThreshold: Number(e.target.value)})} className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500" />
                         </div>
                         <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Proactive Threshold (Prob &gt; X)</label>
                            <input type="number" step="0.01" value={policy.proactiveThreshold} onChange={e => setPolicy({...policy, proactiveThreshold: Number(e.target.value)})} className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500" />
                         </div>
                      </div>

                      <div className="pt-6 border-t border-gray-200">
                         <h3 className="text-sm font-semibold text-gray-900 mb-4">Allowed Communication Channels</h3>
                         <div className="space-y-3">
                            <label className="flex items-center gap-3">
                               <input type="checkbox" checked={policy.emailEnabled} onChange={e => setPolicy({...policy, emailEnabled: e.target.checked})} className="w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500" />
                               <span className="text-sm text-gray-700">Email Drafts (AI Assistant)</span>
                            </label>
                            <label className="flex items-center gap-3">
                               <input type="checkbox" checked={policy.smsEnabled} onChange={e => setPolicy({...policy, smsEnabled: e.target.checked})} className="w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500" />
                               <span className="text-sm text-gray-700">SMS Reminders</span>
                            </label>
                         </div>
                      </div>
                   </div>
                )}

                {(activeTab === 'Notifications' || activeTab === 'API Keys' || activeTab === 'Team') && (
                   <div className="text-center py-12">
                      <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-indigo-50 text-indigo-600 mb-4">
                         {activeTab === 'Notifications' && <Bell className="w-8 h-8" />}
                         {activeTab === 'API Keys' && <Key className="w-8 h-8" />}
                         {activeTab === 'Team' && <Users className="w-8 h-8" />}
                      </div>
                      <h3 className="text-lg font-bold text-gray-900 mb-2">{activeTab} Settings</h3>
                      <p className="text-gray-500 text-sm max-w-sm mx-auto">This section is currently managed by external identity and notification providers. Configuration is read-only in the demo environment.</p>
                   </div>
                )}

             </div>
             
             {/* Save Footer */}
             {(activeTab === 'General' || activeTab === 'Recovery Policy') && (
                <div className="px-6 md:px-8 py-4 bg-gray-50 border-t border-gray-200 flex items-center justify-end gap-4">
                   {saved && <span className="text-emerald-600 text-sm font-medium flex items-center gap-1"><CheckCircle2 className="w-4 h-4" /> Settings saved</span>}
                   <button type="submit" className="px-6 py-2 bg-indigo-600 text-white rounded-lg shadow-sm text-sm font-medium hover:bg-indigo-700 focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 flex items-center gap-2 transition-colors">
                      <Save className="w-4 h-4" /> Save Changes
                   </button>
                </div>
             )}
           </form>
        </div>
      </div>
    </div>
  );
}
