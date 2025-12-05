import React, { useEffect, useMemo, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useBIDashboardUpdates } from '../hooks/useWebSocket';
import { useAuthStore } from '../store/authStore';
import { TenantSwitcher } from '../components/tenant/TenantSwitcher';

interface DashboardLayoutProps {
  children: React.ReactNode;
}

const DashboardLayout: React.FC<DashboardLayoutProps> = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const user = useAuthStore(state => state.user);
  const clearAuth = useAuthStore(state => state.clearAuth);
  const { isConnected, lastUpdate, updateCount } = useBIDashboardUpdates();

  const handleLogout = () => {
    clearAuth();
    navigate('/auth/login');
  };

  type NavItem = {
    name: string;
    href?: string;
    icon?: string;
    roles?: string[];
    children?: { name: string; href: string; }[];
    section?: string;
  };

  const baseNav: NavItem[] = [
    { section: 'Overview', name: 'Dashboard', href: '/dashboard', icon: '📊', roles: ['admin', 'executive', 'manager', 'clinician'] },
    { section: 'Overview', name: 'Executive View', href: '/executive', icon: '👔', roles: ['admin', 'executive'] },
    { section: 'Overview', name: 'Branch Comparison', href: '/compare', icon: '⚖️', roles: ['admin', 'executive', 'manager'] },
    {
      section: 'Overview',
      name: 'Analytics',
      icon: '📈',
      roles: ['admin', 'executive', 'manager'],
      href: '/analytics',
      // Tabs are within the Analytics page itself (Overview, Operations, Financial, Production)
    },
    { section: 'Operations', name: 'Patients', href: '/patients', icon: '🧑‍⚕️', roles: ['admin', 'executive', 'manager', 'clinician'] },
    { section: 'Operations', name: 'Appointments', href: '/appointments', icon: '🗓️', roles: ['admin', 'executive', 'manager', 'clinician'] },
    { section: 'Operations', name: 'Practices', href: '/practices', icon: '🏢', roles: ['admin', 'executive', 'manager'] },
    { section: 'System', name: 'MCP Server', href: '/admin/mcp', icon: '🖥️', roles: ['admin'] },
    { section: 'System', name: 'Integrations', href: '/integrations', icon: '🔗', roles: ['admin', 'executive', 'manager'] },
    { section: 'System', name: 'Settings', href: '/settings', icon: '⚙️', roles: ['admin', 'executive', 'manager', 'clinician'] },
  ];

  const navigationBySection = useMemo(() => {
    const role = user?.role;
    const filtered = baseNav.filter(i => !i.roles || (role && i.roles.includes(role)));
    const sections: Record<string, NavItem[]> = {};
    for (const item of filtered) {
      const key = item.section || 'General';
      sections[key] = sections[key] || [];
      sections[key].push(item);
    }
    return sections;
  }, [user?.role]);

  // Track collapsed state per section (persist to localStorage)
  const [openSections, setOpenSections] = useState<Record<string, boolean>>({});
  useEffect(() => {
    const stored = localStorage.getItem('sidebar:openSections');
    if (stored) setOpenSections(JSON.parse(stored));
  }, []);
  useEffect(() => {
    localStorage.setItem('sidebar:openSections', JSON.stringify(openSections));
  }, [openSections]);
  const toggleSection = (key: string) => setOpenSections(s => ({ ...s, [key]: !s[key] }));

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-gray-600 bg-opacity-75 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Header */}
      <header className="bg-white shadow-sm border-b sticky top-0 z-30">
        <div className="px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Mobile menu button */}
            <div className="flex items-center">
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="lg:hidden p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100"
              >
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              </button>

              <h1 className="ml-2 lg:ml-0 text-xl font-semibold text-gray-900">
                Dental Practice BI
              </h1>
            </div>

            {/* Header actions */}
            <div className="flex items-center space-x-4">
              {/* Tenant Switcher */}
              <TenantSwitcher />

              {/* Real-time connection indicator */}
              <div className="hidden sm:flex items-center space-x-2">
                <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
                <span className="text-xs text-gray-500">
                  {isConnected ? 'Live' : 'Offline'}
                </span>
                {lastUpdate && (
                  <span className="text-xs text-gray-400">
                    • {updateCount} updates
                  </span>
                )}
              </div>

              {/* User menu */}
              <div className="flex items-center space-x-3">
                <div className="hidden sm:block text-right">
                  <div className="text-sm font-medium text-gray-900">
                    {user?.firstName} {user?.lastName}
                  </div>
                  <div className="text-xs text-gray-500 capitalize">{user?.role}</div>
                </div>

                <button
                  onClick={handleLogout}
                  className="bg-primary-600 text-white px-3 py-1.5 rounded-md text-sm hover:bg-primary-700 transition-colors"
                >
                  Logout
                </button>
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="flex">
        {/* Sidebar */}
        <nav className={`
          fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-lg transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0
          ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
        `}>
          <div className="flex flex-col h-full">
            {/* Sidebar header */}
            <div className="flex items-center justify-between p-4 border-b lg:hidden">
              <h2 className="text-lg font-semibold text-gray-900">Navigation</h2>
              <button
                onClick={() => setSidebarOpen(false)}
                className="p-2 rounded-md text-gray-400 hover:text-gray-500"
              >
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Navigation items */}
            <div className="flex-1 p-4">
              {Object.entries(navigationBySection).map(([section, items]) => {
                const open = openSections[section] ?? true;
                return (
                  <div key={section} className="mb-4">
                    <button
                      onClick={() => toggleSection(section)}
                      className="w-full flex items-center justify-between px-3 py-2 text-xs font-semibold text-gray-600 uppercase tracking-wide hover:bg-gray-50 rounded"
                      aria-expanded={open}
                    >
                      <span>{section}</span>
                      <span className={`transition-transform ${open ? 'rotate-90' : ''}`}>▸</span>
                    </button>

                    {open && (
                      <ul className="mt-1 space-y-1">
                        {items.map((item) => {
                          const isParentActive = item.href && (location.pathname === item.href || location.pathname.startsWith(item.href + '/'));
                          if (item.children && item.children.length) {
                            return (
                              <li key={item.name}>
                                <div className={`flex items-center justify-between px-4 py-2 rounded-md text-sm font-medium ${isParentActive ? 'bg-primary-100 text-primary-700' : 'text-gray-700 hover:bg-gray-100'}`}>
                                  <Link
                                    to={item.href!}
                                    onClick={() => setSidebarOpen(false)}
                                    className="flex items-center space-x-3 flex-1"
                                    aria-current={isParentActive ? 'page' : undefined}
                                  >
                                    <span className="text-lg">{item.icon}</span>
                                    <span>{item.name}</span>
                                  </Link>
                                </div>
                                {/* Child links */}
                                <ul className="ml-10 mt-1 space-y-1">
                                  {item.children.map((child) => {
                                    const childActive = location.pathname === child.href;
                                    return (
                                      <li key={child.name}>
                                        <Link
                                          to={child.href}
                                          onClick={() => setSidebarOpen(false)}
                                          className={`block px-2 py-1 rounded text-sm ${childActive ? 'text-primary-700 bg-primary-50' : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'}`}
                                          aria-current={childActive ? 'page' : undefined}
                                        >
                                          {child.name}
                                        </Link>
                                      </li>
                                    );
                                  })}
                                </ul>
                              </li>
                            );
                          }

                          // Simple link
                          return (
                            <li key={item.name}>
                              <Link
                                to={item.href!}
                                onClick={() => setSidebarOpen(false)}
                                className={`
                                  flex items-center space-x-3 px-4 py-2 rounded-md text-sm font-medium transition-colors
                                  ${isParentActive ? 'bg-primary-100 text-primary-700' : 'text-gray-700 hover:bg-gray-100'}
                                `}
                                aria-current={isParentActive ? 'page' : undefined}
                              >
                                {item.icon && <span className="text-lg">{item.icon}</span>}
                                <span>{item.name}</span>
                              </Link>
                            </li>
                          );
                        })}
                      </ul>
                    )}
                  </div>
                );
              })}
            </div>

            {/* Sidebar footer - Integration status */}
            <div className="p-4 border-t border-gray-200">
              <div className="text-xs text-gray-500 mb-2">System Status</div>
              <div className="grid grid-cols-2 gap-2">
                <div className="flex items-center space-x-1">
                  <div className="w-2 h-2 bg-green-500 rounded-full" />
                  <span className="text-xs text-gray-600">Dentrix</span>
                </div>
                <div className="flex items-center space-x-1">
                  <div className="w-2 h-2 bg-green-500 rounded-full" />
                  <span className="text-xs text-gray-600">DentalIntel</span>
                </div>
                <div className="flex items-center space-x-1">
                  <div className="w-2 h-2 bg-yellow-500 rounded-full" />
                  <span className="text-xs text-gray-600">ADP</span>
                </div>
                <div className="flex items-center space-x-1">
                  <div className="w-2 h-2 bg-green-500 rounded-full" />
                  <span className="text-xs text-gray-600">Eaglesoft</span>
                </div>
              </div>
            </div>
          </div>
        </nav>

        {/* Main content */}
        <main className="flex-1 lg:ml-0">
          <div className="max-w-7xl mx-auto">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
};

export default DashboardLayout;
