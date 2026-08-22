import { useState, useRef, useEffect } from 'react';
import { Outlet, NavLink, useLocation, useNavigate } from 'react-router-dom';
import { 
  LayoutDashboard, Search, Briefcase, Users, BarChart3, Clock, Settings, Bell, ChevronDown, Layers
} from 'lucide-react';
import clsx from 'clsx';
import { getCustomers, getRecoveryCases } from '../../services/api';

const navItems = [
  { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
  { name: 'Analyze Customer', path: '/analyze', icon: Search },
  { name: 'Recovery Cases', path: '/cases', icon: Briefcase },
  { name: 'Customers', path: '/customers', icon: Users },
  { name: 'Analytics', path: '/analytics', icon: BarChart3 },
];

const systemItems = [
  { name: 'Activity', path: '/activity', icon: Clock },
  { name: 'Settings', path: '/settings', icon: Settings },
];

type SearchResult = {
  type: 'customer' | 'case';
  id: string;
  label: string;
  sublabel: string;
  path: string;
};

export default function Layout() {
  const location = useLocation();
  const navigate = useNavigate();
  const [showProfile, setShowProfile] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const [showSearch, setShowSearch] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  
  const searchRef = useRef<HTMLDivElement>(null);
  const profileRef = useRef<HTMLDivElement>(null);
  const notifRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) setShowSearch(false);
      if (profileRef.current && !profileRef.current.contains(event.target as Node)) setShowProfile(false);
      if (notifRef.current && !notifRef.current.contains(event.target as Node)) setShowNotifications(false);
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    async function performSearch() {
      if (!searchQuery.trim()) {
        setSearchResults([]);
        return;
      }
      
      try {
        const [customers, cases] = await Promise.all([
          getCustomers(searchQuery),
          getRecoveryCases({ search: searchQuery })
        ]);
        
        const results: SearchResult[] = [];
        
        customers.slice(0, 4).forEach(c => {
          results.push({
            type: 'customer',
            id: c.customer_id.toString(),
            label: c.nickname ? `Customer ${c.customer_id} (${c.nickname})` : `Customer ${c.customer_id}`,
            sublabel: `Risk: ${c.risk} • Limit: $${c.credit_limit}`,
            path: `/customers/${c.customer_id}`
          });
        });

        cases.slice(0, 4).forEach(c => {
          results.push({
            type: 'case',
            id: `case-${c.id}`,
            label: `Recovery Case #${c.id}`,
            sublabel: c.nickname ? `Customer ${c.customer_id} (${c.nickname}) • ${c.strategy.replace('_', ' ')}` : `Customer ${c.customer_id} • ${c.strategy.replace('_', ' ')}`,
            path: `/cases/${c.id}`
          });
        });

        setSearchResults(results);
      } catch (e) {
        console.error("Search failed", e);
      }
    }
    
    const timeout = setTimeout(performSearch, 300);
    return () => clearTimeout(timeout);
  }, [searchQuery]);

  useEffect(() => {
    setSelectedIndex(-1);
  }, [searchQuery, showSearch]);

  const handleSearchKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Escape') {
      setShowSearch(false);
      return;
    }
    if (!showSearch && e.key !== 'Enter') {
      setShowSearch(true);
    }
    
    if (searchResults.length > 0) {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelectedIndex(prev => (prev < searchResults.length - 1 ? prev + 1 : prev));
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedIndex(prev => (prev > 0 ? prev - 1 : prev));
      } else if (e.key === 'Enter') {
        e.preventDefault();
        if (selectedIndex >= 0 && selectedIndex < searchResults.length) {
          navigate(searchResults[selectedIndex].path);
          setShowSearch(false);
          setSearchQuery('');
        }
      }
    }
  };

  const renderLink = (item: any) => {
    const isActive = location.pathname.startsWith(item.path);
    return (
      <NavLink
        key={item.name}
        to={item.path}
        className={clsx(
          'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
          isActive ? 'bg-indigo-600 text-white' : 'text-slate-300 hover:bg-slate-800 hover:text-white'
        )}
      >
        <item.icon className={clsx("w-5 h-5", isActive ? "text-indigo-200" : "text-slate-400")} />
        {item.name}
      </NavLink>
    );
  };

  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-900 text-white flex flex-col hidden md:flex">
        <div className="p-4 flex items-center gap-3 border-b border-slate-800">
          <div className="bg-indigo-600 p-1.5 rounded-lg">
            <Layers className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="font-bold text-lg leading-tight">RevPilot</div>
            <div className="text-[10px] text-slate-400 font-medium tracking-wide">Revenue Recovery Platform</div>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto py-4 px-3 space-y-6">
          <div>
            <div className="px-3 text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Main</div>
            <div className="space-y-1">{navItems.map(renderLink)}</div>
          </div>
          <div>
            <div className="px-3 text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">System</div>
            <div className="space-y-1">{systemItems.map(renderLink)}</div>
          </div>
        </div>

        <div className="p-4 border-t border-slate-800">
          <div className="flex items-center gap-2 mb-4 px-2">
            <div className="w-2 h-2 rounded-full bg-emerald-500"></div>
            <span className="text-xs text-slate-400 flex-1">API Operational</span>
            <span className="text-xs text-slate-400 font-medium">99.9%</span>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center font-bold text-sm">A</div>
            <div className="overflow-hidden">
              <div className="text-sm font-medium truncate">Alex Chen</div>
              <div className="text-xs text-slate-400 truncate">alex@fintech.com</div>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Topbar */}
        <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6 z-10">
          <div className="font-semibold text-lg text-gray-900 capitalize">
            {location.pathname.split('/')[1].replace('-', ' ')}
          </div>
          
          <div className="flex items-center gap-6">
            <div className="relative w-72 hidden sm:block" ref={searchRef}>
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input 
                type="text" 
                placeholder="Search customers, cases..." 
                value={searchQuery}
                onChange={e => { setSearchQuery(e.target.value); setShowSearch(true); }}
                onFocus={() => setShowSearch(true)}
                onKeyDown={handleSearchKeyDown}
                className="w-full pl-9 pr-4 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:bg-white transition-colors"
              />
              {showSearch && searchQuery && (
                <div className="absolute top-full mt-2 w-full bg-white border border-gray-200 rounded-lg shadow-lg py-2 z-50 max-h-96 overflow-y-auto">
                   <div className="px-4 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wider">Results</div>
                   {searchResults.length === 0 ? (
                     <div className="px-4 py-3 text-sm text-gray-500">No results found in database</div>
                   ) : (
                     searchResults.map((result, idx) => (
                       <button 
                         key={`${result.id}-${idx}`}
                         onClick={() => { navigate(result.path); setShowSearch(false); setSearchQuery(''); }} 
                         className={clsx(
                           "w-full text-left px-4 py-2 flex items-center gap-3 transition-colors",
                           idx === selectedIndex ? "bg-indigo-50" : "hover:bg-gray-50"
                         )}
                       >
                         <div className={clsx("p-1.5 rounded", result.type === 'customer' ? "bg-emerald-100 text-emerald-700" : "bg-blue-100 text-blue-700")}>
                           {result.type === 'customer' ? <Users className="w-4 h-4" /> : <Briefcase className="w-4 h-4" />}
                         </div>
                         <div>
                           <div className="text-sm font-medium text-gray-900">{result.label}</div>
                           <div className="text-xs text-gray-500">{result.sublabel}</div>
                         </div>
                       </button>
                     ))
                   )}
                </div>
              )}
            </div>
            
            <div className="flex items-center gap-4">
              <div className="relative" ref={notifRef}>
                <button onClick={() => setShowNotifications(!showNotifications)} className="relative text-gray-500 hover:text-gray-700 p-1 focus:outline-none">
                  <Bell className="w-5 h-5" />
                </button>
                {showNotifications && (
                  <div className="absolute right-0 top-full mt-2 w-80 bg-white border border-gray-200 rounded-lg shadow-lg py-2 z-50">
                    <div className="px-4 py-2 border-b border-gray-100 flex justify-between items-center">
                      <span className="font-semibold text-gray-900">Notifications</span>
                    </div>
                    <div className="px-4 py-8 text-center">
                      <p className="text-sm text-gray-500">No new notifications.</p>
                    </div>
                  </div>
                )}
              </div>
              
              <div className="relative" ref={profileRef}>
                <div onClick={() => setShowProfile(!showProfile)} className="flex items-center gap-2 cursor-pointer hover:bg-gray-50 py-1 px-2 rounded-lg transition-colors">
                  <div className="w-8 h-8 rounded-full bg-indigo-600 text-white flex items-center justify-center font-bold text-sm">A</div>
                  <div className="hidden md:block">
                    <div className="text-sm font-medium text-gray-700 leading-tight">Alex Chen</div>
                    <div className="text-xs text-gray-500">Admin</div>
                  </div>
                  <ChevronDown className="w-4 h-4 text-gray-400" />
                </div>
                {showProfile && (
                  <div className="absolute right-0 top-full mt-2 w-48 bg-white border border-gray-200 rounded-lg shadow-lg py-1 z-50">
                    <div className="px-4 py-3 border-b border-gray-100 mb-1">
                      <div className="text-sm font-medium text-gray-900">Alex Chen</div>
                      <div className="text-xs text-gray-500">alex@fintech.com</div>
                    </div>
                    <button onClick={() => navigate('/settings')} className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50">Profile</button>
                    <button onClick={() => navigate('/settings')} className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50">Preferences</button>
                    <button onClick={() => navigate('/settings')} className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50">Settings</button>
                    <div className="border-t border-gray-100 mt-1 pt-1">
                      <button onClick={() => { alert('Authentication backend is not implemented yet. You cannot sign out.'); setShowProfile(false); }} className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50">Sign out</button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto p-6 relative">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
