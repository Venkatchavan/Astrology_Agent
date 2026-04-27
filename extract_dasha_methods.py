"""
Extract detailed Dasha calculation pages from PDFs
"""

import PyPDF2

# Extract from Robert Svoboda's book - Chapter 11 on Dashas
pdf_path = "data/Robert_Svoboda_-_Light_on_life_An_Introduction_to_the_Astrology_of_India.pdf"

print("=" * 80)
print("EXTRACTING VIMSHOTTARI DASHA CALCULATION METHOD")
print("From: Robert Svoboda - Light on Life")
print("=" * 80)

with open(pdf_path, 'rb') as file:
    pdf_reader = PyPDF2.PdfReader(file)
    
    # Pages 307-320 contain Dasha information (0-indexed: 306-319)
    dasha_pages = range(306, 322)
    
    for page_num in dasha_pages:
        page = pdf_reader.pages[page_num]
        text = page.extract_text()
        
        print(f"\n{'=' * 80}")
        print(f"PAGE {page_num + 1}")
        print("=" * 80)
        print(text)
        print()

# Also extract from the Art and Science book - Chapter 12
print("\n" + "=" * 80)
print("ADDITIONAL REFERENCE - THE ART AND SCIENCE OF VEDIC ASTROLOGY")
print("=" * 80)

pdf_path2 = "data/toaz.info-the-art-and-science-of-vedic-as-richard-fishpdf-pr_02b07b198c615367695a56c8fc77aec4.pdf"

with open(pdf_path2, 'rb') as file:
    pdf_reader = PyPDF2.PdfReader(file)
    
    # Pages 126-135 contain Vimshotari Dasha (0-indexed: 125-134)
    dasha_pages = range(125, 136)
    
    for page_num in dasha_pages:
        page = pdf_reader.pages[page_num]
        text = page.extract_text()
        
        print(f"\n{'=' * 80}")
        print(f"PAGE {page_num + 1}")
        print("=" * 80)
        print(text)
        print()
