import { useState, useEffect } from 'react';
import { getRecoveryCases } from '../services/api';
import { RecoveryCaseItem } from '../types';
import { Activity as ActivityIcon, CheckCircle, AlertTriangle, ArrowRight, ShieldCheck, Mail, Clock } from 'lucide-react';
import { Link } from 'react-router-dom';
import clsx from 'clsx';

export default function Activity() {
  const [activities, setActivities] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadActivities() {
      try {
        const cases = await getRecoveryCases();
        // Transform cases into a realistic timeline of activity events
        const events = cases.map((c: RecoveryCaseItem) => {
          let actionLabel = 'Analysis Completed';
          let icon = CheckCircle;
          let iconColor = 'text-emerald-500 bg-emerald-100';
          const nick = c.nickname ? ` (${c.nickname})` : '';
          let description = `Automated analysis completed for Customer #${c.customer_id}${nick}. Assigned ${c.strategy.replace('_', ' ')} via ${c.communication_channel}.`;

          if (c.risk_level === 'HIGH') {
             actionLabel = 'High Risk Detected';
             icon = AlertTriangle;
             iconColor = 'text-amber-500 bg-amber-100';
             description = `Customer #${c.customer_id}${nick} flagged as HIGH risk. Escalation candidate review required.`;
          } else if (c.risk_level === 'PROACTIVE') {
             actionLabel = 'Proactive Outreach Triggered';
             icon = ShieldCheck;
             iconColor = 'text-blue-500 bg-blue-100';
             description = `Customer #${c.customer_id}${nick} identified for proactive balance clarification.`;
          }

          return {
            id: c.id,
            caseId: c.id,
            customerId: c.customer_id,
            action: actionLabel,
            description,
            timestamp: new Date(c.created_at),
            icon,
            iconColor
          };
        });
        
        // Add some simulated system events
        events.push({
           id: 999991,
           caseId: 0,
           customerId: 0,
           action: 'Policy Engine Updated',
           description: 'Recovery Policy v3.2 was successfully deployed by System Admin.',
           timestamp: new Date(Date.now() - 86400000 * 2),
           icon: ActivityIcon,
           iconColor: 'text-indigo-500 bg-indigo-100'
        });

        // Sort by timestamp descending
        events.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());
        setActivities(events);
      } catch (err) {
        console.error("Unable to load activity.", err);
      } finally {
        setLoading(false);
      }
    }
    loadActivities();
  }, []);

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-20">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">System Activity</h1>
        <p className="text-gray-500 text-sm mt-1">Real-time log of automated actions and recovery events.</p>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
         {loading ? (
           <div className="flex justify-center p-8"><div className="w-8 h-8 rounded-full border-2 border-indigo-200 border-t-indigo-600 animate-spin"></div></div>
         ) : activities.length === 0 ? (
           <div className="text-center py-12">
             <ActivityIcon className="w-12 h-12 text-gray-300 mx-auto mb-3" />
             <h3 className="text-sm font-medium text-gray-900">No activity yet</h3>
             <p className="text-sm text-gray-500 mt-1">Run customer analyses to see activity here.</p>
           </div>
         ) : (
           <div className="relative border-l border-gray-200 ml-3 md:ml-4 space-y-8">
             {activities.map((item, idx) => (
               <div key={item.id} className="relative pl-8 md:pl-10">
                 <div className={clsx("absolute -left-4 w-8 h-8 rounded-full border-4 border-white flex items-center justify-center", item.iconColor)}>
                   <item.icon className="w-3.5 h-3.5" />
                 </div>
                 
                 <div className="bg-gray-50 border border-gray-100 rounded-lg p-4 transition-colors hover:bg-gray-100/50">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-2">
                       <h4 className="text-sm font-bold text-gray-900">{item.action}</h4>
                       <span className="text-xs text-gray-500 flex items-center gap-1">
                          <Clock className="w-3.5 h-3.5" />
                          {item.timestamp.toLocaleString()}
                       </span>
                    </div>
                    <p className="text-sm text-gray-600 leading-relaxed mb-3">{item.description}</p>
                    
                    {item.caseId > 0 && (
                       <div className="flex gap-3">
                          <Link to={`/cases/${item.caseId}`} className="text-xs font-medium text-indigo-600 hover:text-indigo-800 flex items-center gap-1">
                             View Case <ArrowRight className="w-3 h-3" />
                          </Link>
                          <Link to={`/customers/${item.customerId}`} className="text-xs font-medium text-gray-500 hover:text-gray-700 flex items-center gap-1">
                             Customer Profile <ArrowRight className="w-3 h-3" />
                          </Link>
                       </div>
                    )}
                 </div>
               </div>
             ))}
           </div>
         )}
      </div>
    </div>
  );
}
