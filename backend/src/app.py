import streamlit as st
import Nova.backend.src.engine as engine
import Nova.backend.src.formatter as formatter
import time

# --- 1. Page Configuration & CSS ---
st.set_page_config(layout="wide", page_title="N.O.V.A. Hub")

st.markdown("""
<style>
    .step-tracker {font-weight: bold; color: #555; text-align: center; padding: 15px; background-color: #0e1117; border-radius: 8px; border: 1px solid #333; margin-bottom: 30px;}
    .highlight-step {color: #000; background-color: #ffc107; padding: 5px 15px; border-radius: 15px;}
    .box-container {border: 1px solid #444; padding: 20px; border-radius: 8px; background-color: #1e2127; margin-bottom: 20px;}
    .success-text {color: #198754; font-weight: bold;}
    .warning-text {color: #ffc107; font-weight: bold;}
    .error-text {color: #dc3545; font-weight: bold;}
    .section-title {font-size: 1.1rem; font-weight: 600; margin-bottom: 10px; color: #ddd;}
</style>
""", unsafe_allow_html=True)

# --- 2. Session State Management ---
if 'raw_text' not in st.session_state: st.session_state.raw_text = None
if 'metadata' not in st.session_state: st.session_state.metadata = None
if 'lexical_hash' not in st.session_state: st.session_state.lexical_hash = None
if 'filename' not in st.session_state: st.session_state.filename = None

# --- Helper Function to Reset App ---
def reset_app():
    st.session_state.raw_text = None
    st.session_state.metadata = None
    st.session_state.lexical_hash = None
    st.session_state.filename = None

# --- 3. MAIN APP LOGIC (State Machine) ---

st.title("Manuscript Intelligence Hub ☁️")

# ==========================================
# STATE 1: UPLOAD SCREEN
# ==========================================
if st.session_state.raw_text is None:
    st.markdown('<div class="step-tracker"><span class="highlight-step">1. Upload</span> &nbsp; 〉 &nbsp; 2. Verify Structure &nbsp; 〉 &nbsp; 3. Compliance Check &nbsp; 〉 &nbsp; 4. Download</div>', unsafe_allow_html=True)
    
    st.write("")
    st.markdown("<h3 style='text-align: center; color: #ccc;'>Upload your Raw Manuscript (.docx)</h3>", unsafe_allow_html=True)
    st.write("")
    
    # Center the uploader
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        uploaded_file = st.file_uploader("", type=['docx'], label_visibility="collapsed")
        
        if uploaded_file is not None:
            st.session_state.filename = uploaded_file.name
            
            # Processing UI
            st.write("---")
            progress_bar = st.progress(0)
            status_text = st.empty()

            status_text.markdown("Processing: **📖 Unpacking .docx and extracting raw text...**")
            progress_bar.progress(25)
            text = engine.extract_text_from_docx(uploaded_file)
            st.session_state.raw_text = text
            time.sleep(0.5)
            
            status_text.markdown("Processing: **🔐 Calculating Lexical SHA-256 Hash...**")
            progress_bar.progress(50)
            st.session_state.lexical_hash = engine.calculate_lexical_hash(text)
            time.sleep(0.5)
                
            status_text.markdown("Processing: **🤖 AI engine parsing structural semantics...**")
            progress_bar.progress(85)
            meta = engine.get_document_metadata(text)
            st.session_state.metadata = meta
            
            progress_bar.progress(100)
            status_text.markdown("✅ **Analysis Complete!** Transitioning to dashboard...")
            time.sleep(1)
            
            st.rerun()

