import React, { useEffect, useState } from 'react';
import { useOutletContext, useNavigate } from 'react-router-dom';
import {
  IndianRupee,
  ShieldAlert,
  AlertTriangle,
  FileCheck,
  TrendingUp,
  PieChart as PieIcon,
  BarChart3,
  MapPin,
  Flame,
  Camera,
  GitCompare,
  ClipboardList,
  Eye,
  Copy,
  CalendarClock,
  CheckCircle2,
  Layers,
  Sliders,
  Sparkles,
  ArrowUpRight,
  ShieldCheck,
  Activity,
  Zap,
  Globe,
  Download,
  Clock
} from 'lucide-react';
import {
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, AreaChart, Area,
  ScatterChart, Scatter, ZAxis
} from 'recharts';
import { getKPIs, getTop5PercentWorks, getFlaggedAnomalies } from '../services/api';
import { useTranslation } from '../i18n/translations';

const SEV_COLORS = { CRITICAL: '#ef4444', HIGH: '#f97316', MEDIUM: '#f59e0b', LOW: '#10b981' };

const roleLabel = (role, t) => {
  if (role === 'DISTRICT_OFFICER') return t('districtOfficer');
  if (role === 'AUDITOR') return t('leadAuditor');
  return t('centralAdmin');
};

const Dashboard = () => {
  const { activeRole, refreshKey, language } = useOutletContext();
  const navigate = useNavigate();
  const t = useTranslation(language || 'en');
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [top5, setTop5] = useState([]);
  const [scatterData, setScatterData] = useState([]);
  const [timeStr, setTimeStr] = useState(new Date().toLocaleTimeString());

  useEffect(() => {
    const timer = setInterval(() => setTimeStr(new Date().toLocaleTimeString()), 1000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        setLoading(true);
        const [kpis, queue, anomalies] = await Promise.all([
          getKPIs(),
          getTop5PercentWorks(),
          getFlaggedAnomalies({ limit: 80 })
        ]);
        setData(kpis);
        let queueRows = queue || [];
        if (activeRole === 'DISTRICT_OFFICER') {
          queueRows = queueRows.filter((p) => p.district_name === 'Varanasi');
        }
        setTop5(queueRows.slice(0, 8));
        const scatter = (anomalies || []).slice(0, 60).map((p) => ({
          name: p.project_code,
          payment: Number(p.payment_progress || 0),
          physical: Number(p.physical_progress || 0),
          severity: p.severity,
          fill: SEV_COLORS[p.severity] || '#06b6d4'
        }));
        setScatterData(scatter);
      } catch (err) {
        console.error('Failed to load dashboard metrics', err);
      } finally {
        setLoading(false);
      }
    };
    fetchMetrics();
  }, [refreshKey, activeRole]);

  if (loading) {
    return (
      <div className="h-[80vh] flex flex-col items-center justify-center gap-4">
        <div className="relative">
          <div className="w-16 h-16 border-4 border-cyan-500/20 border-t-cyan-500 rounded-full animate-spin"></div>
          <Activity className="w-6 h-6 text-cyan-400 absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 animate-pulse" />
        </div>
        <p className="text-sm font-bold text-slate-300 tracking-wide uppercase">
          Initializing MoSPI Forensic Analytics Engine...
        </p>
      </div>
    );
  }

  const formatCurrencyCrores = (val) => `₹${(val / 10000000).toFixed(2)} Cr`;
  const severityDonut = (data.severity_distribution || []).map((s) => ({
    ...s,
    fill: SEV_COLORS[s.severity] || '#64748b'
  }));

  const riskPct = data.total_sanctioned_funds > 0
    ? ((data.suspended_fraud_value / data.total_sanctioned_funds) * 100).toFixed(1)
    : 0;

  return (
    <div className="space-y-6 pb-12">
      {/* Top Command Bar / Government Header */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-slate-900 via-slate-900/90 to-cyan-950/40 border border-slate-800/80 p-6 shadow-2xl backdrop-blur-xl">
        <div className="absolute -top-24 -right-24 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none"></div>
        <div className="absolute -bottom-24 -left-24 w-96 h-96 bg-red-500/10 rounded-full blur-3xl pointer-events-none"></div>

        <div className="relative z-10 flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2.5">
              <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-bold bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
                <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping"></span>
                {roleLabel(activeRole, t)}
              </span>
              <span className="px-2.5 py-1 rounded-full text-[11px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1">
                <ShieldCheck className="w-3.5 h-3.5" />
                {t('govStandard')}
              </span>
              <span className="px-2.5 py-1 rounded-full text-[11px] font-mono text-slate-400 bg-slate-800/80 border border-slate-700/60 flex items-center gap-1">
                <Clock className="w-3 h-3 text-cyan-400" />
                {timeStr} IST
              </span>
            </div>
            <h1 className="text-2xl md:text-3xl font-black text-white tracking-tight flex items-center gap-3">
              <span>{t('executiveDashboard')}</span>
              <span className="text-xs px-2.5 py-1 font-bold rounded-lg bg-red-950 text-red-400 border border-red-800 uppercase tracking-wider">
                SIH Problem #26102
              </span>
            </h1>
            <p className="text-xs text-slate-400 max-w-2xl leading-relaxed">
              Real-time AI-driven anomaly and fraud surveillance portal for the Ministry of Statistics and Programme Implementation (MoSPI). Continuous audit of 1,000+ national works.
            </p>
          </div>

          {/* Quick Action Navigation Buttons */}
          <div className="flex flex-wrap items-center gap-3">
            <button
              onClick={() => navigate('/map')}
              className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-slate-950 font-bold text-xs flex items-center gap-2 shadow-lg shadow-cyan-500/20 transition-all hover:scale-105"
            >
              <Globe className="w-4 h-4" />
              <span>{t('geospatialIntelligence')}</span>
              <ArrowUpRight className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => navigate('/audit?top_5_percent=true')}
              className="px-4 py-2.5 rounded-xl bg-slate-800/90 hover:bg-slate-700 border border-slate-700 text-xs font-bold text-red-400 hover:text-red-300 flex items-center gap-2 transition-all hover:scale-105"
            >
              <Flame className="w-4 h-4 text-red-500 animate-pulse" />
              <span>{t('top5HighRisk')}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Hero Financial Outlay & High-Level Risk Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Funds Outlay */}
        <div className="glass-card rounded-2xl p-5 border border-slate-800/80 bg-gradient-to-br from-slate-900/90 via-slate-900/60 to-slate-950 relative overflow-hidden group hover:border-cyan-500/40 transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Total Portfolio Outlay</span>
            <div className="p-2 rounded-xl bg-cyan-950/80 text-cyan-400 border border-cyan-800/60">
              <IndianRupee className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <div className="text-2xl font-black text-white tracking-tight">
              {formatCurrencyCrores(data.total_sanctioned_funds)}
            </div>
            <div className="flex items-center justify-between text-[11px] text-slate-400 mt-2">
              <span>{data.total_projects} sanctioned works</span>
              <span className="text-emerald-400 font-bold">100% Monitored</span>
            </div>
          </div>
          <div className="w-full bg-slate-800 h-1.5 rounded-full mt-3 overflow-hidden">
            <div className="bg-cyan-400 h-full rounded-full" style={{ width: '100%' }}></div>
          </div>
        </div>

        {/* Flagged at-risk expenditure */}
        <div className="glass-card rounded-2xl p-5 border border-red-900/50 bg-gradient-to-br from-red-950/30 via-slate-900/80 to-slate-950 relative overflow-hidden group hover:border-red-500/50 transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-red-400 uppercase tracking-wider">{t('flaggedExpenditure')}</span>
            <div className="p-2 rounded-xl bg-red-950 text-red-400 border border-red-800/80">
              <AlertTriangle className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <div className="text-2xl font-black text-red-400 tracking-tight">
              {formatCurrencyCrores(data.suspended_fraud_value)}
            </div>
            <div className="flex items-center justify-between text-[11px] text-slate-400 mt-2">
              <span className="text-red-400 font-bold">{riskPct}% of total outlay</span>
              <span className="text-slate-400">Suspension Alert</span>
            </div>
          </div>
          <div className="w-full bg-slate-800 h-1.5 rounded-full mt-3 overflow-hidden">
            <div className="bg-red-500 h-full rounded-full" style={{ width: `${Math.min(riskPct * 3, 100)}%` }}></div>
          </div>
        </div>

        {/* Critical & High-Risk Count */}
        <div className="glass-card rounded-2xl p-5 border border-orange-900/50 bg-gradient-to-br from-orange-950/30 via-slate-900/80 to-slate-950 relative overflow-hidden group hover:border-orange-500/50 transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-orange-400 uppercase tracking-wider">High & Critical Risks</span>
            <div className="p-2 rounded-xl bg-orange-950 text-orange-400 border border-orange-800/80">
              <ShieldAlert className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <div className="text-2xl font-black text-white tracking-tight flex items-baseline gap-2">
              <span className="text-red-400">{data.critical_projects_count} Critical</span>
              <span className="text-slate-500 text-lg font-normal">/</span>
              <span className="text-orange-400 text-xl font-bold">{data.high_risk_projects_count} High</span>
            </div>
            <div className="flex items-center justify-between text-[11px] text-slate-400 mt-2">
              <span>Immediate CAG Audit</span>
              <span className="text-cyan-400 font-semibold">{data.top_5_percent_count} in Top 5%</span>
            </div>
          </div>
          <div className="w-full bg-slate-800 h-1.5 rounded-full mt-3 overflow-hidden">
            <div className="bg-orange-400 h-full rounded-full" style={{ width: '45%' }}></div>
          </div>
        </div>

        {/* Human-in-the-loop audit throughput */}
        <div className="glass-card rounded-2xl p-5 border border-emerald-900/50 bg-gradient-to-br from-emerald-950/20 via-slate-900/80 to-slate-950 relative overflow-hidden group hover:border-emerald-500/50 transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-emerald-400 uppercase tracking-wider">HITL Audit Throughput</span>
            <div className="p-2 rounded-xl bg-emerald-950 text-emerald-400 border border-emerald-800/80">
              <CheckCircle2 className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <div className="text-2xl font-black text-white tracking-tight flex items-baseline gap-2">
              <span className="text-emerald-400">{data.cases_resolved_count}</span>
              <span className="text-slate-400 text-xs font-medium">resolved cases</span>
            </div>
            <div className="flex items-center justify-between text-[11px] text-slate-400 mt-2">
              <span>{data.cases_under_review_count} active under review</span>
              <span className="text-emerald-400 font-bold">Tamper-Proof</span>
            </div>
          </div>
          <div className="w-full bg-slate-800 h-1.5 rounded-full mt-3 overflow-hidden">
            <div
              className="bg-emerald-400 h-full rounded-full"
              style={{ width: `${(data.cases_resolved_count / (data.cases_resolved_count + data.cases_under_review_count || 1)) * 100}%` }}
            ></div>
          </div>
        </div>
      </div>

      {/* SIH 5-Factor Anomaly Distribution Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3.5">
        <div
          onClick={() => navigate('/audit')}
          className="glass-card p-4 rounded-xl border border-slate-800/80 hover:border-amber-500/50 cursor-pointer transition-all group"
        >
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-slate-400 uppercase">{t('paymentMismatch')}</span>
            <GitCompare className="w-4 h-4 text-amber-400 group-hover:scale-110 transition-transform" />
          </div>
          <div className="text-xl font-extrabold text-white mt-2">{data.payment_mismatch_count}</div>
          <p className="text-[10px] text-slate-500 mt-0.5">≥25% Progress Gap</p>
        </div>

        <div
          onClick={() => navigate('/map')}
          className="glass-card p-4 rounded-xl border border-slate-800/80 hover:border-orange-500/50 cursor-pointer transition-all group"
        >
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-slate-400 uppercase">{t('geospatialAnomalies')}</span>
            <MapPin className="w-4 h-4 text-orange-400 group-hover:scale-110 transition-transform" />
          </div>
          <div className="text-xl font-extrabold text-white mt-2">{data.geospatial_anomaly_count}</div>
          <p className="text-[10px] text-slate-500 mt-0.5">Deviation &gt; 500m</p>
        </div>

        <div
          onClick={() => navigate('/audit')}
          className="glass-card p-4 rounded-xl border border-slate-800/80 hover:border-purple-500/50 cursor-pointer transition-all group"
        >
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-slate-400 uppercase">{t('duplicateEvidence')}</span>
            <Camera className="w-4 h-4 text-purple-400 group-hover:scale-110 transition-transform" />
          </div>
          <div className="text-xl font-extrabold text-white mt-2">{data.duplicate_evidence_count}</div>
          <p className="text-[10px] text-slate-500 mt-0.5">SHA-256 Hash Match</p>
        </div>

        <div
          onClick={() => navigate('/audit')}
          className="glass-card p-4 rounded-xl border border-slate-800/80 hover:border-indigo-500/50 cursor-pointer transition-all group"
        >
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-slate-400 uppercase">{t('duplicateProjects')}</span>
            <Copy className="w-4 h-4 text-indigo-400 group-hover:scale-110 transition-transform" />
          </div>
          <div className="text-xl font-extrabold text-white mt-2">{data.duplicate_project_count}</div>
          <p className="text-[10px] text-slate-500 mt-0.5">BERT Overlap &ge; 70%</p>
        </div>

        <div
          onClick={() => navigate('/audit')}
          className="glass-card p-4 rounded-xl border border-slate-800/80 hover:border-red-500/50 cursor-pointer transition-all group"
        >
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-slate-400 uppercase">{t('timelineDelays')}</span>
            <CalendarClock className="w-4 h-4 text-red-400 group-hover:scale-110 transition-transform" />
          </div>
          <div className="text-xl font-extrabold text-white mt-2">{data.timeline_delay_count}</div>
          <p className="text-[10px] text-slate-500 mt-0.5">Critical Delays</p>
        </div>
      </div>

      {/* Main Forensic Charts Bento Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Severity Distribution Donut */}
        <div className="glass-card p-5 rounded-2xl border border-slate-800/80 flex flex-col justify-between">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <div className="p-2 rounded-lg bg-red-950/60 border border-red-800/50 text-red-400">
                <PieIcon className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white">Risk Severity Distribution</h3>
                <p className="text-[10px] text-slate-400">SIH 5-Factor Composite Score</p>
              </div>
            </div>
            <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-slate-800 text-slate-300">
              {data.total_projects} Total
            </span>
          </div>

          <div className="h-56 relative flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={severityDonut}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="count"
                  nameKey="severity"
                >
                  {severityDonut.map((entry, index) => (
                    <Cell key={`sev-${index}`} fill={entry.fill} stroke="#0f172a" strokeWidth={2} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    background: '#0f172a',
                    border: '1px solid #334155',
                    borderRadius: '12px',
                    fontSize: '12px',
                    color: '#fff'
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
            <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
              <span className="text-xl font-black text-white">{data.critical_projects_count + data.high_risk_projects_count}</span>
              <span className="text-[9px] font-bold text-red-400 uppercase tracking-widest">High Risk</span>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-800/60">
            {severityDonut.map((s) => (
              <div key={s.severity} className="flex items-center justify-between text-xs px-2 py-1 rounded-lg bg-slate-950/60">
                <div className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full" style={{ background: s.fill }}></span>
                  <span className="text-slate-300 text-[11px] font-medium">{s.severity}</span>
                </div>
                <span className="font-bold text-slate-100">{s.count}</span>
              </div>
            ))}
          </div>
        </div>

        {/* 5-Factor Risk Weight Decomposition */}
        <div className="glass-card p-5 rounded-2xl border border-slate-800/80 flex flex-col justify-between">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <div className="p-2 rounded-lg bg-cyan-950/60 border border-cyan-800/50 text-cyan-400">
                <BarChart3 className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white">5-Factor SIH Formula Weighting</h3>
                <p className="text-[10px] text-slate-400">Normalized anomaly intensity index</p>
              </div>
            </div>
          </div>

          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.risk_factor_distribution || []} layout="vertical" margin={{ left: 10, right: 10, top: 10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" horizontal={false} />
                <XAxis type="number" stroke="#64748b" fontSize={10} domain={[0, 40]} />
                <YAxis dataKey="factor" type="category" stroke="#94a3b8" fontSize={11} width={75} />
                <Tooltip
                  formatter={(val) => [`${val} points`, 'Avg Impact']}
                  contentStyle={{
                    background: '#0f172a',
                    border: '1px solid #334155',
                    borderRadius: '12px',
                    fontSize: '12px',
                    color: '#fff'
                  }}
                />
                <Bar dataKey="score" radius={[0, 6, 6, 0]}>
                  {(data.risk_factor_distribution || []).map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill || '#06b6d4'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="text-[11px] text-slate-400 pt-2 border-t border-slate-800/60 text-center">
            Formula: <span className="text-cyan-400 font-mono">0.30 Cost + 0.25 Time + 0.20 Pay + 0.15 Geo + 0.10 Dupl</span>
          </div>
        </div>

        {/* Monthly Fund Disbursement & Anomaly Trend */}
        <div className="glass-card p-5 rounded-2xl border border-slate-800/80 flex flex-col justify-between">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <div className="p-2 rounded-lg bg-emerald-950/60 border border-emerald-800/50 text-emerald-400">
                <TrendingUp className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white">Monthly Fund Flow vs Anomalies</h3>
                <p className="text-[10px] text-slate-400">Disbursement correlation timeline</p>
              </div>
            </div>
          </div>

          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data.monthly_fund_flow || []} margin={{ left: -15, right: 10, top: 10, bottom: 0 }}>
                <defs>
                  <linearGradient id="disburseGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#06b6d4" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="anomalyGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="month" stroke="#64748b" fontSize={10} />
                <YAxis stroke="#64748b" fontSize={10} />
                <Tooltip
                  contentStyle={{
                    background: '#0f172a',
                    border: '1px solid #334155',
                    borderRadius: '12px',
                    fontSize: '12px',
                    color: '#fff'
                  }}
                />
                <Area type="monotone" dataKey="disbursement" name="Disbursement (₹ Cr)" stroke="#06b6d4" fillOpacity={1} fill="url(#disburseGrad)" strokeWidth={2} />
                <Area type="monotone" dataKey="anomalies" name="Flagged Works" stroke="#ef4444" fillOpacity={1} fill="url(#anomalyGrad)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          <div className="flex items-center justify-center gap-4 text-[11px] pt-2 border-t border-slate-800/60">
            <div className="flex items-center gap-1.5 text-cyan-400">
              <span className="w-2.5 h-1 bg-cyan-400 rounded"></span> Disbursement
            </div>
            <div className="flex items-center gap-1.5 text-red-400">
              <span className="w-2.5 h-1 bg-red-400 rounded"></span> Anomalies
            </div>
          </div>
        </div>
      </div>

      {/* Top 5% Priority Audit Queue Interactive Table */}
      <div className="glass-card rounded-2xl border border-slate-800/80 overflow-hidden shadow-xl">
        <div className="p-5 border-b border-slate-800/80 flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-slate-950/40">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-red-950 text-red-400 border border-red-800">
              <Flame className="w-4 h-4 animate-pulse" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <span>Top 5% Priority Forensic Triage Queue</span>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-extrabold bg-red-950 text-red-400 border border-red-800">
                  {data.top_5_percent_count} Works Flagged
                </span>
              </h3>
              <p className="text-[11px] text-slate-400">Requires immediate human-in-the-loop review before subsequent installment release.</p>
            </div>
          </div>
          <button
            onClick={() => navigate('/audit?top_5_percent=true')}
            className="px-3.5 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs font-semibold text-cyan-400 hover:text-white flex items-center gap-1.5 self-start sm:self-auto transition-all"
          >
            <span>Full Triage Desk</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-900/90 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
              <tr>
                <th className="px-5 py-3.5">Project Code</th>
                <th className="px-5 py-3.5">Title & Sector</th>
                <th className="px-5 py-3.5">District / MP</th>
                <th className="px-5 py-3.5">Risk Rating</th>
                <th className="px-5 py-3.5">Progress Gap</th>
                <th className="px-5 py-3.5 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50">
              {top5.map((p) => (
                <tr key={p.id} className="hover:bg-slate-800/40 transition-colors">
                  <td className="px-5 py-3.5 font-mono text-cyan-400 font-bold">{p.project_code}</td>
                  <td className="px-5 py-3.5 max-w-sm">
                    <p className="font-semibold text-slate-100 truncate">{p.title}</p>
                    <p className="text-[10px] text-slate-500 mt-0.5">{p.category}</p>
                  </td>
                  <td className="px-5 py-3.5">
                    <p className="text-slate-200 font-medium">{p.district_name}</p>
                    <p className="text-[10px] text-slate-400">{p.mp_name}</p>
                  </td>
                  <td className="px-5 py-3.5">
                    <span
                      className="px-2.5 py-1 rounded-full text-[10px] font-extrabold border inline-flex items-center gap-1"
                      style={{
                        color: SEV_COLORS[p.severity],
                        borderColor: SEV_COLORS[p.severity],
                        backgroundColor: `${SEV_COLORS[p.severity]}15`
                      }}
                    >
                      <ShieldAlert className="w-3 h-3" />
                      {p.severity} ({Number(p.risk_score).toFixed(1)})
                    </span>
                  </td>
                  <td className="px-5 py-3.5">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-amber-400">Δ {Number(p.progress_mismatch).toFixed(1)}%</span>
                      <span className="text-[10px] text-slate-500">(Pay {Number(p.payment_progress).toFixed(0)}% vs Phys {Number(p.physical_progress).toFixed(0)}%)</span>
                    </div>
                  </td>
                  <td className="px-5 py-3.5 text-right">
                    <button
                      onClick={() => navigate(`/audit?id=${p.id}`)}
                      className="px-3 py-1.5 rounded-lg bg-cyan-950/80 hover:bg-cyan-900 border border-cyan-800 text-cyan-400 text-xs font-semibold inline-flex items-center gap-1.5 transition-all"
                    >
                      <Eye className="w-3.5 h-3.5" />
                      <span>Inspect</span>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;