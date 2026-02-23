import React, { useState } from 'react';
import { AppState } from '../../types';
import { FileDown, CheckCircle2, RefreshCcw, FileText, ShieldCheck, FileCode, Loader2 } from 'lucide-react';
import { motion } from 'motion/react';
import { API_BASE } from '../../config';

// Added 'state' to the props so we can send the data to the backend
export function DownloadStep({ state, onReset }: { state: AppState, onReset: () => void }) {
  const [isDownloading, setIsDownloading] = useState(false);

  // Function to download the compiled IEEE PDF
  const handleDownloadPDF = async () => {
    setIsDownloading(true);
    try {
      const response = await fetch(`${API_BASE}/download/pdf`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          metadata: state.metadata,
          raw_text: state.rawText
        })
      });

      if (!response.ok) throw new Error("PDF generation failed");

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = "NOVA_Manuscript.pdf";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error("Download Error:", error);
      alert("Failed to generate PDF. Check the Python backend terminal for LaTeX errors.");
    } finally {
      setIsDownloading(false);
    }
  };

  // Function to download the Integrity Report
  const handleDownloadReport = async () => {
    setIsDownloading(true);
    try {
      const response = await fetch(`${API_BASE}/download/report`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          metadata: state.metadata,
          raw_text: state.rawText
        })
      });

      if (!response.ok) throw new Error("Report generation failed");

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = "NOVA_Integrity_Report.txt";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error("Report Error:", error);
      alert("Failed to generate Report.");
    } finally {
      setIsDownloading(false);
    }
  };

  // DOCX download is typically handled similarly, but we'll put a placeholder alert for now
  const handleDownloadDOCX = () => {
    alert("DOCX generator module initializing... This feature will use python-docx in the final version.");
  };

  return (
    <div className="max-w-4xl mx-auto py-20 px-4 text-center">
      <motion.div
        initial={{ opacity: 0, scale: 0.5 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ type: "spring", stiffness: 200, damping: 20 }}
        className="w-24 h-24 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center mx-auto mb-10 shadow-[0_0_40px_rgba(16,185,129,0.2)]"
      >
        <CheckCircle2 className="w-12 h-12" />
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        <h1 className="text-5xl font-black text-slate-900 mb-6 tracking-tight">Success! Your Files are Ready.</h1>
        <p className="text-xl text-slate-500 max-w-2xl mx-auto leading-relaxed mb-16">
          N.O.V.A. has finalized your academic manuscript. All cryptographic proofs have been bundled into the integrity report.
        </p>
      </motion.div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-20">
        <DownloadButton
          icon={<FileText className="w-6 h-6" />}
          label="Download IEEE PDF"
          color="bg-slate-900"
          delay={0.3}
          onClick={handleDownloadPDF}
          disabled={isDownloading}
        />
        <DownloadButton
          icon={<FileCode className="w-6 h-6" />}
          label="Download Compliant DOCX"
          color="bg-slate-900"
          delay={0.4}
          onClick={handleDownloadDOCX}
          disabled={isDownloading}
        />
        <DownloadButton
          icon={<ShieldCheck className="w-6 h-6" />}
          label="Download Integrity Report"
          color="bg-amber-500"
          delay={0.5}
          onClick={handleDownloadReport}
          disabled={isDownloading}
        />
      </div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.8 }}
      >
        <button
          onClick={onReset}
          className="inline-flex items-center gap-3 text-slate-400 hover:text-slate-900 font-bold uppercase tracking-widest text-xs transition-colors group"
        >
          <RefreshCcw className="w-4 h-4 group-hover:rotate-180 transition-transform duration-500" />
          Start New Session
        </button>
      </motion.div>
    </div>
  );
}

// Updated button component to handle clicks and loading states
function DownloadButton({ icon, label, color, delay, onClick, disabled }: { icon: React.ReactNode, label: string, color: string, delay: number, onClick: () => void, disabled: boolean }) {
  return (
    <motion.button
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay }}
      whileHover={{ y: disabled ? 0 : -5, scale: disabled ? 1 : 1.02 }}
      whileTap={{ scale: disabled ? 1 : 0.98 }}
      onClick={onClick}
      disabled={disabled}
      className={`${color} ${disabled ? 'opacity-70 cursor-not-allowed' : ''} text-white p-8 rounded-3xl shadow-xl flex flex-col items-center gap-4 transition-all hover:shadow-2xl`}
    >
      <div className="w-14 h-14 bg-white/10 rounded-2xl flex items-center justify-center mb-2">
        {disabled ? <Loader2 className="w-6 h-6 animate-spin" /> : icon}
      </div>
      <span className="font-black uppercase tracking-widest text-xs">{label}</span>
      <FileDown className="w-5 h-5 opacity-50" />
    </motion.button>
  );
}