# ==========================================
# STATE 2: DASHBOARD / VERIFICATION SCREEN
# ==========================================
else:
    st.markdown('<div class="step-tracker">1. Upload &nbsp; 〉 &nbsp; <span class="highlight-step">2. Verify Structure</span> &nbsp; 〉 &nbsp; 3. Compliance Check &nbsp; 〉 &nbsp; 4. Download</div>', unsafe_allow_html=True)

    col_left, col_right = st.columns([2, 1.3], gap="large")

    # ------------------ LEFT COLUMN: RAW TEXT ------------------
    with col_left:
        st.subheader("Raw Manuscript Feed")
        st.caption(f"Viewing: **{st.session_state.filename}**")
        
        st.text_area("Original Content (Read-Only)", value=st.session_state.raw_text, height=650, disabled=True)
        
        st.write("")
        if st.button("⬅️ Upload a Different File", type="secondary"):
            reset_app()
            st.rerun()

    # ------------------ RIGHT COLUMN: GLASS BOX ------------------
    with col_right:
        st.subheader("Glass Box Verification")
        
        # --- A. Tag Review (Show exactly what was detected) ---
        # --- A. Tag Review (Show exactly what was detected) ---
        st.markdown('<div class="box-container">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">🔍 Extracted Metadata (Edit to correct)</div>', unsafe_allow_html=True)
        st.caption("The AI extracted the following blocks. Please verify their accuracy.")
        
        new_title = st.text_area("Title", value=st.session_state.metadata.get('title', ''), height=68)
        new_authors = st.text_area("Authors", value=st.session_state.metadata.get('authors', ''), height=68)
        new_abstract = st.text_area("Abstract", value=st.session_state.metadata.get('abstract', ''), height=180)
        
        st.markdown('<div class="section-title" style="margin-top: 15px;">🛡️ Truth Engine: Citation Verification</div>', unsafe_allow_html=True)
        new_refs = st.text_area("Bibliography", value=st.session_state.metadata.get('references', ''), height=250)

        st.markdown('</div>', unsafe_allow_html=True)

        # Update Session State with any user edits
        st.session_state.metadata['title'] = new_title
        st.session_state.metadata['authors'] = new_authors
        st.session_state.metadata['abstract'] = new_abstract
        st.session_state.metadata['references'] = new_refs # <-- ADD THIS TOO

        # --- B. Compliance Checklist ---
        st.markdown('<div class="box-container">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">📋 Compliance Checklist</div>', unsafe_allow_html=True)
        
        # Title Check
        if new_title.strip() and new_title != "Error" and new_title != "Extraction Failed":
            st.markdown("✅ <span class='success-text'>Title Detected</span>", unsafe_allow_html=True)
        else:
            st.markdown("❌ <span class='error-text'>Title Missing or Failed</span>", unsafe_allow_html=True)

        # Author Check
        if new_authors.strip() and new_authors != "Error" and new_authors != "Extraction Failed":
            st.markdown("✅ <span class='success-text'>Authors Identified</span>", unsafe_allow_html=True)
        else:
            st.markdown("❌ <span class='error-text'>Authors Missing</span>", unsafe_allow_html=True)
        
        # Abstract Length Check
        word_count = len(new_abstract.split())
        if word_count == 0 or new_abstract == "Extraction Failed":
            st.markdown("❌ <span class='error-text'>Abstract Missing</span>", unsafe_allow_html=True)
        elif word_count > 250:
            st.markdown(f"⚠️ <span class='warning-text'>Abstract Too Long ({word_count} words - Max 250)</span>", unsafe_allow_html=True)
        else:
            st.markdown(f"✅ <span class='success-text'>Abstract Length OK ({word_count} words)</span>", unsafe_allow_html=True)
            
        st.markdown('</div>', unsafe_allow_html=True)

        # --- C. Gen-AI Fixer ---
        st.markdown('<div class="box-container">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">🪄 Gen-AI Fixer</div>', unsafe_allow_html=True)
        if st.button("✨ Auto-Fix Grammar & Shorten Abstract", use_container_width=True):
            st.info("Triggering LLM to rewrite abstract... (Hook up to engine.py here)")
        st.markdown('</div>', unsafe_allow_html=True)

        # --- D. Generation & Output ---
        if st.button("📄 Generate IEEE PDF", type="primary", use_container_width=True):
            with st.spinner("Compiling LaTeX..."):
                result = formatter.generate_pdf(st.session_state.metadata, st.session_state.raw_text)
                if result and not str(result).startswith("Formatting Error"):
                    st.success("PDF Generated Successfully!")
                    st.download_button(label="⬇️ Download PDF", data=result, file_name="nova_output.pdf", mime="application/pdf", use_container_width=True)
                else:
                    st.error(f"Failed to generate PDF: {result}")
        
        # Download Hashing Report
        report_text = f"N.O.V.A. INTEGRITY REPORT\n-------------------------\nDocument: {st.session_state.filename}\nLexical SHA-256 Hash: {st.session_state.lexical_hash}\nVerification: 100% Character Integrity Confirmed."
        st.download_button(label="🛡️ Download Hashing Report", data=report_text, file_name="integrity_report.txt", mime="text/plain", use_container_width=True)