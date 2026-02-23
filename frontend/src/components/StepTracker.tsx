import React from 'react';
import { ChevronRight } from 'lucide-react';

const STEPS = [
  { id: 1, label: 'Upload' },
  { id: 2, label: 'Verify Structure' },
  { id: 3, label: 'Compliance Check' },
  { id: 4, label: 'Finalize & Proofs' },
  { id: 5, label: 'Download' },
];

export function StepTracker({ currentStep }: { currentStep: number }) {
  return (
    <nav className="flex overflow-x-auto py-4 px-6 bg-slate-900 border-b border-slate-800 scrollbar-hide sticky top-0 z-50" aria-label="Breadcrumb">
      <ol role="list" className="flex items-center space-x-2 sm:space-x-4 mx-auto">
        {STEPS.map((step, index) => {
          const isCurrent = step.id === currentStep;
          const isPast = step.id < currentStep;
          
          return (
            <li key={step.id} className="flex items-center">
              <div
                className={`flex items-center px-4 py-2 rounded-md text-sm font-bold transition-all duration-300 ${
                  isCurrent
                    ? 'bg-[#ffc107] text-slate-900 shadow-[0_0_15px_rgba(255,193,7,0.3)] scale-105'
                    : isPast
                    ? 'bg-slate-800 text-slate-300'
                    : 'bg-slate-800/40 text-slate-500'
                }`}
              >
                <span className="mr-2 opacity-60">{step.id}.</span>
                <span className="whitespace-nowrap uppercase tracking-wider">{step.label}</span>
              </div>
              {index !== STEPS.length - 1 && (
                <ChevronRight className="ml-2 sm:ml-4 h-4 w-4 text-slate-700 flex-shrink-0" />
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
