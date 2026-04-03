import fitz  # PyMuPDF
from docx import Document
from pathlib import Path

Path("tests/fixtures").mkdir(parents=True, exist_ok=True)

# Valid text PDF
doc = fitz.open()
page = doc.new_page()
page.insert_text((72, 72), "This Data Processing Agreement is entered into between...")
doc.save("tests/fixtures/sample_dpa.pdf")
doc.close()

# Write a minimal DOCX
d = Document()
d.add_paragraph("Master Service Agreement between Company A and Supplier B.")
d.save("tests/fixtures/sample_msa.docx")

print("Fixtures created.")
