import React, { useState, useEffect, useRef } from 'react';
import { Database, RefreshCw, UserCheck, Search, Bell, CheckCircle2, ShieldAlert, AlertTriangle, Check, CheckCheck, ExternalLink, Languages } from 'lucide-react';
import { seedDatabase, getNotifications, markNotificationRead, markAllNotificationsRead, setApiRoleHeader, loginWithRole } from '../services/api';
import { useToast } from './Toast';

const Navbar = ({ activeRole, setActiveRole, onDatabaseReseeded, onSelectProject, language, setLanguage }) => {
  const [isSeeding, setIsSeeding] = useState(false);
  const [seedMessage, setSeedMessage] = useState(null);
  const [notifications, setNotifications] = useState([]);
  const [showNotifDropdown, setShowNotifDropdown] = useState(false);
  const notifRef = useRef(null);
  const toast = useToast();

  const roles = [
    { id: 'ADMIN', label: 'Central Admin (MoSPI)' },
    { id: 'DISTRICT_OFFICER', label: 'District Officer' },
    { id: 'AUDITOR', label: 'Lead Auditor (CAG)' }
  ];

  const fetchNotifications = async () => {
    try {
      const data = await getNotifications();
      setNotifications(data || []);
    } catch (err) {
      // Fallback local notifications
    }
  };

  useEffect(() => {
    fetchNotifications();
    const interval = setInterval(fetchNotifications, 15000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    setApiRoleHeader(activeRole);
    loginWithRole(activeRole).catch(() => {});
  }, [activeRole]);

  // Click outside listener for notification dropdown
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (notifRef.current && !notifRef.current.contains(event.target)) {
        setShowNotifDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleReseed = async () => {
    try {
      setIsSeeding(true);
      setSeedMessage(null);
      const res = await seedDatabase();
      setSeedMessage(`Seeded ${res.projects_seeded} records!`);
      toast.success(`Successfully seeded ${res.projects_seeded} MPLADS project records with synthetic anomalies!`, 4000);
      if (onDatabaseReseeded) onDatabaseReseeded();
      fetchNotifications();
      setTimeout(() => setSeedMessage(null), 4000);
    } catch (err) {
      setSeedMessage('Seeding failed');
      toast.error('Database seeding failed. Please check backend connectivity.', 4000);
      setTimeout(() => setSeedMessage(null), 4000);
    } finally {
      setIsSeeding(false);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await markAllNotificationsRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
    } catch (err) {
      console.error(err);
    }
  };

  const handleNotificationClick = async (notif) => {
    try {
      if (!notif.is_read) {
        await markNotificationRead(notif.id);
        setNotifications((prev) => prev.map((n) => (n.id === notif.id ? { ...n, is_read: true } : n)));
      }
      if (notif.project_id && onSelectProject) {
        onSelectProject(notif.project_id);
        setShowNotifDropdown(false);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  return (
    <header className="h-16 border-b border-slate-800/80 bg-slate-900/60 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-30">
      {/* Search Input & Role Switcher */}
      <div className="flex items-center gap-4">
        {/* Role View Switcher */}
        <div className="flex items-center bg-slate-950/80 p-1 rounded-xl border border-slate-800">
          <UserCheck className="w-4 h-4 text-cyan-400 ml-2 mr-1 hidden sm:inline" />
          <span className="text-[11px] font-semibold text-slate-400 mr-2 hidden sm:inline">Role View:</span>
          <div className="flex gap-1">
            {roles.map((r) => (
              <button
                key={r.id}
                onClick={() => setActiveRole(r.id)}
                className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
                  activeRole === r.id
                    ? 'bg-cyan-500 text-slate-950 shadow-md shadow-cyan-500/20 font-bold'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
                }`}
              >
                {r.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Action Buttons & Notifications */}
      <div className="flex items-center gap-3">
        {seedMessage && (
          <span className="text-xs text-emerald-400 bg-emerald-950/80 border border-emerald-800 px-3 py-1.5 rounded-lg flex items-center gap-1.5 animate-fade-in">
            <CheckCircle2 className="w-3.5 h-3.5" /> {seedMessage}
          </span>
        )}

        {/* Language Toggle */}
        <button
          onClick={() => {
            const newLang = language === 'en' ? 'hi' : 'en';
            setLanguage(newLang);
            toast.success(newLang === 'hi' ? 'भाषा हिन्दी में बदली गई' : 'Language changed to English', 2000);
          }}
          className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs font-semibold text-slate-200 hover:text-white transition-all"
          title="Toggle Language / भाषा बदलें"
        >
          <Languages className="w-3.5 h-3.5" />
          <span>{language === 'en' ? 'हिन्दी' : 'English'}</span>
        </button>

        {/* Re-seed DB Button */}
        <button
          onClick={handleReseed}
          disabled={isSeeding}
          className="flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs font-semibold text-cyan-400 hover:text-cyan-300 transition-all disabled:opacity-50"
          title="Re-seed database with 1,000+ synthetic MPLADS records and SIH anomalies"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isSeeding ? 'animate-spin' : ''}`} />
          <span>{isSeeding ? 'Seeding DB...' : 'Re-Seed Data'}</span>
        </button>

        {/* Notification Alert Bell with Popover */}
        <div className="relative" ref={notifRef}>
          <button
            onClick={() => setShowNotifDropdown(!showNotifDropdown)}
            className="relative p-2 rounded-xl bg-slate-800/80 border border-slate-700 text-slate-300 hover:text-white hover:bg-slate-700 transition-colors"
            title="System Alerts & Notifications"
          >
            <Bell className="w-4 h-4" />
            {unreadCount > 0 && (
              <span className="absolute -top-1 -right-1 min-w-[18px] h-[18px] px-1 rounded-full bg-red-500 text-[10px] font-bold text-white flex items-center justify-center animate-pulse shadow-md shadow-red-500/50">
                {unreadCount}
              </span>
            )}
          </button>

          {/* Dropdown Menu */}
          {showNotifDropdown && (
            <div className="absolute right-0 mt-2 w-80 sm:w-96 glass-card bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden z-50 animate-in fade-in zoom-in-95 duration-150">
              <div className="p-3.5 border-b border-slate-800 flex items-center justify-between bg-slate-950/60">
                <div className="flex items-center gap-2">
                  <Bell className="w-4 h-4 text-cyan-400" />
                  <span className="text-xs font-bold text-slate-100">Audit Alerts & Notifications</span>
                  {unreadCount > 0 && (
                    <span className="px-1.5 py-0.5 rounded-full bg-red-950 text-red-400 border border-red-800 text-[10px] font-bold">
                      {unreadCount} new
                    </span>
                  )}
                </div>
                {unreadCount > 0 && (
                  <button
                    onClick={handleMarkAllRead}
                    className="text-[11px] text-cyan-400 hover:text-cyan-300 font-semibold flex items-center gap-1"
                  >
                    <CheckCheck className="w-3.5 h-3.5" /> Mark all read
                  </button>
                )}
              </div>

              <div className="max-h-80 overflow-y-auto divide-y divide-slate-800/60">
                {notifications.length === 0 ? (
                  <div className="p-6 text-center text-xs text-slate-500">No active system alerts.</div>
                ) : (
                  notifications.map((n) => (
                    <div
                      key={n.id}
                      onClick={() => handleNotificationClick(n)}
                      className={`p-3.5 hover:bg-slate-800/50 cursor-pointer transition-colors flex items-start gap-3 ${
                        !n.is_read ? 'bg-cyan-950/20' : ''
                      }`}
                    >
                      <div
                        className={`p-1.5 rounded-lg shrink-0 mt-0.5 ${
                          n.severity === 'CRITICAL'
                            ? 'bg-red-950 text-red-400 border border-red-800'
                            : n.severity === 'HIGH'
                            ? 'bg-orange-950 text-orange-400 border border-orange-800'
                            : 'bg-amber-950 text-amber-400 border border-amber-800'
                        }`}
                      >
                        {n.severity === 'CRITICAL' ? (
                          <ShieldAlert className="w-3.5 h-3.5" />
                        ) : (
                          <AlertTriangle className="w-3.5 h-3.5" />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <h4 className="text-xs font-bold text-slate-200 truncate">{n.title}</h4>
                          <span className="text-[10px] text-slate-500 shrink-0 ml-2">
                            {new Date(n.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </span>
                        </div>
                        <p className="text-[11px] text-slate-400 line-clamp-2 mt-0.5 leading-relaxed">{n.message}</p>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

export default Navbar;

