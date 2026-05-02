import React, { useState } from 'react';
import { AppState, ReferenceEntry } from '../../types';
import { CheckCircle2, AlertCircle, Info, BookMarked, Edit3, List } from 'lucide-react';
import { motion } from 'framer-motion';

export function VerifyStep({ state, updateState, onNext }: { state: AppState, updateState: (s: Partial<AppState>) => void, onNext: () => void }) {
  const handleMetadataChange = (field: keyof AppState['metadata'], value: string) => {
    updateState({
      metadata: {
        ...state.metadata,
        [field]: value
      }
    });
  };

  const confidence = state.metadata.confidence || 0;
  const confidenceColor = confidence > 80 ? 'text-emerald-600' : confidence > 50 ? 'text-amber-500' : 'text-red-500';
  const barColor = confidence > 80 ? 'from-emerald-400 to-emerald-600' : confidence > 50 ? 'from-amber-400 to-amber-600' : 'from-red-400 to-red-600';

  const refList: ReferenceEntry[] = state.metadata.references_list || [];

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
            <h3 className="font-bold text-slate-800 uppercase tracking-wider text-sm">Raw Text Feed</h3>
          </div>
          <div className="flex items-center gap-2 text-xs font-bold text-slate-400 bg-slate-200/50 px-3 py-1 rounded-full">
            <Info className="w-3 h-3" />
            READ-ONLY STREAM
          </div>
        </div>
        <div className="p-8 flex-1 overflow-y-auto bg-slate-50/30 font-mono text-sm text-slate-600 leading-relaxed selection:bg-amber-100">
          <pre className="whitespace-pre-wrap">{state.rawText}</pre>
        </div>
      </motion.div>

      {/* Right Column: Tag Review */}
      <motion.div
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        className="flex flex-col gap-6 overflow-y-auto pr-2 custom-scrollbar"
      >
        {/* AI Confidence Score */}
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
            {confidence > 80
              ? <CheckCircle2 className="w-4 h-4 text-emerald-500 flex-shrink-0" />
              : <AlertCircle className="w-4 h-4 text-amber-500 flex-shrink-0" />}
            {confidence > 80
              ? "Structural parsing complete. High confidence in entity extraction. Please verify tags below."
              : "AI confidence is lower than optimal. Please carefully review extracted tags below."}
          </p>
        </div>

        {/* Tag Review */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 flex-1 flex flex-col">
          <h3 className="font-bold text-slate-900 text-sm uppercase tracking-tight mb-6 flex items-center gap-2">
            Tag Review
            <span className="text-[10px] font-bold text-amber-600 bg-amber-50 px-2 py-0.5 rounded border border-amber-100">EDITABLE</span>
          </h3>

          <div className="space-y-6 flex-1 overflow-y-auto pr-2 custom-scrollbar">
            <Field label="Title"    value={state.metadata.title}    onChange={(v) => handleMetadataChange('title', v)}    rows={2} />
            <Field label="Authors"  value={state.metadata.authors}  onChange={(v) => handleMetadataChange('authors', v)}  rows={1} />
            <Field label="Abstract" value={state.metadata.abstract} onChange={(v) => handleMetadataChange('abstract', v)} rows={5} />
            <Field label="Headings" value={state.metadata.headings} onChange={(v) => handleMetadataChange('headings', v)} rows={4} />

            {/* Rich References Verification Panel */}
            <ReferencesPanel
              refText={state.metadata.references}
              refList={refList}
              onChangeText={(v) => handleMetadataChange('references', v)}
              onChangeList={(v: ReferenceEntry[]) => handleMetadataChange('references_list', v as any)}
            />
          </div>

          <div className="mt-8 pt-6 border-t border-slate-100">
            <button
              onClick={onNext}
              className="w-full bg-[#ffc107] hover:bg-amber-500 text-slate-900 font-black py-4 px-6 rounded-xl transition-all shadow-lg hover:shadow-amber-100 active:scale-[0.98] flex items-center justify-center gap-3 uppercase tracking-widest text-sm"
            >
              Confirm Structure &amp; Next Step
            </button>
          </div>
        </div>
      </motion.div>
    </div>
  );
}

