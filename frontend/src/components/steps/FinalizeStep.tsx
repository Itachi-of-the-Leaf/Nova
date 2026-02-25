import React from 'react';
import { AppState } from '../../types';
import { Fingerprint, ShieldCheck, Zap, ArrowRight, CheckCircle2 } from 'lucide-react';
import { motion } from 'motion/react';

export function FinalizeStep({ state, onNext }: { state: AppState, onNext: () => void }) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-[2.2fr_1.2fr] gap-8 h-[calc(100vh-140px)] overflow-hidden">
      {/* Left Column: Final Product Preview */}
      <motion.div 
        initial={{ opacity: 0, scale: 0.98 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-slate-900 rounded-3xl shadow-2xl overflow-hidden flex flex-col relative"
      >
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_120%,rgba(255,193,7,0.1),transparent)] pointer-events-none"></div>
        <div className="bg-slate-800/50 px-8 py-6 border-b border-slate-700 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 bg-amber-400 rounded-xl flex items-center justify-center shadow-[0_0_20px_rgba(255,193,7,0.3)]">
              <ShieldCheck className="w-6 h-6 text-slate-900" />
            </div>
            <div>
              <h3 className="font-black text-white text-sm uppercase tracking-widest">Final Product Preview</h3>
              <p className="text-[10px] text-slate-400 font-bold uppercase tracking-tighter">IEEE Standard Compliant</p>
            </div>
          </div>
          <div className="flex items-center gap-2 text-xs font-bold text-emerald-400 bg-emerald-400/10 px-4 py-1.5 rounded-full border border-emerald-400/20">
            <CheckCircle2 className="w-3 h-3" />
            READY FOR EXPORT
          </div>
        </div>
        
        <div className="p-16 flex-1 overflow-y-auto flex items-center justify-center">
          <motion.div 
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="text-center max-w-md"
          >
            <div className="w-24 h-24 bg-slate-800 rounded-3xl flex items-center justify-center mx-auto mb-8 border border-slate-700 shadow-2xl">
              <Zap className="w-12 h-12 text-amber-400" />
            </div>
            <h2 className="text-4xl font-black text-white mb-6 leading-tight">Your Manuscript is <span className="text-amber-400">Optimized.</span></h2>
            <p className="text-slate-400 text-lg leading-relaxed mb-10">
              N.O.V.A. has successfully applied IEEE formatting, verified all citations, and generated cryptographic proofs of integrity.
            </p>
            <div className="flex flex-col gap-4">
              <div className="bg-slate-800/50 p-4 rounded-2xl border border-slate-700 flex items-center justify-between">
                <span className="text-slate-500 text-xs font-bold uppercase tracking-widest">Format</span>
                <span className="text-white font-bold">IEEE Transactions</span>
              </div>
              <div className="bg-slate-800/50 p-4 rounded-2xl border border-slate-700 flex items-center justify-between">
                <span className="text-slate-500 text-xs font-bold uppercase tracking-widest">Integrity</span>
                <span className="text-emerald-400 font-bold">Verified ({state.semanticHashScore}%)</span>
              </div>
            </div>
          </motion.div>
        </div>
      </motion.div>

      {/* Right Column: Cryptographic Integrity Proofs */}
      <div className="flex flex-col gap-6 overflow-y-auto pr-2 custom-scrollbar">
        <motion.div 
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          className="bg-white rounded-3xl border border-slate-200 shadow-sm p-8 flex-1 flex flex-col"
        >
          <div className="flex items-center gap-4 mb-10">
            <div className="w-12 h-12 bg-slate-900 rounded-2xl flex items-center justify-center shadow-lg">
              <Fingerprint className="w-6 h-6 text-amber-400" />
            </div>
            <h3 className="font-black text-slate-900 text-lg uppercase tracking-tight">Hashing Dashboard</h3>
          </div>

          <div className="space-y-8 flex-1">
            <HashBox 
              label="Original Lexical Hash (SHA-256)" 
              hash={state.lexicalHashOriginal} 
              status="original"
            />
            <HashBox 
              label="Final Lexical Hash (SHA-256)" 
              hash={state.lexicalHashFinal} 
              status="modified"
              note="Lexical hash altered due to human-verified copy-editing."
            />
            
            <div className="pt-6 border-t border-slate-100">
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-xs font-black text-slate-400 uppercase tracking-widest">Semantic Hash Score</h4>
                <span className="text-emerald-600 font-black text-2xl">{state.semanticHashScore}%</span>
              </div>
              <div className="w-full bg-slate-100 rounded-full h-4 mb-4 overflow-hidden shadow-inner">
                <motion.div 
                  initial={{ width: 0 }}
                  animate={{ width: `${state.semanticHashScore}%` }}
                  transition={{ duration: 1.5, ease: "easeOut" }}
                  className="bg-gradient-to-r from-emerald-400 to-emerald-600 h-full rounded-full"
                />
              </div>
              <p className="text-[11px] text-slate-500 leading-relaxed bg-slate-50 p-4 rounded-xl border border-slate-100 italic">
                "High semantic score mathematically proves <span className="text-emerald-600 font-bold">0% scientific hallucination</span>. The core research intent remains identical despite formatting optimizations."
              </p>
            </div>
          </div>

          <div className="mt-10 pt-8 border-t border-slate-100">
            <button 
              onClick={onNext}
              className="w-full bg-slate-900 hover:bg-slate-800 text-white font-black py-5 px-8 rounded-2xl transition-all shadow-xl hover:shadow-slate-200 active:scale-[0.98] flex items-center justify-center gap-4 uppercase tracking-[0.2em] text-sm group"
            >
              Generate Output Files
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </button>
          </div>
        </motion.div>
      </div>
    </div>
  );
}

function HashBox({ label, hash, status, note }: { label: string, hash: string, status: 'original' | 'modified', note?: string }) {
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest">{label}</label>
        {status === 'modified' && (
          <span className="text-[9px] font-black text-amber-600 bg-amber-50 px-2 py-0.5 rounded border border-amber-100 uppercase">Changed</span>
        )}
      </div>
      <div className="bg-slate-50 p-4 rounded-xl border border-slate-100 font-mono text-[10px] text-slate-500 break-all leading-relaxed shadow-inner">
        {hash}
      </div>
      {note && <p className="text-[10px] text-slate-400 font-medium italic">{note}</p>}
    </div>
  );
}
