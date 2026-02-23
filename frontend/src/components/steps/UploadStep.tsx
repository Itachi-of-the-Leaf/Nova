import React, { useState, useRef } from 'react';
import { UploadCloud, Shield, FileSearch, Fingerprint } from 'lucide-react';
import { motion } from 'framer-motion'; // Changed from 'motion/react' to standard framer-motion

export function UploadStep({ onNext }: { onNext: (data: any) => void }) {
  const [isUploading, setIsUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('');
  
  // This reference connects to our hidden file input
  const fileInputRef = useRef<HTMLInputElement>(null);

  // This function runs when you actually select a file
  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    setStatus('Unpacking document & sending to AI Engine...');
    setProgress(20);

    try {
      // 1. Package the file to send
      const formData = new FormData();
      formData.append('file', file);

      // 2. Send it to the Python Backend (The Bridge!)
      setStatus('AI Parsing & Calculating Hashes...');
      setProgress(50);
      
      const response = await fetch('http://127.0.0.1:8000/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Server responded with ${response.status}`);
      }

      // 3. Receive the REAL data back from Python
      const data = await response.json();
      setProgress(100);
      setStatus('Extraction Complete!');

      // 4. Move to Step 2 with the REAL data
      setTimeout(() => {
        onNext({
          rawText: data.raw_text,
          metadata: data.metadata,
          lexicalHashOriginal: data.lexical_hash,
          fileName: file.name
        });
      }, 1000);

    } catch (error) {
      console.error("Upload Error:", error);
      setStatus('Error connecting to backend!');
      setIsUploading(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto py-12 px-4">
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-16"
      >
        <div className="inline-block px-4 py-1.5 mb-6 rounded-full bg-amber-100 text-amber-800 text-xs font-bold uppercase tracking-widest border border-amber-200">
          Enterprise Grade Academic Tool
        </div>
        <h1 className="text-5xl font-black text-slate-900 tracking-tight mb-6">
          N.O.V.A. <span className="text-slate-400 font-light">Assistant</span>
        </h1>
        <p className="text-xl text-slate-600 max-w-2xl mx-auto leading-relaxed">
          The Normalized Optimization & Verification Assistant for high-stakes academic publishing.
        </p>
      </motion.div>

      {/* The Upload Box */}
      <motion.div 
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.2 }}
        className={`relative border-2 border-dashed rounded-3xl p-16 text-center transition-all duration-500 ${
          isUploading ? 'border-amber-400 bg-amber-50/30' : 'border-slate-200 hover:border-amber-400 hover:bg-slate-50 cursor-pointer group'
        }`}
        onClick={() => !isUploading && fileInputRef.current?.click()}
      >
        {/* HIDDEN INPUT THAT DOES THE REAL WORK */}
        <input 
          type="file" 
          ref={fileInputRef} 
          className="hidden" 
          accept=".docx" 
          onChange={handleFileUpload} 
        />

        {!isUploading ? (
          <div className="flex flex-col items-center">
            <div className="w-20 h-20 bg-slate-100 text-slate-400 rounded-2xl flex items-center justify-center mb-6 border border-slate-200 group-hover:bg-amber-100 group-hover:text-amber-600 group-hover:border-amber-200 transition-all duration-300 transform group-hover:rotate-3">
              <UploadCloud className="w-10 h-10" />
            </div>
            <h3 className="text-2xl font-bold text-slate-900 mb-2">Drop your manuscript here</h3>
            <p className="text-slate-500 mb-8 max-w-sm mx-auto">
              Securely upload your .docx file for structural analysis and cryptographic verification.
            </p>
            <button className="bg-slate-900 text-white px-8 py-3.5 rounded-xl font-bold hover:bg-slate-800 transition-all shadow-lg hover:shadow-slate-200 active:scale-95 pointer-events-none">
              Select Document
            </button>
          </div>
        ) : (
          <div className="flex flex-col items-center py-8">
            <div className="w-full max-w-md mb-8">
              <div className="flex justify-between text-sm font-bold text-slate-700 mb-3 uppercase tracking-wider">
                <span className="flex items-center gap-2">
                  <motion.div 
                    animate={{ rotate: 360 }}
                    transition={{ repeat: Infinity, duration: 2, ease: "linear" }}
                    className="w-4 h-4 border-2 border-amber-500 border-t-transparent rounded-full"
                  />
                  {status}
                </span>
                <span className="text-amber-600">{progress}%</span>
              </div>
              <div className="w-full bg-slate-200 rounded-full h-3 overflow-hidden shadow-inner">
                <motion.div 
                  className="bg-gradient-to-r from-amber-400 to-amber-600 h-full rounded-full"
                  initial={{ width: 0 }}
                  animate={{ width: `${progress}%` }}
                />
              </div>
            </div>
            <p className="text-slate-400 text-sm italic">Local privacy connection established...</p>
          </div>
        )}
      </motion.div>

      {/* Feature Cards Below */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-20">
        <FeatureCard icon={<Shield className="w-6 h-6 text-emerald-600" />} title="Privacy-First Local Processing" description="Your research never leaves your machine." />
        <FeatureCard icon={<FileSearch className="w-6 h-6 text-blue-600" />} title="Multi-Modal Structure Detection" description="Advanced AI detects headings and abstracts." />
        <FeatureCard icon={<Fingerprint className="w-6 h-6 text-purple-600" />} title="Cryptographic Integrity Proofs" description="Mathematical verification against hallucinations." />
      </div>
    </div>
  );
}

function FeatureCard({ icon, title, description }: { icon: React.ReactNode, title: string, description: string }) {
  return (
    <motion.div whileHover={{ y: -5 }} className="bg-white p-8 rounded-2xl border border-slate-100 shadow-sm hover:shadow-md transition-all duration-300">
      <div className="w-14 h-14 bg-slate-50 rounded-xl flex items-center justify-center mb-6 border border-slate-100">
        {icon}
      </div>
      <h4 className="text-xl font-bold text-slate-900 mb-3">{title}</h4>
      <p className="text-slate-500 text-sm leading-relaxed">{description}</p>
    </motion.div>
  );
}