// ── Plain textarea field ──────────────────────────────────────────────────────
function Field({ label, value, onChange, rows }: { label: string; value: string; onChange: (v: string) => void; rows: number }) {
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

// ── Rich references verification panel ───────────────────────────────────────
function ReferencesPanel({
  refText,
  refList,
  onChangeText,
  onChangeList,
}: {
  refText: string;
  refList: ReferenceEntry[];
  onChangeText: (v: string) => void;
  onChangeList: (v: ReferenceEntry[]) => void;
}) {
  const [showRaw, setShowRaw] = useState(false);
  const [verifying, setVerifying] = useState<Record<number, boolean>>({});
  const [crossrefResults, setCrossrefResults] = useState<Record<number, any>>({});

  /** A reference is "good" if it has a year and is long enough to be real. */
  const getHealth = (text: string): 'good' | 'warn' => {
    const hasYear = /\b(19|20)\d{2}\b/.test(text);
    const isSubstantial = text.length > 40;
    return hasYear && isSubstantial ? 'good' : 'warn';
  };

  const handleVerify = async (ref: ReferenceEntry) => {
    setVerifying(prev => ({ ...prev, [ref.number]: true }));
    try {
      // Use window.location.hostname if needed, or fallback to localhost
      const baseUrl = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' 
        ? 'http://localhost:8000' 
        : '';
      const response = await fetch(`${baseUrl}/api/verify-citation`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ citation: ref.text })
      });
      const data = await response.json();
      setCrossrefResults(prev => ({ ...prev, [ref.number]: data }));
    } catch (err) {
      console.error(err);
      setCrossrefResults(prev => ({ ...prev, [ref.number]: { error: 'Network error fetching Crossref.' } }));
    } finally {
      setVerifying(prev => ({ ...prev, [ref.number]: false }));
    }
  };

  const handleAcceptCrossref = (ref: ReferenceEntry, data: any) => {
    const formatted = `${data.author || 'Unknown'}. ${data.title || 'Unknown'}. DOI: ${data.doi || ''}`;
    
    // Update the parsed list
    const newList = refList.map(r => r.number === ref.number ? { ...r, text: formatted } : r);
    onChangeList(newList);

    // Update the raw text blob
    const newRefText = refText.replace(ref.text, formatted);
    onChangeText(newRefText);

    // Clear result
    setCrossrefResults(prev => {
      const next = { ...prev };
      delete next[ref.number];
      return next;
    });
  };

  const goodCount = refList.filter((r) => getHealth(r.text) === 'good').length;
  const warnCount = refList.length - goodCount;
  const notFound = refList.length === 0;

  return (
    <div className="group">
      {/* Header row */}
      <div className="flex items-center justify-between mb-2">
        <label className="block text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] group-focus-within:text-amber-600 transition-colors flex items-center gap-1.5">
          <BookMarked className="w-3 h-3" />
          References
        </label>
        <div className="flex items-center gap-2">
          {refList.length > 0 && (
            <span className="text-[10px] font-black text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
              {refList.length} detected
            </span>
          )}
          {warnCount > 0 && (
            <span className="text-[10px] font-black text-amber-700 bg-amber-50 px-2 py-0.5 rounded-full border border-amber-200">
              {warnCount} flagged
            </span>
          )}
          <button
            type="button"
            onClick={() => setShowRaw((p) => !p)}
            className="flex items-center gap-1 text-[10px] font-bold text-slate-400 hover:text-amber-600 transition-colors"
          >
            {showRaw ? <List className="w-3 h-3" /> : <Edit3 className="w-3 h-3" />}
            {showRaw ? 'List View' : 'Edit Raw'}
          </button>
        </div>
      </div>

      {/* Raw edit mode */}
      {showRaw ? (
        <textarea
          value={refText}
          onChange={(e) => onChangeText(e.target.value)}
          rows={6}
          className="w-full text-sm border border-slate-200 rounded-xl p-4 focus:ring-4 focus:ring-amber-400/10 focus:border-amber-400 outline-none transition-all resize-none bg-slate-50/50 focus:bg-white text-slate-700 font-mono text-xs leading-relaxed"
          placeholder="Paste references here..."
        />
      ) : notFound ? (
        /* No references found */
        <div className="border-2 border-dashed border-red-200 bg-red-50/60 rounded-xl p-6 text-center">
          <div className="text-2xl mb-2">⚠️</div>
          <p className="text-xs font-black text-red-600 mb-1">No references detected</p>
          <p className="text-[10px] text-red-400 mb-4 leading-relaxed">
            The system couldn't find a References section.<br />Make sure your document has a "References" heading.
          </p>
          <button
            type="button"
            onClick={() => setShowRaw(true)}
            className="text-[10px] font-black text-amber-700 bg-amber-100 hover:bg-amber-200 px-3 py-1.5 rounded-lg transition-colors"
          >
            Add References Manually →
          </button>
        </div>
      ) : (
        /* List view */
        <div className="border border-slate-200 rounded-xl overflow-hidden shadow-sm">
          {/* Panel header */}
          <div className="bg-slate-50 px-3 py-2.5 border-b border-slate-200 flex items-center justify-between">
            <span className="text-[10px] font-black text-slate-500 uppercase tracking-wider flex items-center gap-1.5">
              <CheckCircle2 className="w-3 h-3 text-emerald-500" />
              Reference Verification
            </span>
            <span className="text-[10px] text-slate-400 font-bold">
              {goodCount}/{refList.length} verified ✓
            </span>
          </div>

          {/* Scrollable reference cards */}
          <div className="max-h-56 overflow-y-auto divide-y divide-slate-100 custom-scrollbar">
            {refList.map((ref) => {
              const health = getHealth(ref.text);
              const isVerifying = verifying[ref.number];
              const crResult = crossrefResults[ref.number];

              return (
                <div
                  key={ref.number}
                  className={`flex flex-col gap-2 px-3 py-2.5 transition-colors hover:bg-slate-50 ${
                    health === 'warn' ? 'bg-amber-50/50' : ''
                  }`}
                >
                  <div className="flex items-start gap-3">
                    {/* Number badge */}
                    <span
                      className={`text-[10px] font-black shrink-0 px-1.5 py-0.5 rounded mt-0.5 ${
                        health === 'good'
                          ? 'bg-emerald-100 text-emerald-700'
                          : 'bg-amber-100 text-amber-700'
                      }`}
                    >
                      [{ref.number}]
                    </span>

                    {/* Reference text */}
                    <p className="text-[11px] text-slate-700 leading-relaxed flex-1 min-w-0">
                      {ref.text}
                    </p>

                    {/* Status icon / Verify Button */}
                    <div className="shrink-0 flex items-center gap-2 mt-0.5">
                      {health === 'warn' && !crResult && (
                        <button
                          type="button"
                          onClick={() => handleVerify(ref)}
                          disabled={isVerifying}
                          className="text-[10px] font-bold bg-indigo-50 text-indigo-700 border border-indigo-200 px-2 py-0.5 rounded hover:bg-indigo-100 disabled:opacity-50 transition-colors whitespace-nowrap"
                        >
                          {isVerifying ? 'Verifying...' : 'Verify via Crossref'}
                        </button>
                      )}
                      <span className="text-xs" title={health === 'good' ? 'Looks complete' : 'May be missing year or too short'}>
                        {health === 'good' ? '✓' : '⚠'}
                      </span>
                    </div>
                  </div>

                  {/* Crossref Side-by-Side Comparison UI */}
                  {crResult && (
                    <div className="mt-2 p-3 bg-indigo-50/50 rounded-lg border border-indigo-100 text-[10px]">
                      {crResult.error ? (
                        <div className="text-red-600 font-bold">Error: {crResult.error}</div>
                      ) : (
                        <div className="space-y-3">
                          <div className="flex items-center justify-between border-b border-indigo-100 pb-2 mb-2">
                            <span className="font-bold text-indigo-900 flex items-center gap-1">
                              <BookMarked className="w-3 h-3" />
                              Crossref Match Found
                            </span>
                          </div>
                          
                          <div className="grid grid-cols-2 gap-4">
                            <div>
                              <div className="text-[9px] font-bold text-slate-400 uppercase tracking-widest mb-1">Original Parse</div>
                              <div className="text-slate-600 font-mono leading-relaxed bg-white p-2 rounded border border-slate-200">
                                {ref.text}
                              </div>
                            </div>
                            
                            <div>
                              <div className="text-[9px] font-bold text-indigo-400 uppercase tracking-widest mb-1">Crossref Data</div>
                              <div className="space-y-1.5 bg-white p-2 rounded border border-indigo-200">
                                <div><span className="font-bold text-indigo-900">Title:</span> <span className="text-indigo-800">{crResult.title}</span></div>
                                <div><span className="font-bold text-indigo-900">Author:</span> <span className="text-indigo-800">{crResult.author}</span></div>
                                <div><span className="font-bold text-indigo-900">DOI:</span> <a href={crResult.url} target="_blank" rel="noreferrer" className="text-blue-600 hover:underline">{crResult.doi}</a></div>
                              </div>
                            </div>
                          </div>

                          <div className="flex justify-end pt-2">
                            <button
                              type="button"
                              onClick={() => handleAcceptCrossref(ref, crResult)}
                              className="bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-1.5 px-3 rounded shadow-sm transition-colors"
                            >
                              Accept Crossref Format
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Footer summary */}
          {warnCount > 0 && (
            <div className="bg-amber-50 border-t border-amber-100 px-3 py-2">
              <p className="text-[10px] text-amber-700 font-bold">
                ⚠ {warnCount} reference{warnCount > 1 ? 's' : ''} may be incomplete (missing year or too short).
                Use <button type="button" onClick={() => setShowRaw(true)} className="underline hover:text-amber-900">Edit Raw</button> or verify via Crossref.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}