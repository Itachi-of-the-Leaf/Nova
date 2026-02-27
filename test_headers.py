import docx

def get_first_header(filepath):
    doc = docx.Document(filepath)
    for p in doc.paragraphs:
        if p.text.strip() and len(p.text.strip()) > 5:
            return p.text.strip()
            
print("Sample 3 First Block:", get_first_header("assets/Sample_3_Input.docx"))
print("Sample X First Block:", get_first_header("assets/Sample_X_Input.docx"))
