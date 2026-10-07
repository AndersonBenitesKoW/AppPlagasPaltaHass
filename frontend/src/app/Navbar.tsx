import React from 'react';
import { Sparkles, History, BookOpen } from 'lucide-react';

export type TabId = 'analisis' | 'historial' | 'catalogo';

interface NavbarProps {
  tabActiva: TabId;
  onCambiarTab: (tab: TabId) => void;
  totalHistorial?: number;
}

export const Navbar: React.FC<NavbarProps> = ({ tabActiva, onCambiarTab, totalHistorial }) => {
  return (
    <header className="sticky top-0 z-40 w-full border-b border-emerald-500/15 bg-[#0a0f0d]/80 backdrop-blur-xl">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-18 flex items-center justify-between">
        {/* Logo y título */}
        <div
          className="flex items-center gap-3 cursor-pointer"
          onClick={() => onCambiarTab('analisis')}
        >
          <div className="w-10 h-10 rounded-2xl bg-linear-to-br from-emerald-400 to-emerald-700 flex items-center justify-center shadow-lg shadow-emerald-500/20 text-white font-black text-xl">
            🥑
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-extrabold text-base tracking-tight text-white">
                PaltaVision
              </span>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                YOLO11
              </span>
            </div>
            <p className="text-[11px] text-slate-400 font-medium">Diagnóstico de Palta Hass</p>
          </div>
        </div>

        {/* Pestañas de navegación */}
        <nav className="flex items-center gap-1.5 p-1 bg-[#121915] rounded-2xl border border-dark-border">
          <button
            onClick={() => onCambiarTab('analisis')}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold transition-all cursor-pointer ${
              tabActiva === 'analisis'
                ? 'bg-linear-to-r from-emerald-500 to-emerald-600 text-white shadow-md shadow-emerald-500/20'
                : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
            }`}
          >
            <Sparkles className="w-4 h-4" />
            <span>Análisis</span>
          </button>

          <button
            onClick={() => onCambiarTab('historial')}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold transition-all cursor-pointer ${
              tabActiva === 'historial'
                ? 'bg-linear-to-r from-emerald-500 to-emerald-600 text-white shadow-md shadow-emerald-500/20'
                : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
            }`}
          >
            <History className="w-4 h-4" />
            <span>Historial</span>
            {typeof totalHistorial === 'number' && totalHistorial > 0 && (
              <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-emerald-950 text-emerald-300 font-bold border border-emerald-500/30">
                {totalHistorial}
              </span>
            )}
          </button>

          <button
            onClick={() => onCambiarTab('catalogo')}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold transition-all cursor-pointer ${
              tabActiva === 'catalogo'
                ? 'bg-linear-to-r from-emerald-500 to-emerald-600 text-white shadow-md shadow-emerald-500/20'
                : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
            }`}
          >
            <BookOpen className="w-4 h-4" />
            <span className="hidden sm:inline">Guía Fitosanitaria</span>
            <span className="sm:hidden">Guía</span>
          </button>
        </nav>
      </div>
    </header>
  );
};
