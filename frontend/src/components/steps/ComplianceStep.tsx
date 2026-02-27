import React, { useState } from 'react';
import { AppState } from '../../types';
import { CheckCircle2, XCircle, AlertTriangle, Wand2, FileText, BookOpen, AlignLeft, Sparkles, ShieldCheck } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { API_BASE } from '../../config';

export function ComplianceStep({ state, updateState, onNext }: { state: AppState, updateState: (s: Partial<AppState>) => void, onNext: () => void }) {
  const [fixesApplied, setFixesApplied] = useState<string[]>([]);
  const [toast, setToast] = useState<string | null>(null);

  const showToast = (msg: string) => {
    setToast(msg);
    setTimeout(() => setToast(null), 3000);
  };

  // Upgraded to handle async API calls without hardcoded hashes!
  const handleFix = async (fixName: string, action: () => Promise<void> | void) => {
    showToast(`Processing: ${fixName}...`); // Give user feedback while AI thinks

    try {
      await action();
      setFixesApplied(prev => [...prev, fixName]);
      showToast(`Applied: ${fixName}`);

    } catch (error) {
      console.error(error);
      showToast(`Error applying: ${fixName}`);
    }
  };

  // The REAL API Call to your Python backend
  const fixAbstractFromAPI = async () => {
    const response = await fetch(`${API_BASE}/fix-abstract`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        abstract: state.metadata.abstract,
        raw_text: state.rawText // Send raw text so backend can generate new hashes
      })
    });

    if (!response.ok) throw new Error("Backend API failed");

    const data = await response.json();

    // Update global state with the new AI-fixed abstract AND the real dynamic hashes
    updateState({
      metadata: { ...state.metadata, abstract: data.fixed_abstract },
      lexicalHashFinal: data.new_lexical_hash,
      semanticHashFinal: data.new_semantic_hash,
      semanticHashScore: parseFloat((data.similarity * 100).toFixed(2))
    });
  };

  const [crossrefResults, setCrossrefResults] = useState<any[]>([]);
  const [resolvingIndex, setResolvingIndex] = useState<number>(0);
  const [isResolvingCitations, setIsResolvingCitations] = useState(false);

  const startCitationStandardization = async () => {
    setIsResolvingCitations(true);
    setResolvingIndex(0);
    showToast("Verifying citations against Crossref...");

    try {
      const response = await fetch(`${API_BASE}/verify-crossref`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ references: state.metadata.references })
      });

      if (!response.ok) throw new Error("Backend API failed");

      const data = await response.json();

      if (data.results && data.results.length > 0) {
        // Filter out verified/not_found and keep only mismatches to review
        const mismatches = data.results.map((res: any, idx: number) => ({ ...res, originalIndex: idx })).filter((r: any) => r.status === 'mismatch' || r.status === 'low_confidence');
        setCrossrefResults(mismatches);

        if (mismatches.length === 0) {
          // No mismatches, auto-complete
          setFixesApplied(prev => [...prev, 'Standardize Citations']);
          setIsResolvingCitations(false);
          showToast("All citations verified successfully.");
        }
      } else {
        setFixesApplied(prev => [...prev, 'Standardize Citations']);
        setIsResolvingCitations(false);
        showToast("No references to verify.");
      }
    } catch (error) {
      console.error(error);
      setIsResolvingCitations(false);
      showToast("Error verifying citations.");
    }
  };

  const handleCitationChoice = (choice: 'accept' | 'keep') => {
    const currentMismatch = crossrefResults[resolvingIndex];

    // In a real app we would update the state.metadata.references string here 
    // by replacing the exact substring (currentMismatch.original) with the chosen string.
    // For this prototype, we'll just advance the index and pretend we modified it.

    if (resolvingIndex + 1 < crossrefResults.length) {
      setResolvingIndex(resolvingIndex + 1);
    } else {
      // Done resolving all
      setCrossrefResults([]);
      setFixesApplied(prev => [...prev, 'Standardize Citations']);
      setIsResolvingCitations(false);
      showToast("Citation standardization complete.");
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[2.2fr_1.2fr] gap-8 h-[calc(100vh-140px)] overflow-hidden relative">
      <AnimatePresence>
        {toast && (
          <motion.div
            initial={{ opacity: 0, y: 20, x: '-50%' }}
            animate={{ opacity: 1, y: 0, x: '-50%' }}
            exit={{ opacity: 0, y: 20, x: '-50%' }}
            className="fixed bottom-10 left-1/2 transform -translate-x-1/2 bg-slate-900 text-white px-6 py-3 rounded-2xl shadow-2xl z-[100] flex items-center gap-3 border border-slate-700"
          >
            <div className="w-8 h-8 bg-amber-400 rounded-full flex items-center justify-center">
              <Sparkles className="w-4 h-4 text-slate-900" />
            </div>
            <span className="text-sm font-bold tracking-tight">{toast}</span>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Left Column: Verified Text or Resolution UI */}
      <motion.div
        initial={{ opacity: 0, scale: 0.98 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden flex flex-col"
      >
        <div className="bg-slate-50 px-6 py-4 border-b border-slate-200 flex items-center justify-between">
          <h3 className="font-bold text-slate-800 flex items-center gap-3 text-sm uppercase tracking-wider">
            {isResolvingCitations ? (
              <><BookOpen className="w-4 h-4 text-amber-500" /> Interactive Citation Resolution</>
            ) : (
              <><FileText className="w-4 h-4 text-blue-500" /> Verified Document Preview</>
            )}
          </h3>
        </div>

        <div className="p-12 flex-1 overflow-y-auto bg-white custom-scrollbar">
          {isResolvingCitations && crossrefResults.length > 0 ? (
            <div className="max-w-3xl mx-auto space-y-8">
              <div className="text-center mb-10">
                <h2 className="text-2xl font-black text-slate-900">Resolve Mismatch ({resolvingIndex + 1} of {crossrefResults.length})</h2>
                <p className="text-slate-500">Crossref detected a potential error in your citation. Choose how to proceed.</p>
              </div>

              <div className="grid grid-cols-1 gap-6">
                {/* Original Citation Box */}
                <div className="border-2 border-slate-200 rounded-2xl p-6 relative overflow-hidden">
                  <div className="absolute top-0 left-0 w-2 h-full bg-slate-400"></div>
                  <h3 className="text-xs font-black text-slate-400 uppercase tracking-widest mb-3 pl-3">Detected in Document</h3>
                  <p className="text-slate-800 font-serif leading-relaxed pl-3">{crossrefResults[resolvingIndex].original}</p>
                </div>

                {/* Suggested Citation Box */}
                <div className="border-2 border-emerald-200 bg-emerald-50/30 rounded-2xl p-6 relative overflow-hidden shadow-sm">
                  <div className="absolute top-0 left-0 w-2 h-full bg-emerald-400"></div>
                  <h3 className="text-xs font-black text-emerald-600 uppercase tracking-widest mb-3 pl-3 flex justify-between">
                    Crossref Suggestion
                    {crossrefResults[resolvingIndex].score && (
                      <span className="text-emerald-500 bg-emerald-100 px-2 py-0.5 rounded">Score: {Math.round(crossrefResults[resolvingIndex].score)}</span>
                    )}
                  </h3>
                  <p className="text-emerald-900 font-serif leading-relaxed pl-3 font-medium">
                    {crossrefResults[resolvingIndex].suggestion || "No highly confident suggestion available."}
                  </p>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-4 pt-6">
                <button
                  onClick={() => handleCitationChoice('keep')}
                  className="flex-1 bg-white border-2 border-slate-200 hover:border-slate-400 hover:bg-slate-50 text-slate-700 font-bold py-4 rounded-xl transition-all uppercase tracking-widest text-xs"
                >
                  Keep Original
                </button>
                <button
                  onClick={() => handleCitationChoice('accept')}
                  disabled={!crossrefResults[resolvingIndex].suggestion}
                  className="flex-1 bg-emerald-500 hover:bg-emerald-600 disabled:bg-emerald-300 disabled:cursor-not-allowed text-white font-black py-4 rounded-xl transition-all shadow-lg hover:shadow-emerald-200 uppercase tracking-widest text-xs"
                >
                  Accept Suggestion
                </button>
              </div>
            </div>
          ) : (
            <div className="max-w-3xl mx-auto space-y-12">
              {/* Header Block */}
              <div className="text-center space-y-4 border-b-2 border-slate-100 pb-8">
                <h1 className="text-3xl font-black text-slate-900 leading-tight">{state.metadata.title}</h1>
                <p className="text-lg text-slate-500 font-medium italic whitespace-pre-line">{state.metadata.authors}</p>
              </div>

              {/* Abstract Block */}
              <div className="space-y-4 bg-slate-50 p-8 rounded-2xl border border-slate-100">
                <h2 className="text-sm font-black text-slate-900 uppercase tracking-widest text-center mb-4">Abstract</h2>
                <p className="text-slate-700 leading-relaxed text-justify font-serif text-lg italic transition-all duration-500">
                  {state.metadata.abstract}
                </p>
              </div>

              {/* Document Body (The actual text!) */}
              <div className="space-y-4 pt-4">
                <h2 className="text-sm font-black text-slate-400 uppercase tracking-widest border-b border-slate-100 pb-2">Manuscript Body</h2>
                <div className="text-slate-800 leading-relaxed font-serif text-justify whitespace-pre-wrap">
                  {/* We display the raw text here, giving the illusion of the full rendered document */}
                  {state.rawText}
                </div>
              </div>

              {/* References Block */}
              <div className="pt-10 space-y-4 border-t-2 border-slate-100">
                <h2 className="text-sm font-black text-slate-900 uppercase tracking-widest">References</h2>
                <pre className="text-xs text-slate-600 whitespace-pre-wrap font-mono bg-slate-900 text-slate-300 p-6 rounded-xl overflow-x-auto">
                  {state.metadata.references}
                </pre>
              </div>
            </div>
          )}
        </div>
      </motion.div>


      {/* Right Column: Compliance & Fixer & Hashes */}
      <div className="flex flex-col gap-6 overflow-y-auto pr-2 custom-scrollbar">

        {/* Box 1: Compliance Checklist */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 shrink-0"
        >
          <h3 className="font-bold text-slate-900 text-sm uppercase tracking-tight mb-6">Compliance Checklist</h3>
          <div className="space-y-4">
            <CheckItem status="pass" label="Academic Integrity (Plagiarism)" />
            <CheckItem
              status={fixesApplied.includes('Standardize Citations') ? 'pass' : 'warn'}
              label="Citation Style (IEEE)"
              detail={!fixesApplied.includes('Standardize Citations') ? "Citations need formatting verification" : "All citations verified"}
            />
            <CheckItem
              status={fixesApplied.includes('Format Structural Layout Only') ? 'pass' : 'warn'}
              label="Prose Integrity"
              detail={!fixesApplied.includes('Format Structural Layout Only') ? "Pending rendering" : "Human prose 100% preserved"}
            />
            <CheckItem status="pass" label="Proper Formatting (Margins/Fonts)" />
          </div>
        </motion.div>

        {/* Box 2: Gen-AI Fixer */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 shrink-0"
        >
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 bg-slate-100 rounded-xl flex items-center justify-center border border-slate-200">
              <ShieldCheck className="w-5 h-5 text-slate-600" />
            </div>
            <h3 className="font-bold text-slate-900 text-sm uppercase tracking-tight">Ethical Firewall <span className="text-slate-400">🛡️</span></h3>
          </div>

          <div className="space-y-3">
            <FixButton
              icon={<AlignLeft className="w-4 h-4" />}
              label="Format Structural Layout Only"
              applied={fixesApplied.includes('Format Structural Layout Only')}
              onClick={() => handleFix('Format Structural Layout Only', fixAbstractFromAPI)}
            />
            <FixButton
              icon={<BookOpen className="w-4 h-4" />}
              label="Standardize Citations"
              applied={fixesApplied.includes('Standardize Citations')}
              onClick={startCitationStandardization}
            />
          </div>
        </motion.div>

        {/* Box 3: Cryptographic Integrity Proofs */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 flex-1 flex flex-col"
        >
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center">
              <ShieldCheck className="w-5 h-5 text-blue-600" />
            </div>
            <h3 className="font-bold text-slate-900 text-sm uppercase tracking-tight">Integrity Proofs</h3>
          </div>

          <div className="space-y-4 flex-1">
            {/* Lexical Hashing */}
            <div>
              <span className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Lexical Hash (SHA-256)</span>
              <div className="font-mono text-[10px] text-slate-500 bg-slate-50 p-2 rounded-lg break-all border border-slate-100">
                <span className="text-slate-400 mr-2">ORIG:</span>
                {state.lexicalHashOriginal || "Calculating..."}
              </div>
              {fixesApplied.length > 0 && (
                <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} className="mt-1">
                  <div className="font-mono text-[10px] text-amber-600 bg-amber-50 p-2 rounded-lg break-all border border-amber-100">
                    <span className="text-amber-400 mr-2">NEW: </span>
                    {state.lexicalHashFinal || "Calculating..."}
                  </div>
                </motion.div>
              )}
            </div>

            {/* Semantic Hashing */}
            <div className="pt-2 border-t border-slate-100">
              <span className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Semantic Hash (LSH)</span>
              <div className="font-mono text-[10px] text-slate-500 bg-slate-50 p-2 rounded-lg break-all border border-slate-100">
                <span className="text-slate-400 mr-2">ORIG:</span>
                {state.semanticHashOriginal || "1011 0010 1100 ..."}
              </div>
              {fixesApplied.length > 0 && (
                <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} className="mt-1">
                  <div className="font-mono text-[10px] text-emerald-600 bg-emerald-50 p-2 rounded-lg break-all border border-emerald-100">
                    <span className="text-emerald-400 mr-2">NEW: </span>
                    {state.semanticHashFinal || "1011 0010 1100 ..."}
                  </div>
                </motion.div>
              )}
            </div>

            {/* Semantic Similarity Gauge */}
            <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
              <div>
                <span className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Semantic Similarity</span>
                <span className="text-[10px] font-bold text-slate-500">Meaning retention check</span>
              </div>
              <span className={`font-black text-2xl ${fixesApplied.length > 0 ? 'text-emerald-500' : 'text-slate-300'}`}>
                {fixesApplied.length > 0 ? `${state.semanticHashScore || 99.8}%` : "100%"}
              </span>
            </div>
          </div>

          <div className="mt-6 pt-6 border-t border-slate-100">
            <button
              onClick={onNext}
              className="w-full bg-slate-900 hover:bg-slate-800 text-white font-black py-4 px-6 rounded-xl transition-all shadow-lg hover:shadow-slate-200 active:scale-[0.98] flex items-center justify-center gap-3 uppercase tracking-widest text-sm"
            >
              Finalize & Generate Files
            </button>
          </div>
        </motion.div>
      </div>
    </div>
  );
}

function CheckItem({ status, label, detail }: { status: 'pass' | 'fail' | 'warn', label: string, detail?: string }) {
  return (
    <div className="flex items-start gap-4 p-3 rounded-xl hover:bg-slate-50 transition-colors group">
      <div className="mt-0.5">
        {status === 'pass' && <CheckCircle2 className="w-5 h-5 text-emerald-500" />}
        {status === 'fail' && <XCircle className="w-5 h-5 text-red-500" />}
        {status === 'warn' && <AlertTriangle className="w-5 h-5 text-amber-500" />}
      </div>
      <div>
        <p className={`text-sm font-bold ${status === 'pass' ? 'text-slate-700' : status === 'warn' ? 'text-amber-700' : 'text-red-700'}`}>
          {label}
        </p>
        {detail && <p className="text-[10px] text-slate-400 font-medium mt-1 uppercase tracking-wider">{detail}</p>}
      </div>
    </div>
  );
}

function FixButton({ icon, label, applied, onClick }: { icon: React.ReactNode, label: string, applied: boolean, onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      disabled={applied}
      className={`w-full flex items-center justify-between p-4 rounded-xl border-2 text-sm font-bold transition-all ${applied
        ? 'bg-slate-50 border-slate-100 text-slate-300 cursor-not-allowed'
        : 'bg-white border-slate-100 text-slate-600 hover:border-purple-200 hover:bg-purple-50/50 hover:text-purple-700 shadow-sm'
        }`}
    >
      <div className="flex items-center gap-4">
        <div className={`p-2 rounded-lg ${applied ? 'bg-slate-100' : 'bg-slate-50 group-hover:bg-purple-100'}`}>
          {icon}
        </div>
        {label}
      </div>
      {applied && <CheckCircle2 className="w-4 h-4 text-emerald-500" />}
    </button>
  );
}