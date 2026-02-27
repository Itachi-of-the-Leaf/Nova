/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import { AppState } from './types';
import { StepTracker } from './components/StepTracker';
import { UploadStep } from './components/steps/UploadStep';
import { VerifyStep } from './components/steps/VerifyStep';
import { ComplianceStep } from './components/steps/ComplianceStep';
import { FinalizeStep } from './components/steps/FinalizeStep';
import { DownloadStep } from './components/steps/DownloadStep';
import { AnimatePresence, motion } from 'motion/react';

const INITIAL_STATE: AppState = {
  step: 1,
  rawText: '',
  metadata: {
    title: '',
    authors: '',
    abstract: '',
    headings: '',
    references: [],
  },
  lexicalHashOriginal: '',
  lexicalHashFinal: '',
  semanticHashScore: 0,
};

export default function App() {
  const [state, setState] = useState<AppState>(INITIAL_STATE);

  const updateState = (updates: Partial<AppState>) => {
    setState((prev) => ({ ...prev, ...updates }));
  };

  const nextStep = () => {
    setState((prev) => ({ ...prev, step: (prev.step + 1) as any }));
  };

  const resetApp = () => {
    setState(INITIAL_STATE);
  };

  const renderStep = () => {
    switch (state.step) {
      case 1:
        return <UploadStep onNext={(data) => {
          updateState({ ...data, step: 2 });
        }} />;
      case 2:
        return <VerifyStep state={state} updateState={updateState} onNext={nextStep} />;
      case 3:
        return <ComplianceStep state={state} updateState={updateState} onNext={nextStep} />;
      case 4:
        return <FinalizeStep state={state} onNext={nextStep} />;
      case 5:
        return <DownloadStep state={state} onReset={resetApp} />;
      default:
        return <UploadStep onNext={nextStep} />;
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <StepTracker currentStep={state.step} />

      <main className="flex-1 container mx-auto px-4 py-8">
        <AnimatePresence mode="wait">
          <motion.div
            key={state.step}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.3, ease: "easeInOut" }}
            className="h-full"
          >
            {renderStep()}
          </motion.div>
        </AnimatePresence>
      </main>

      {/* Footer Branding */}
      <footer className="py-6 px-8 border-t border-slate-200 bg-white flex justify-between items-center">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 bg-slate-900 rounded-md flex items-center justify-center">
            <span className="text-[10px] font-black text-amber-400">N</span>
          </div>
          <span className="text-xs font-black text-slate-900 uppercase tracking-tighter">N.O.V.A. System</span>
        </div>
        <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">
          &copy; 2026 Normalized Optimization & Verification Assistant
        </div>
        <div className="flex gap-4">
          <div className="w-2 h-2 rounded-full bg-emerald-500"></div>
          <div className="w-2 h-2 rounded-full bg-emerald-500"></div>
          <div className="w-2 h-2 rounded-full bg-emerald-500"></div>
        </div>
      </footer>
    </div>
  );
}
