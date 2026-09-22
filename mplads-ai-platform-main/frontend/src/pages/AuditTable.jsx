import React, { useEffect, useState } from 'react';
import { useOutletContext, useSearchParams } from 'react-router-dom';
import {
  Search, Filter, AlertTriangle, Eye, Sparkles, X,
  ShieldAlert, Building2, UserCheck, MapPin, CheckCircle, Bot,
  Camera, GitBranch, MessageSquare, CheckSquare, Ban, CheckCircle2,
  Hash, Navigation
} from 'lucide-react';
import {
  getFlaggedAnomalies,
  getTop5PercentWorks,
  getProjectById,
  getProjectExplanation,
  reviewProjectCase,
  requestClarification,
  verifyAnomaly,
  dismissAnomaly,
  resolveCase,
  uploadEvidence,
  recordProjectView
} from '../services/api';
import { useToast } from '../components/Toast';

const SIH_WEIGHTS = [
  { key: 'cost_score', label: 'Cost', weight: '30%' },
  { key: 'timeline_score', label: 'Timeline', weight: '25%' },
  { key: 'payment_score', label: 'Payment', weight: '20%' },
  { key: 'geo_score', label: 'Geo', weight: '15%' },
  { key: 'duplicate_score', label: 'Duplicate', weight: '10%' }
];

