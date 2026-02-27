import sys
sys.path.append("backend")

from unstructured.partition.auto import partition
print("Extracting Sample X tables...")
elements = partition(
    filename="assets/Sample_X_Input.docx",
    strategy="hi_res",
    hi_res_model_name="yolox",
    infer_table_structure=True,
    skip_infer_table_types=["pdf"]
)

for e in elements:
    if type(e).__name__ == "Table":
        print("TABLE FOUND!")
        html = getattr(e.metadata, "text_as_html", "NO HTML") if hasattr(e, "metadata") else "NO HTML"
        print("HTML length:", len(html))
        print("PREVIEW:", html[:200])
