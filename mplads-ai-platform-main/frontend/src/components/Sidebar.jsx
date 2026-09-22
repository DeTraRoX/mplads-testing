import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { LayoutDashboard, AlertTriangle, FilePlus2, ShieldAlert, Cpu, ChevronLeft, ChevronRight, Activity, Flame, MapPin } from 'lucide-react';
import { useTranslation } from '../i18n/translations';

const Sidebar = ({ isCollapsed, toggleSidebar, language }) => {
  const location = useLocation();
  const isTop5View = location.pathname === '/audit' && new URLSearchParams(location.search).get('top_5_percent') === 'true';
  const t = useTranslation(language || 'en');

  const navItems = [
    {
      name: t('executiveDashboard'),
      path: '/',
      icon: LayoutDashboard,
      badge: t('realtime'),
      isActive: location.pathname === '/'
    },
    {
      name: t('geospatialIntelligence'),
      path: '/map',
      icon: MapPin,
      badge: t('gis'),
      isActive: location.pathname === '/map'
    },
    {
      name: t('top5HighRisk'),
      path: '/audit?top_5_percent=true',
      icon: Flame,
      badge: t('priority'),
      isActive: isTop5View
    },
    {
      name: t('auditDesk'),
      path: '/audit',
      icon: AlertTriangle,
      badge: t('hitl'),
      isActive: location.pathname === '/audit' && !isTop5View
    },
    {
      name: t('liveAnalyzer'),
      path: '/analyzer',
      icon: FilePlus2,
      badge: t('sih'),
      isActive: location.pathname === '/analyzer'
    }
  ];

  return (
    <aside
      className={`fixed top-0 left-0 h-screen z-40 bg-slate-900/95 backdrop-blur-xl border-r border-slate-800/80 transition-all duration-300 flex flex-col justify-between ${
        isCollapsed ? 'w-20' : 'w-64'
      }`}
    >
      <div>
        <div className="h-16 px-4 flex items-center justify-between border-b border-slate-800/80">
          <div className="flex items-center gap-3 overflow-hidden">
            <div className="p-2 rounded-xl bg-gradient-to-tr from-cyan-600 to-blue-600 text-white shrink-0 shadow-lg shadow-cyan-500/20">
              <ShieldAlert className="w-6 h-6" />
            </div>
            {!isCollapsed && (
              <div>
                <h1 className="font-extrabold text-sm tracking-wide text-white leading-tight">MPLADS <span className="text-cyan-400">AI AUDIT</span></h1>
                <p className="text-[10px] text-slate-400 font-medium">SIH Forensic Prototype</p>
              </div>
            )}
          </div>
          <button
            onClick={toggleSidebar}
            className="p-1.5 rounded-lg bg-slate-800 text-slate-400 hover:text-white hover:bg-slate-700 transition-colors"
            title={isCollapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
          >
            {isCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        </div>

        <nav className="p-3 space-y-1.5 mt-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={`flex items-center justify-between px-3 py-3 rounded-xl font-medium text-sm transition-all duration-200 ${
                  item.isActive
                    ? 'bg-gradient-to-r from-cyan-500/20 to-blue-500/10 text-cyan-400 border border-cyan-500/30 shadow-md shadow-cyan-500/10'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Icon className="w-5 h-5 shrink-0" />
                  {!isCollapsed && <span>{item.name}</span>}
                </div>
                {!isCollapsed && item.badge && (
                  <span className="text-[10px] px-2 py-0.5 rounded-full font-semibold bg-slate-800 text-slate-300 border border-slate-700">
                    {item.badge}
                  </span>
                )}
              </NavLink>
            );
          })}
        </nav>
      </div>

      {!isCollapsed && (
        <div className="p-4 m-3 rounded-xl bg-slate-950/70 border border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-xs font-medium text-slate-400">
            <span className="flex items-center gap-1.5">
              <Cpu className="w-3.5 h-3.5 text-cyan-400" /> ML Engine
            </span>
            <span className="text-emerald-400 font-semibold text-[11px] flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping"></span> Active
            </span>
          </div>
          <div className="flex items-center justify-between text-xs font-medium text-slate-400">
            <span className="flex items-center gap-1.5">
              <Activity className="w-3.5 h-3.5 text-amber-400" /> Ollama Service
            </span>
            <span className="text-cyan-400 font-semibold text-[11px]">Ready (11434)</span>
          </div>
        </div>
      )}
    </aside>
  );
};

export default Sidebar;
