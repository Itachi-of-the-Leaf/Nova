import React from 'react';
import { AppState } from '../../types';
import { CheckCircle2, AlertCircle, Info } from 'lucide-react';
import { motion } from 'framer-motion'; // Usually framer-motion in Vite/React

export function VerifyStep({ state, updateState, onNext }: { state: AppState, updateState: (s: Partial<AppState>) => void, onNext: () => void }) {
  const handleMetadataChange = (field: keyof AppState['metadata'], value: string | string[]) => {
    updateState({
      metadata: {
        ...state.metadata,
        [field]: value
      }
    });
  };

  // Ensure we have a valid number, default to 0 if undefined
  const confidence = state.metadata.confidence || 0;
  const confidenceColor = confidence > 80 ? 'text-emerald-600' : confidence > 50 ? 'text-amber-500' : 'text-red-500';
  const barColor = confidence > 80 ? 'from-emerald-400 to-emerald-600' : confidence > 50 ? 'from-amber-400 to-amber-600' : 'from-red-400 to-red-600';

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[2.2fr_1.2fr] gap-8 h-[calc(100vh-140px)] overflow-hidden">
      {/* Left Column: Raw Text Feed */}
      <motion.div
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden flex flex-col"
      >
        <div className="bg-slate-50 px-6 py-4 border-b border-slate-200 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
            <h3 className="font-bold text-slate-800 uppercase tracking-wider text-sm">
              Raw Text Feed
            </h3>
          </div>
          <div className="flex items-center gap-2 text-xs font-bold text-slate-400 bg-slate-200/50 px-3 py-1 rounded-full">
            <Info className="w-3 h-3" />
            READ-ONLY STREAM
          </div>
        </div>
        <div className="p-8 flex-1 overflow-y-auto bg-slate-50/30 font-mono text-sm text-slate-600 leading-relaxed selection:bg-amber-100">
          <pre className="whitespace-pre-wrap">
            {state.rawText}
          </pre>
        </div>
      </motion.div>

      {/* Right Column: Glass Box Human-in-the-Loop */}
      <motion.div
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        className="flex flex-col gap-6 overflow-y-auto pr-2 custom-scrollbar"
      >
        {/* Box 1: AI Confidence Score (DYNAMIC) */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 border-l-4 border-l-emerald-500">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-slate-900 text-sm uppercase tracking-tight">AI Extraction Confidence</h3>
            <span className={`${confidenceColor} font-black text-xl`}>{confidence}%</span>
          </div>
          <div className="w-full bg-slate-100 rounded-full h-3 mb-4 overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${confidence}%` }}
              transition={{ duration: 1, ease: "easeOut" }}
              className={`bg-gradient-to-r ${barColor} h-full rounded-full`}
            />
          </div>
          <p className="text-xs text-slate-500 flex items-start gap-2 leading-relaxed">
            {confidence > 80 ? <CheckCircle2 className="w-4 h-4 text-emerald-500 flex-shrink-0" /> : <AlertCircle className="w-4 h-4 text-amber-500 flex-shrink-0" />}
            {confidence > 80 ? "Structural parsing complete. High confidence in entity extraction. Please verify the tags below for absolute precision." : "AI confidence is lower than optimal. Please carefully review the extracted tags below."}
          </p>
        </div>

        {/* Box 2: Tag Review */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 flex-1 flex flex-col">
          <h3 className="font-bold text-slate-900 text-sm uppercase tracking-tight mb-6 flex items-center gap-2">
            Tag Review
            <span className="text-[10px] font-bold text-amber-600 bg-amber-50 px-2 py-0.5 rounded border border-amber-100">EDITABLE</span>
          </h3>

          <div className="space-y-6 flex-1 overflow-y-auto pr-2 custom-scrollbar">
            <Field label="Title" value={state.metadata.title} onChange={(v) => handleMetadataChange('title', v)} rows={2} />
            <Field label="Authors" value={state.metadata.authors} onChange={(v) => handleMetadataChange('authors', v)} rows={1} />
            <Field label="Abstract" value={state.metadata.abstract} onChange={(v) => handleMetadataChange('abstract', v)} rows={5} />
            <Field label="Headings" value={state.metadata.headings} onChange={(v) => handleMetadataChange('headings', v)} rows={4} />
            <Field
              label="References"
              value={Array.isArray(state.metadata.references) ? state.metadata.references.join('\n\n') : state.metadata.references}
              onChange={(v) => handleMetadataChange('references', v.split('\n\n').filter(s => s.trim().length > 0))}
              rows={4}
            />
          </div>

          <div className="mt-8 pt-6 border-t border-slate-100">
            <button
              onClick={onNext}
              className="w-full bg-[#ffc107] hover:bg-amber-500 text-slate-900 font-black py-4 px-6 rounded-xl transition-all shadow-lg hover:shadow-amber-100 active:scale-[0.98] flex items-center justify-center gap-3 uppercase tracking-widest text-sm"
            >
              Confirm Structure & Next Step
            </button>
          </div>
        </div>
      </motion.div>
    </div>
  );
}

function Field({ label, value, onChange, rows }: { label: string, value: string, onChange: (v: string) => void, rows: number }) {
  return (
    <div className="group">
      <label className="block text-[10px] font-black text-slate-400 mb-2 uppercase tracking-[0.2em] group-focus-within:text-amber-600 transition-colors">
        {label}
      </label>
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        rows={rows}
        className="w-full text-sm border border-slate-200 rounded-xl p-4 focus:ring-4 focus:ring-amber-400/10 focus:border-amber-400 outline-none transition-all resize-none bg-slate-50/50 focus:bg-white text-slate-700 font-medium leading-relaxed"
      />
    </div>
  );
}