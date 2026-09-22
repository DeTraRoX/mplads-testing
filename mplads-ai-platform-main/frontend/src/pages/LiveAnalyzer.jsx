import React, { useState } from 'react';
import {
  FilePlus2, Sparkles, AlertTriangle, ShieldCheck, ShieldAlert, CheckCircle2
} from 'lucide-react';
import { analyzeProjectProposal } from '../services/api';

const SIH_WEIGHTS = [
  { key: 'cost_score', label: 'Cost', weight: 0.30, hint: '30%' },
  { key: 'timeline_score', label: 'Timeline', weight: 0.25, hint: '25%' },
  { key: 'payment_score', label: 'Payment', weight: 0.20, hint: '20%' },
  { key: 'geo_score', label: 'Geo', weight: 0.15, hint: '15%' },
  { key: 'duplicate_score', label: 'Duplicate', weight: 0.10, hint: '10%' }
];

const LiveAnalyzer = () => {
  const [formData, setFormData] = useState({
    title: 'Construction of Community Center & Skill Training Hub, Ward 14',
    category: 'Community Halls & Libraries',
    sanctioned_amount: 2500000,
    expenditure_amount: 2250000,
    physical_progress: 35,
    delay_months: 6,
    start_date: '2024-01-15',
    target_completion_date: '2024-07-15',
    contractor_name: 'Apex Infrastructure Pvt Ltd',
    contractor_gstin: '07AAAAA0000A1Z5',
    district_name: 'Varanasi',
    location: 'Chowk Area, Ward 14, Varanasi',
    sanctioned_latitude: 25.3176,
    sanctioned_longitude: 82.9739,
    actual_latitude: 25.34428,
    actual_longitude: 83.00341
  });

  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState(null);

  const handleChange = (e) => {
    const { name, value } = e.target;
    const numeric = ['amount', 'progress', 'latitude', 'longitude', 'delay'].some((k) => name.includes(k));
    setFormData((prev) => ({
      ...prev,
      [name]: numeric ? parseFloat(value) || 0 : value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      setAnalyzing(true);
      const res = await analyzeProjectProposal(formData);
      setResult(res);
    } catch (err) {
      console.error('Live analysis failed', err);
    } finally {
      setAnalyzing(false);
    }
  };

  const severity = (result?.severity || result?.risk_level || 'LOW').toUpperCase();

  const bannerStyles = {
    CRITICAL: 'border-red-500/50 from-red-950/60',
    HIGH: 'border-orange-500/50 from-orange-950/60',
    MEDIUM: 'border-amber-500/50 from-amber-950/60',
    LOW: 'border-emerald-500/50 from-emerald-950/60'
  };

  const BannerIcon = severity === 'LOW' ? ShieldCheck : severity === 'MEDIUM' ? AlertTriangle : ShieldAlert;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-extrabold text-white tracking-tight flex items-center gap-2.5">
          <FilePlus2 className="w-6 h-6 text-cyan-400" />
          Live Proposal SIH Risk Evaluator
        </h2>
        <p className="text-xs text-slate-400">
          Executes the transparent SIH composite formula: 0.30×Cost + 0.25×Timeline + 0.20×Payment + 0.15×Geo + 0.10×Duplicate.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-7 glass-card p-6 rounded-2xl border border-slate-800 space-y-5">
          <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2 border-b border-slate-800 pb-3">
            <Sparkles className="w-4 h-4 text-cyan-400" /> Proposal Specification Form
          </h3>

          <form onSubmit={handleSubmit} className="space-y-4 text-xs">
            <div>
              <label className="block text-slate-400 font-semibold mb-1">Project Title / Work Description</label>
              <input type="text" name="title" value={formData.title} onChange={handleChange} required className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-slate-100 focus:outline-none focus:border-cyan-500" />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-slate-400 font-semibold mb-1">Sector Category</label>
                <select name="category" value={formData.category} onChange={handleChange} className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-slate-100 focus:outline-none focus:border-cyan-500 cursor-pointer">
                  <option value="Roads & Bridges">Roads & Bridges</option>
                  <option value="Drinking Water & Sanitation">Drinking Water & Sanitation</option>
                  <option value="Education & School Infrastructure">Education & School Infrastructure</option>
                  <option value="Public Health & Hospitals">Public Health & Hospitals</option>
                  <option value="Community Halls & Libraries">Community Halls & Libraries</option>
                  <option value="Solar Lighting & Electricity">Solar Lighting & Electricity</option>
                </select>
              </div>
              <div>
                <label className="block text-slate-400 font-semibold mb-1">District Name</label>
                <input type="text" name="district_name" value={formData.district_name} onChange={handleChange} required className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-slate-100 focus:outline-none focus:border-cyan-500" />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-slate-400 font-semibold mb-1">Sanctioned Budget (INR)</label>
                <input type="number" name="sanctioned_amount" value={formData.sanctioned_amount} onChange={handleChange} required className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-slate-100 focus:outline-none focus:border-cyan-500" />
              </div>
              <div>
                <label className="block text-slate-400 font-semibold mb-1">Estimated Expenditure (INR)</label>
                <input type="number" name="expenditure_amount" value={formData.expenditure_amount} onChange={handleChange} required className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-slate-100 focus:outline-none focus:border-cyan-500" />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-slate-400 font-semibold mb-1">Physical Progress (%)</label>
                <input type="number" name="physical_progress" value={formData.physical_progress} onChange={handleChange} className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-slate-100 focus:outline-none focus:border-cyan-500" />
              </div>
              <div>
                <label className="block text-slate-400 font-semibold mb-1">Delay (months)</label>
                <input type="number" name="delay_months" value={formData.delay_months} onChange={handleChange} className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-slate-100 focus:outline-none focus:border-cyan-500" />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-slate-400 font-semibold mb-1">Start Date</label>
                <input type="date" name="start_date" value={formData.start_date} onChange={handleChange} required className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-slate-100 focus:outline-none focus:border-cyan-500" />
              </div>
              <div>
                <label className="block text-slate-400 font-semibold mb-1">Target Completion Date</label>
                <input type="date" name="target_completion_date" value={formData.target_completion_date} onChange={handleChange} required className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-slate-100 focus:outline-none focus:border-cyan-500" />
              </div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div>
                <label className="block text-slate-400 font-semibold mb-1">Sanctioned Lat</label>
                <input type="number" step="0.0001" name="sanctioned_latitude" value={formData.sanctioned_latitude} onChange={handleChange} className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-slate-100 focus:outline-none focus:border-cyan-500" />
              </div>
              <div>
                <label className="block text-slate-400 font-semibold mb-1">Sanctioned Lon</label>
                <input type="number" step="0.0001" name="sanctioned_longitude" value={formData.sanctioned_longitude} onChange={handleChange} className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-slate-100 focus:outline-none focus:border-cyan-500" />
              </div>
              <div>
                <label className="block text-slate-400 font-semibold mb-1">Actual Lat</label>
                <input type="number" step="0.0001" name="actual_latitude" value={formData.actual_latitude} onChange={handleChange} className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-slate-100 focus:outline-none focus:border-cyan-500" />
              </div>
              <div>
                <label className="block text-slate-400 font-semibold mb-1">Actual Lon</label>
                <input type="number" step="0.0001" name="actual_longitude" value={formData.actual_longitude} onChange={handleChange} className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-slate-100 focus:outline-none focus:border-cyan-500" />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-slate-400 font-semibold mb-1">Contractor Name</label>
                <input type="text" name="contractor_name" value={formData.contractor_name} onChange={handleChange} required className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-slate-100 focus:outline-none focus:border-cyan-500" />
              </div>
              <div>
                <label className="block text-slate-400 font-semibold mb-1">Contractor GSTIN</label>
                <input type="text" name="contractor_gstin" value={formData.contractor_gstin} onChange={handleChange} required className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-slate-100 focus:outline-none focus:border-cyan-500 font-mono" />
              </div>
            </div>

            <div>
              <label className="block text-slate-400 font-semibold mb-1">Specific Location Address</label>
              <input type="text" name="location" value={formData.location} onChange={handleChange} required className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-slate-100 focus:outline-none focus:border-cyan-500" />
            </div>

            <button
              type="submit"
              disabled={analyzing}
              className="w-full py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-bold text-xs flex items-center justify-center gap-2 shadow-lg shadow-cyan-500/20 transition-all disabled:opacity-50 mt-4"
            >
              <Sparkles className={`w-4 h-4 ${analyzing ? 'animate-spin' : ''}`} />
              <span>{analyzing ? 'Evaluating SIH Composite Formula...' : 'Run SIH Composite Risk Audit'}</span>
            </button>
          </form>
        </div>

        <div className="lg:col-span-5 space-y-5">
          {result ? (
            <div className="space-y-4">
              <div className={`glass-card p-6 rounded-2xl border bg-gradient-to-br ${bannerStyles[severity] || bannerStyles.LOW} via-slate-900 to-slate-950 space-y-4`}>
                <div className="flex items-center justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <div className="p-3 rounded-xl bg-slate-950/60">
                      <BannerIcon className="w-8 h-8" />
                    </div>
                    <div>
                      <span className="text-xs font-bold uppercase tracking-widest block">{severity} — Requires Review</span>
                      <h3 className="text-2xl font-extrabold text-white">Score: {result.final_risk_score ?? result.risk_score} / 100</h3>
                    </div>
                  </div>
                  <span className="px-3 py-1.5 rounded-full text-[11px] font-bold bg-slate-950/70 border border-slate-700">{result.recommendation}</span>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed border-t border-slate-800 pt-3 whitespace-pre-line">{result.ai_summary}</p>
              </div>

              <div className="glass-card p-5 rounded-2xl border border-slate-800 space-y-3">
                <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider border-b border-slate-800 pb-2">SIH 5-Factor Breakdown</h4>
                {SIH_WEIGHTS.map((w) => {
                  const val = Number(result[w.key] || 0);
                  const contrib = (val * w.weight).toFixed(1);
                  return (
                    <div key={w.key}>
                      <div className="flex justify-between text-[11px] mb-1">
                        <span className="text-slate-400">{w.label} × {w.hint}</span>
                        <span className="text-slate-100 font-bold">{val.toFixed(1)} → {contrib} pts</span>
                      </div>
                      <div className="h-1.5 rounded-full bg-slate-800 overflow-hidden">
                        <div className="h-full bg-cyan-500" style={{ width: `${Math.min(val, 100)}%` }} />
                      </div>
                    </div>
                  );
                })}
                <div className="grid grid-cols-2 gap-2 pt-2 text-[11px] text-slate-400">
                  <span>Payment {Number(result.payment_progress).toFixed(1)}%</span>
                  <span>Physical {Number(result.physical_progress).toFixed(1)}%</span>
                  <span>Mismatch {Number(result.progress_mismatch).toFixed(1)}%</span>
                  <span>Geo {Number(result.geo_distance_meters).toFixed(0)} m {result.geo_anomaly_flag ? '(flag)' : ''}</span>
                </div>
              </div>

              {/* Sentence-BERT Duplicate & Semantic Overlap Card */}
              <div className="glass-card p-5 rounded-2xl border border-cyan-900/60 bg-gradient-to-b from-cyan-950/30 to-slate-950 space-y-3">
                <div className="flex items-center justify-between border-b border-slate-800/80 pb-2">
                  <h4 className="text-xs font-bold text-cyan-400 uppercase tracking-wider flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5" /> Sentence-BERT Proposal Matcher
                  </h4>
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-cyan-950 border border-cyan-800 text-cyan-300 font-mono">
                    {result.model_used || 'Sentence-BERT (all-MiniLM-L6-v2)'}
                  </span>
                </div>
                <div className="space-y-2 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Semantic Similarity Score:</span>
                    <span className="text-sm font-bold text-white">
                      {result.similarity_score !== undefined ? `${result.similarity_score}%` : `${Number(result.duplicate_score || 0).toFixed(1)}%`}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Proposal Overlap Status:</span>
                    <span className={`px-2 py-0.5 rounded-md text-[10px] font-bold border ${
                      (result.duplicate_status === 'DUPLICATE_PROPOSAL' || result.similarity_score >= 85)
                        ? 'bg-red-950/80 border-red-800 text-red-300'
                        : (result.duplicate_status === 'HIGH_OVERLAP' || result.similarity_score >= 70)
                        ? 'bg-amber-950/80 border-amber-800 text-amber-300'
                        : 'bg-emerald-950/80 border-emerald-800 text-emerald-300'
                    }`}>
                      {result.duplicate_status || (result.similarity_score >= 85 ? 'DUPLICATE_PROPOSAL' : result.similarity_score >= 70 ? 'HIGH_OVERLAP' : 'NORMAL')}
                    </span>
                  </div>
                  {result.matched_project ? (
                    <div className="p-2.5 rounded-xl bg-slate-950 border border-slate-800 space-y-1 mt-1">
                      <span className="text-[10px] text-slate-500 font-bold uppercase block">Closest Prior Sanctioned Project:</span>
                      <p className="text-slate-200 font-semibold text-xs leading-snug">{result.matched_project}</p>
                    </div>
                  ) : (
                    <p className="text-[11px] text-slate-500 italic">No direct historical project semantic match identified.</p>
                  )}
                </div>
              </div>

              <div className="glass-card p-5 rounded-2xl border border-slate-800 space-y-3">
                <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider border-b border-slate-800 pb-2">
                  Detected Risk Indicators ({result.risk_factors.length})
                </h4>
                <div className="space-y-2 text-xs">
                  {result.risk_factors.length > 0 ? (
                    result.risk_factors.map((factor, i) => (
                      <div key={i} className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                        <div className="flex items-center justify-between font-bold">
                          <span className="text-slate-200">{factor.name}</span>
                          <span className="text-[10px] text-amber-400">{factor.severity} · {factor.score}</span>
                        </div>
                        <p className="text-[11px] text-slate-400 leading-relaxed">{factor.description}</p>
                      </div>
                    ))
                  ) : (
                    <div className="p-3 rounded-xl bg-emerald-950/40 border border-emerald-900 text-emerald-300 font-medium flex items-center gap-2">
                      <CheckCircle2 className="w-4 h-4" /> Parameters fall within expected distributions.
                    </div>
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div className="glass-card p-8 rounded-2xl border border-slate-800 h-full flex flex-col items-center justify-center text-center text-slate-400 space-y-3">
              <div className="p-4 rounded-full bg-slate-900 border border-slate-800 text-cyan-400">
                <Sparkles className="w-8 h-8" />
              </div>
              <h4 className="font-bold text-slate-200">Awaiting Proposal Submission</h4>
              <p className="text-xs max-w-xs text-slate-400">Default values match worked case MP-2024-8842. Run the audit to see the 5-factor SIH breakdown.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default LiveAnalyzer;
