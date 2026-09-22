import React from 'react';

const StatCard = ({ title, value, subtext, icon: Icon, color = 'cyan', isAlert = false }) => {
  const colorStyles = {
    cyan: 'from-cyan-500/20 to-blue-500/10 text-cyan-400 border-cyan-500/30',
    red: 'from-red-500/20 to-rose-500/10 text-red-400 border-red-500/30',
    amber: 'from-amber-500/20 to-orange-500/10 text-amber-400 border-amber-500/30',
    orange: 'from-orange-500/20 to-amber-500/10 text-orange-400 border-orange-500/30',
    violet: 'from-violet-500/20 to-purple-500/10 text-violet-400 border-violet-500/30',
    emerald: 'from-emerald-500/20 to-teal-500/10 text-emerald-400 border-emerald-500/30',
  };

  return (
    <div className={`glass-card glass-card-hover p-5 rounded-2xl relative overflow-hidden border ${isAlert ? 'glow-red border-red-500/50' : ''}`}>
      <div className={`absolute top-0 right-0 w-32 h-32 bg-gradient-to-br ${colorStyles[color] || colorStyles.cyan} rounded-full blur-3xl opacity-30 -mr-10 -mt-10 pointer-events-none`}></div>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs font-semibold tracking-wider text-slate-400 uppercase">{title}</p>
          <h3 className="text-2xl lg:text-3xl font-extrabold text-white mt-2 tracking-tight">{value}</h3>
          {subtext && <p className="text-xs text-slate-400 mt-1 font-medium">{subtext}</p>}
        </div>
        <div className={`p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 ${colorStyles[color]?.split(' ')[2] || 'text-cyan-400'}`}>
          {Icon && <Icon className="w-6 h-6" />}
        </div>
      </div>
    </div>
  );
};

export default StatCard;