const AuditTable = () => {
  const { refreshKey, activeRole } = useOutletContext();
  const [searchParams] = useSearchParams();
  const toast = useToast();
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [severityFilter, setSeverityFilter] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [reviewFilter, setReviewFilter] = useState('');
  const [top5Only, setTop5Only] = useState(false);

  const [selectedProject, setSelectedProject] = useState(null);
  const [aiReport, setAiReport] = useState(null);
  const [reportLoading, setReportLoading] = useState(false);
  const [remarks, setRemarks] = useState('');
  const [actionBusy, setActionBusy] = useState(false);
  const [evidenceUrl, setEvidenceUrl] = useState('');
  const [evidenceDescription, setEvidenceDescription] = useState('');
  const [uploadingEvidence, setUploadingEvidence] = useState(false);
  const [evidenceFeedback, setEvidenceFeedback] = useState(null);
  const [actionMessage, setActionMessage] = useState(null);

  const fetchAnomalies = async () => {
    try {
      setLoading(true);
      const params = {
        search: search || undefined,
        severity: severityFilter || undefined,
        category: categoryFilter || undefined,
        review_status: reviewFilter || undefined,
        limit: 100
      };
      const res = top5Only ? await getTop5PercentWorks() : await getFlaggedAnomalies(params);
      let rows = res || [];
      if (activeRole === 'DISTRICT_OFFICER') {
        rows = rows.filter((p) => p.district_name === 'Varanasi');
      }
      if (top5Only) {
        if (search) {
          const q = search.toLowerCase();
          rows = rows.filter((p) =>
            (p.title || '').toLowerCase().includes(q) ||
            (p.project_code || '').toLowerCase().includes(q) ||
            (p.district_name || '').toLowerCase().includes(q)
          );
        }
        if (severityFilter) rows = rows.filter((p) => p.severity === severityFilter);
        if (categoryFilter) rows = rows.filter((p) => p.category === categoryFilter);
        if (reviewFilter) rows = rows.filter((p) => p.review_status === reviewFilter);
      }
      setProjects(rows);
    } catch (err) {
      console.error('Failed to load anomaly table', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const qpTop = searchParams.get('top_5_percent') === 'true';
    setTop5Only(qpTop);
  }, [searchParams]);

  useEffect(() => {
    fetchAnomalies();
  }, [search, severityFilter, categoryFilter, reviewFilter, refreshKey, top5Only, activeRole]);

  useEffect(() => {
    const openId = searchParams.get('id');
    if (openId) {
      handleOpenDrawer({ id: Number(openId) });
    }
  }, [searchParams, refreshKey]);

  const handleOpenDrawer = async (project) => {
    setAiReport(null);
    setActionMessage(null);
    setEvidenceFeedback(null);
    setRemarks(project.review_remarks || '');
    try {
      const full = await getProjectById(project.id);
      setSelectedProject(full);
      setRemarks(full.review_remarks || '');
      // Log tamper-evident audit record for every case view (fire-and-forget)
      recordProjectView(project.id).catch(() => {});
    } catch (err) {
      setSelectedProject(project);
    }
  };

  const handleAttachEvidence = async (e) => {
    e.preventDefault();
    if (!selectedProject || !evidenceUrl.trim()) return;
    try {
      setUploadingEvidence(true);
      setEvidenceFeedback(null);
      const payload = {
        image_path: evidenceUrl.trim(),
        description: evidenceDescription.trim() || 'Site photo evidence',
        latitude: selectedProject.actual_latitude,
        longitude: selectedProject.actual_longitude,
        uploaded_by: activeRole === 'ADMIN' ? 'Central Admin' : 'District Field Inspector'
      };
      const res = await uploadEvidence(selectedProject.id, payload);
      setEvidenceFeedback(
        res.is_duplicate_flag
          ? 'CRITICAL ALERT: Duplicate photo evidence detected (identical SHA-256 hash reused across projects).'
          : 'Photo evidence attached successfully with SHA-256 cryptographic hash verification.'
      );
      setEvidenceUrl('');
      setEvidenceDescription('');
      await refreshSelected();
    } catch (err) {
      setEvidenceFeedback(
        err.response?.status === 403
          ? 'Access Denied: Auditor role has read-only access and cannot upload evidence.'
          : 'Failed to attach evidence. Please verify server connectivity.'
      );
    } finally {
      setUploadingEvidence(false);
    }
  };

  const refreshSelected = async (updated) => {
    if (updated && updated.id) {
      setSelectedProject(updated);
      setRemarks(updated.review_remarks || '');
      fetchAnomalies();
      return;
    }
    if (selectedProject) {
      const full = await getProjectById(selectedProject.id);
      setSelectedProject(full);
      fetchAnomalies();
    }
  };

  const runHitlAction = async (kind) => {
    if (!selectedProject) return;
    if (!remarks.trim()) {
      setActionMessage('Add review remarks before submitting a case action.');
      toast.warning('Please add review remarks before submitting a case action.', 3000);
      return;
    }
    const payload = {
      action: kind.toUpperCase(),
      remarks,
      username: activeRole || 'Officer'
    };
    try {
      setActionBusy(true);
      let updated;
      if (kind === 'review') updated = await reviewProjectCase(selectedProject.id, payload);
      else if (kind === 'clarification') updated = await requestClarification(selectedProject.id, { remarks, requested_to: 'District Nodal Agency', username: payload.username });
      else if (kind === 'verify') updated = await verifyAnomaly(selectedProject.id, payload);
      else if (kind === 'dismiss') updated = await dismissAnomaly(selectedProject.id, payload);
      else if (kind === 'resolve') updated = await resolveCase(selectedProject.id, payload);
      setActionMessage(`Case updated to ${updated.review_status}. Hash-chained audit record created.`);
      toast.success(`Case updated to ${updated.review_status}! Cryptographic hash chain recorded.`, 3000);
      await refreshSelected(updated);
    } catch (err) {
      setActionMessage('Action failed. Check API connectivity.');
      toast.error('Case action failed. Please check server connectivity.', 3000);
    } finally {
      setActionBusy(false);
    }
  };

  const handleGenerateAiReport = async () => {
    if (!selectedProject) return;
    try {
      setReportLoading(true);
      const res = await getProjectExplanation(selectedProject.id);
      setAiReport(res.executive_summary);
    } catch (err) {
      setAiReport('Ollama service offline. Fallback: this work carries elevated anomaly indicators and requires field verification before the next tranche.');
    } finally {
      setReportLoading(false);
    }
  };

  const getRiskBadge = (project) => {
    const score = Number(project.risk_score || 0);
    const sev = project.severity || (score >= 85 ? 'CRITICAL' : score >= 70 ? 'HIGH' : score >= 40 ? 'MEDIUM' : 'LOW');
    const styles = {
      CRITICAL: 'bg-red-950/80 text-red-400 border-red-800',
      HIGH: 'bg-orange-950/80 text-orange-400 border-orange-800',
      MEDIUM: 'bg-amber-950/80 text-amber-400 border-amber-800',
      LOW: 'bg-emerald-950/80 text-emerald-400 border-emerald-800'
    };
    return (
      <span className={`px-2.5 py-1 rounded-full text-xs font-bold border flex items-center gap-1 w-fit ${styles[sev] || styles.MEDIUM}`}>
        {sev === 'LOW' ? <CheckCircle className="w-3 h-3" /> : <ShieldAlert className="w-3 h-3" />}
        {sev} ({score.toFixed(1)})
      </span>
    );
  };

  return (
    <div className="space-y-6 relative">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-extrabold text-white tracking-tight flex items-center gap-2.5">
            <AlertTriangle className="w-6 h-6 text-red-500" />
            {top5Only ? 'Top 5% Priority Audit Queue' : 'Interactive Audit Desk'}
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Filter works by review status and severity, inspect SIH risk components, and complete human-in-the-loop case actions.
          </p>
        </div>
        <button
          onClick={() => {
            try {
              const csvContent = "data:text/csv;charset=utf-8," +
                ["Code,Title,District,MP,Sanctioned,Expenditure,Severity,Risk Score",
                  ...projects.map(p => `"${p.project_code}","${p.title}","${p.district_name}","${p.mp_name}",${p.sanctioned_amount},${p.expenditure_amount},"${p.severity}",${p.risk_score}`)
                ].join("\n");
              const encodedUri = encodeURI(csvContent);
              const link = document.createElement("a");
              link.setAttribute("href", encodedUri);
              link.setAttribute("download", `MPLADS_Audit_Report_${new Date().toISOString().split('T')[0]}.csv`);
              document.body.appendChild(link);
              link.click();
              document.body.removeChild(link);
              toast.success(`Exported ${projects.length} forensic audit records to CSV!`, 3000);
            } catch (err) {
              toast.error('Failed to export CSV report', 3000);
            }
          }}
          className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs font-semibold text-slate-200 hover:text-white flex items-center gap-2 transition-all"
        >
          <Hash className="w-3.5 h-3.5 text-cyan-400" />
          Export Forensic CSV
        </button>
      </div>

      <div className="glass-card p-4 rounded-2xl border border-slate-800 flex flex-col lg:flex-row items-center justify-between gap-4">
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search title, code, location..."
            className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-4 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
          />
        </div>

        <div className="flex flex-wrap items-center gap-3 w-full lg:w-auto">
          <div className="flex items-center gap-2 bg-slate-950 px-3 py-1.5 rounded-xl border border-slate-800 text-xs">
            <Filter className="w-3.5 h-3.5 text-slate-500" />
            <select value={severityFilter} onChange={(e) => setSeverityFilter(e.target.value)} className="bg-transparent text-slate-300 focus:outline-none cursor-pointer">
              <option value="">All Severities</option>
              <option value="CRITICAL">CRITICAL</option>
              <option value="HIGH">HIGH</option>
              <option value="MEDIUM">MEDIUM</option>
              <option value="LOW">LOW</option>
            </select>
          </div>
          <div className="flex items-center gap-2 bg-slate-950 px-3 py-1.5 rounded-xl border border-slate-800 text-xs">
            <select value={reviewFilter} onChange={(e) => setReviewFilter(e.target.value)} className="bg-transparent text-slate-300 focus:outline-none cursor-pointer">
              <option value="">All Review Statuses</option>
              <option value="AI_FLAGGED">AI_FLAGGED</option>
              <option value="UNDER_REVIEW">UNDER_REVIEW</option>
              <option value="CLARIFICATION_REQUIRED">CLARIFICATION_REQUIRED</option>
              <option value="VERIFIED">VERIFIED</option>
              <option value="DISMISSED">DISMISSED</option>
              <option value="RESOLVED">RESOLVED</option>
            </select>
          </div>
          <div className="flex items-center gap-2 bg-slate-950 px-3 py-1.5 rounded-xl border border-slate-800 text-xs">
            <select value={categoryFilter} onChange={(e) => setCategoryFilter(e.target.value)} className="bg-transparent text-slate-300 focus:outline-none cursor-pointer">
              <option value="">All Sectors</option>
              <option value="Roads & Bridges">Roads & Bridges</option>
              <option value="Drinking Water & Sanitation">Water & Sanitation</option>
              <option value="Education & School Infrastructure">Education</option>
              <option value="Public Health & Hospitals">Health & Hospitals</option>
              <option value="Community Halls & Libraries">Community Halls</option>
              <option value="Solar Lighting & Electricity">Solar Lighting</option>
              <option value="Sports & Youth Infrastructure">Sports & Youth</option>
            </select>
          </div>
          <label className="flex items-center gap-2 text-xs text-slate-300 bg-slate-950 px-3 py-1.5 rounded-xl border border-slate-800 cursor-pointer">
            <input type="checkbox" checked={top5Only} onChange={(e) => setTop5Only(e.target.checked)} />
            Top 5% only
          </label>
        </div>
      </div>

      <div className="glass-card rounded-2xl border border-slate-800 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-900/80 text-slate-400 uppercase font-semibold text-[11px] tracking-wider border-b border-slate-800">
              <tr>
                <th className="px-5 py-4">Project Code & Title</th>
                <th className="px-5 py-4">District / MP</th>
                <th className="px-5 py-4">Progress</th>
                <th className="px-5 py-4">Review Status</th>
                <th className="px-5 py-4">Risk Rating</th>
                <th className="px-5 py-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {loading ? (
                <tr>
                  <td colSpan="6" className="text-center py-12 text-slate-400">
                    <div className="w-6 h-6 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
                    Querying flagged anomaly logs...
                  </td>
                </tr>
              ) : projects.length === 0 ? (
                <tr>
                  <td colSpan="6" className="text-center py-12 text-slate-400">No matching works requiring review.</td>
                </tr>
              ) : (
                projects.map((p) => (
                  <tr key={p.id} className="hover:bg-slate-900/50 transition-colors">
                    <td className="px-5 py-4 max-w-xs">
                      <span className="font-mono text-[11px] text-cyan-400 font-semibold block">{p.project_code}</span>
                      <span className="font-semibold text-slate-100 line-clamp-1 mt-0.5">{p.title}</span>
                      <span className="text-[10px] text-slate-500 block mt-0.5">{p.category}</span>
                    </td>
                    <td className="px-5 py-4">
                      <span className="font-medium text-slate-200 block">{p.district_name}</span>
                      <span className="text-[11px] text-slate-400 block">{p.mp_name}</span>
                    </td>
                    <td className="px-5 py-4">
                      <span className="block text-slate-200">Pay {Number(p.payment_progress || 0).toFixed(0)}% · Phys {Number(p.physical_progress || 0).toFixed(0)}%</span>
                      <span className="text-[11px] text-amber-400">Mismatch {Number(p.progress_mismatch || 0).toFixed(1)}%</span>
                    </td>
                    <td className="px-5 py-4">
                      <span className="text-[10px] font-bold px-2 py-1 rounded-full bg-slate-950 border border-slate-700 text-slate-300">{p.review_status}</span>
                    </td>
                    <td className="px-5 py-4">{getRiskBadge(p)}</td>
                    <td className="px-5 py-4 text-right">
                      <button
                        onClick={() => handleOpenDrawer(p)}
                        className="px-3 py-1.5 rounded-xl bg-cyan-950/80 hover:bg-cyan-900 border border-cyan-800 text-cyan-400 text-xs font-semibold flex items-center gap-1.5 ml-auto transition-all"
                      >
                        <Eye className="w-3.5 h-3.5" /> Inspect
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {selectedProject && (
        <div className="fixed inset-0 z-50 flex justify-end bg-slate-950/80 backdrop-blur-sm">
          <div className="w-full max-w-2xl bg-slate-900 border-l border-slate-800 h-full p-6 overflow-y-auto space-y-5 shadow-2xl">
            <div className="flex items-start justify-between border-b border-slate-800 pb-4">
              <div>
                <span className="font-mono text-xs text-cyan-400 font-bold">{selectedProject.project_code}</span>
                <h3 className="text-lg font-extrabold text-white mt-1">{selectedProject.title}</h3>
                <p className="text-xs text-slate-400 mt-0.5">{selectedProject.category} • {selectedProject.location}</p>
              </div>
              <button onClick={() => setSelectedProject(null)} className="p-1.5 rounded-lg bg-slate-800 text-slate-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-400">SIH Composite Risk</span>
              {getRiskBadge(selectedProject)}
            </div>

            <div className="glass-card p-4 rounded-xl border border-slate-800 space-y-3">
              <h4 className="text-[11px] font-bold text-slate-300 uppercase tracking-wider">5-Component Risk Formula</h4>
              <p className="text-[10px] text-slate-500">Risk = 0.30×Cost + 0.25×Timeline + 0.20×Payment + 0.15×Geo + 0.10×Duplicate</p>
              {SIH_WEIGHTS.map((w) => {
                const val = Number(selectedProject[w.key] || 0);
                return (
                  <div key={w.key}>
                    <div className="flex justify-between text-[11px] mb-1">
                      <span className="text-slate-400">{w.label} ({w.weight})</span>
                      <span className="text-slate-100 font-bold">{val.toFixed(1)}</span>
                    </div>
                    <div className="h-1.5 rounded-full bg-slate-800 overflow-hidden">
                      <div className="h-full bg-cyan-500" style={{ width: `${Math.min(val, 100)}%` }} />
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="glass-card p-4 rounded-xl border border-slate-800 space-y-3">
              <h4 className="text-[11px] font-bold text-slate-300 uppercase tracking-wider">Progress & Mismatch Meter</h4>
              <div className="text-xs text-slate-300">
                Payment {Number(selectedProject.payment_progress || 0).toFixed(1)}% vs Physical {Number(selectedProject.physical_progress || 0).toFixed(1)}%
                <span className="text-amber-400 font-bold"> · Δ {Number(selectedProject.progress_mismatch || 0).toFixed(1)}%</span>
              </div>
              <div>
                <div className="text-[10px] text-slate-500 mb-1">Payment progress</div>
                <div className="h-2 rounded-full bg-slate-800 overflow-hidden">
                  <div className="h-full bg-orange-400" style={{ width: `${Math.min(selectedProject.payment_progress || 0, 100)}%` }} />
                </div>
              </div>
              <div>
                <div className="text-[10px] text-slate-500 mb-1">Physical progress</div>
                <div className="h-2 rounded-full bg-slate-800 overflow-hidden">
                  <div className="h-full bg-emerald-400" style={{ width: `${Math.min(selectedProject.physical_progress || 0, 100)}%` }} />
                </div>
              </div>
            </div>

            <div className="glass-card p-4 rounded-xl border border-slate-800 space-y-2 text-xs">
              <h4 className="text-[11px] font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                <Navigation className="w-3.5 h-3.5 text-cyan-400" /> Geospatial Inspection
              </h4>
              <p className="text-slate-400">Sanctioned: {selectedProject.sanctioned_latitude}, {selectedProject.sanctioned_longitude}</p>
              <p className="text-slate-400">Actual: {selectedProject.actual_latitude}, {selectedProject.actual_longitude}</p>
              <p className="text-slate-200">
                Haversine: <span className="font-bold">{Number(selectedProject.geo_distance_meters || 0).toFixed(0)} m</span>
                {selectedProject.geo_anomaly_flag || selectedProject.geo_distance_meters > 500 ? (
                  <span className="ml-2 text-red-400 font-bold">Anomaly detected (&gt;500m) — requires review</span>
                ) : (
                  <span className="ml-2 text-emerald-400">Within 500m tolerance</span>
                )}
              </p>
            </div>

            {selectedProject.matched_proposal_title && (
              <div className="glass-card p-4 rounded-xl border border-cyan-900/60 bg-slate-950 space-y-2 text-xs">
                <h4 className="text-[11px] font-bold text-cyan-400 uppercase tracking-wider flex items-center gap-1.5">
                  <GitBranch className="w-3.5 h-3.5 text-cyan-400" /> Sentence-BERT Duplicate Proposal Match
                </h4>
                <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 space-y-1">
                  <span className="text-[10px] text-slate-500 font-semibold uppercase block">Prior Recorded Proposal:</span>
                  <p className="text-slate-200 font-bold">{selectedProject.matched_proposal_title}</p>
                  <div className="flex items-center gap-3 pt-1 text-[11px]">
                    <span className="text-slate-400">Semantic Overlap: <strong className="text-cyan-400">{((selectedProject.duplicate_similarity_ratio || 0) * 100).toFixed(1)}%</strong></span>
                    <span className="text-slate-400">Score: <strong className="text-amber-400">{Number(selectedProject.duplicate_score || 0).toFixed(1)}/100</strong></span>
                  </div>
                </div>
              </div>
            )}

            <div className="space-y-3">
              <h4 className="text-[11px] font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                <Camera className="w-3.5 h-3.5 text-cyan-400" /> Photo Evidence Gallery
              </h4>
              <div className="grid grid-cols-2 gap-3">
                {(selectedProject.evidence_items || []).length === 0 && (
                  <p className="text-xs text-slate-500 col-span-2">No evidence attached.</p>
                )}
                {(selectedProject.evidence_items || []).map((ev) => (
                  <div key={ev.id} className="rounded-xl overflow-hidden border border-slate-800 bg-slate-950">
                    <img src={ev.image_path} alt={ev.description || 'Evidence'} className="w-full h-28 object-cover" />
                    <div className="p-2 space-y-1">
                      <p className="text-[10px] text-slate-400 line-clamp-2">{ev.description}</p>
                      <p className="text-[10px] font-mono text-slate-500 truncate">SHA-256 {ev.image_hash}</p>
                      {ev.is_duplicate_flag && (
                        <span className="inline-block text-[10px] font-bold text-red-400 border border-red-800 rounded px-1.5 py-0.5">Duplicate hash — reused photo indicator</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>

              {/* Attach Evidence Form */}
              <form onSubmit={handleAttachEvidence} className="p-3.5 rounded-xl border border-slate-800 bg-slate-950/80 space-y-2.5">
                <h5 className="text-[11px] font-bold text-slate-300">Attach Field Evidence Photo</h5>
                <div>
                  <input
                    type="url"
                    value={evidenceUrl}
                    onChange={(e) => setEvidenceUrl(e.target.value)}
                    placeholder="Evidence Image URL (https://...)"
                    className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
                  />
                </div>
                <div>
                  <input
                    type="text"
                    value={evidenceDescription}
                    onChange={(e) => setEvidenceDescription(e.target.value)}
                    placeholder="Inspection description (e.g. Plinth verification photograph)"
                    className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
                  />
                </div>
                <div className="flex items-center justify-between">
                  <button
                    type="button"
                    onClick={() => setEvidenceUrl("https://images.unsplash.com/photo-1541888946425-d0fbb186156f?w=600&auto=format&fit=crop")}
                    className="text-[10px] text-cyan-400 hover:text-cyan-300 underline"
                  >
                    Use Sample Image (Triggers Duplicate Check)
                  </button>
                  <button
                    type="submit"
                    disabled={uploadingEvidence || activeRole === 'AUDITOR' || !evidenceUrl.trim()}
                    className="px-3 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-slate-950 font-bold text-xs flex items-center gap-1 transition-all"
                  >
                    {uploadingEvidence ? 'Hashing...' : 'Attach & Hash'}
                  </button>
                </div>
                {evidenceFeedback && (
                  <p className={`text-[11px] p-2 rounded-lg ${evidenceFeedback.includes('ALERT') ? 'bg-red-950/70 border border-red-800 text-red-300' : 'bg-emerald-950/70 border border-emerald-800 text-emerald-300'}`}>
                    {evidenceFeedback}
                  </p>
                )}
              </form>
            </div>

            <div className="space-y-2">
              <h4 className="text-[11px] font-bold text-slate-300 uppercase tracking-wider">Milestone Timeline</h4>
              <div className="space-y-2">
                {(selectedProject.milestones || []).map((m) => (
                  <div key={m.id} className="flex items-start gap-3 text-xs">
                    <div className={`mt-1 w-2.5 h-2.5 rounded-full ${m.status === 'Completed' ? 'bg-emerald-400' : m.status === 'Delayed' ? 'bg-red-400' : 'bg-amber-400'}`} />
                    <div>
                      <p className="text-slate-200 font-semibold">{m.name} · {m.status} ({Number(m.completion_percentage).toFixed(0)}%)</p>
                      <p className="text-[10px] text-slate-500">Planned {m.planned_start_date} → {m.planned_end_date}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="space-y-2 text-xs">
              <h4 className="font-bold text-slate-300 uppercase text-[11px] tracking-wider">Detected Risk Indicators</h4>
              {(selectedProject.anomaly_logs || []).map((log) => (
                <div key={log.id} className="p-3 rounded-xl bg-red-950/40 border border-red-900/60 space-y-1">
                  <div className="flex items-center justify-between text-red-400 font-bold">
                    <span>{log.anomaly_type}</span>
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-red-900/80 text-red-200">{log.severity}</span>
                  </div>
                  <p className="text-[11px] text-slate-300">{log.details}</p>
                </div>
              ))}
            </div>

            <div className="glass-card p-4 rounded-xl border border-slate-800 space-y-3">
              <h4 className="text-[11px] font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                <MessageSquare className="w-3.5 h-3.5" /> Human-in-the-Loop Case Management
              </h4>
              <p className="text-[10px] text-slate-500">Current status: <strong className="text-slate-300">{selectedProject.review_status}</strong></p>
              {activeRole === 'AUDITOR' && (
                <div className="p-2.5 rounded-lg bg-amber-950/40 border border-amber-800 text-[11px] text-amber-300">
                  Auditor Mode: Read-only access to audit trail and forensic data. Case action mutations are restricted to Central Admin & District Officers.
                </div>
              )}
              <textarea
                value={remarks}
                onChange={(e) => setRemarks(e.target.value)}
                rows={3}
                disabled={activeRole === 'AUDITOR'}
                placeholder="Add review remarks..."
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-cyan-500 disabled:opacity-50"
              />
              <div className="grid grid-cols-2 gap-2">
                <button disabled={actionBusy || activeRole === 'AUDITOR'} onClick={() => runHitlAction('review')} className="px-3 py-2 rounded-lg bg-slate-800 disabled:opacity-40 text-[11px] font-semibold text-slate-200">Under Review</button>
                <button disabled={actionBusy || activeRole === 'AUDITOR'} onClick={() => runHitlAction('clarification')} className="px-3 py-2 rounded-lg bg-amber-950 disabled:opacity-40 border border-amber-800 text-[11px] font-semibold text-amber-300">Request Clarification</button>
                <button disabled={actionBusy || activeRole === 'AUDITOR'} onClick={() => runHitlAction('verify')} className="px-3 py-2 rounded-lg bg-cyan-950 disabled:opacity-40 border border-cyan-800 text-[11px] font-semibold text-cyan-300 flex items-center justify-center gap-1"><CheckSquare className="w-3 h-3" /> Verify Anomaly</button>
                <button disabled={actionBusy || activeRole === 'AUDITOR'} onClick={() => runHitlAction('dismiss')} className="px-3 py-2 rounded-lg bg-slate-950 disabled:opacity-40 border border-slate-700 text-[11px] font-semibold text-slate-300 flex items-center justify-center gap-1"><Ban className="w-3 h-3" /> Dismiss</button>
                <button disabled={actionBusy || activeRole === 'AUDITOR'} onClick={() => runHitlAction('resolve')} className="col-span-2 px-3 py-2 rounded-lg bg-emerald-950 disabled:opacity-40 border border-emerald-800 text-[11px] font-semibold text-emerald-300 flex items-center justify-center gap-1"><CheckCircle2 className="w-3 h-3" /> Resolve</button>
              </div>
              {actionMessage && <p className="text-[11px] text-cyan-400">{actionMessage}</p>}
            </div>

            <div className="space-y-2">
              <h4 className="text-[11px] font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                <Hash className="w-3.5 h-3.5 text-cyan-400" /> Tamper-Evident Hash-Chained Audit Trail
              </h4>
              <div className="space-y-2">
                {(selectedProject.audit_logs || []).map((a) => (
                  <div key={a.id} className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-[11px] space-y-1">
                    <div className="flex justify-between text-slate-200 font-semibold">
                      <span>{a.action}</span>
                      <span className="text-slate-500">{a.username}</span>
                    </div>
                    <p className="text-slate-400">{a.remarks}</p>
                    {a.old_value && <p className="text-slate-500">{a.old_value} → {a.new_value}</p>}
                    <p className="font-mono text-[10px] text-slate-600 truncate">prev {a.previous_hash}</p>
                    <p className="font-mono text-[10px] text-cyan-700 truncate">hash {a.record_hash}</p>
                  </div>
                ))}
              </div>
            </div>

            <div className="glass-card p-4 rounded-xl border border-cyan-900/50 bg-gradient-to-b from-cyan-950/30 to-slate-950 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-cyan-400 font-bold text-xs">
                  <Bot className="w-4 h-4" />
                  <span>Ollama LLM Audit Report</span>
                </div>
                <button
                  onClick={handleGenerateAiReport}
                  disabled={reportLoading}
                  className="px-3 py-1.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 text-xs font-bold flex items-center gap-1.5 disabled:opacity-50"
                >
                  <Sparkles className={`w-3.5 h-3.5 ${reportLoading ? 'animate-spin' : ''}`} />
                  {reportLoading ? 'Generating...' : 'Trigger Ollama AI'}
                </button>
              </div>
              {aiReport ? (
                <div className="p-3 rounded-lg bg-slate-950/80 border border-cyan-800/60 text-xs text-slate-200 leading-relaxed">{aiReport}</div>
              ) : (
                <p className="text-[11px] text-slate-500 italic">Generate a 2-sentence executive audit summary.</p>
              )}
            </div>

            <div className="grid grid-cols-2 gap-3 pt-2 text-xs">
              <div className="bg-slate-950/70 p-3 rounded-lg border border-slate-800">
                <span className="text-slate-500 block text-[11px]">Member of Parliament</span>
                <span className="text-slate-100 font-bold">{selectedProject.mp_name}</span>
              </div>
              <div className="bg-slate-950/70 p-3 rounded-lg border border-slate-800">
                <span className="text-slate-500 block text-[11px]">Contractor</span>
                <span className="text-slate-100 font-bold">{selectedProject.contractor_name}</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AuditTable;
