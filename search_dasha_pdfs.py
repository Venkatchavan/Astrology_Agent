"""
Search PDFs for Dasha calculation information
"""

import PyPDF2
import os
import re

pdf_dir = "data"
search_terms = [
    "vimshottari", "dasha", "mahadasha", "antardasha",
    "nakshatra ruler", "120 year", "planetary period",
    "moon nakshatra", "dasha balance", "dasha calculation"
]

# Get all PDF files
pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith('.pdf')]

print("=" * 80)
print("SEARCHING PDFs FOR DASHA CALCULATION METHODS")
print("=" * 80)
print(f"\nFound {len(pdf_files)} PDF files:")
for pdf in pdf_files:
    print(f"  • {pdf}")

print("\n" + "=" * 80)
print("SEARCH RESULTS")
print("=" * 80)

for pdf_file in pdf_files:
    pdf_path = os.path.join(pdf_dir, pdf_file)
    print(f"\n{'=' * 80}")
    print(f"FILE: {pdf_file}")
    print("=" * 80)
    
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            total_pages = len(pdf_reader.pages)
            
            print(f"Total pages: {total_pages}")
            print(f"\nSearching for Dasha-related content...\n")
            
            matches_found = 0
            
            # Search through pages
            for page_num in range(min(total_pages, 500)):  # Limit to first 500 pages
                try:
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text().lower()
                    
                    # Check if any search term appears
                    for term in search_terms:
                        if term in text:
                            # Extract context around the term
                            pattern = re.compile(f'.{{0,200}}{re.escape(term)}.{{0,200}}', re.IGNORECASE | re.DOTALL)
                            contexts = pattern.findall(page.extract_text())
                            
                            if contexts:
                                matches_found += 1
                                print(f"\n--- PAGE {page_num + 1} ---")
                                print(f"Term found: '{term}'")
                                print(f"Context (first match):")
                                # Clean up the context
                                context = contexts[0].replace('\n', ' ').strip()
                                print(f"  ...{context}...")
                                
                                # Only show first few matches per file to avoid overwhelming output
                                if matches_found >= 10:
                                    print(f"\n[Limiting output to first 10 matches. Found more on subsequent pages...]")
                                    break
                    
                    if matches_found >= 10:
                        break
                        
                except Exception as e:
                    continue
            
            if matches_found == 0:
                print("No Dasha-related content found in first 500 pages.")
                
    except Exception as e:
        print(f"Error reading PDF: {e}")

print("\n" + "=" * 80)
print("SEARCH COMPLETE")
print("=" * 80)
