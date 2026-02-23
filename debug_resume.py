"""
Debug Script - Run this to find why skills = 0
Save as: debug_resume.py
"""

import re
import PyPDF2


def debug_resume_parsing(pdf_path):
    """Debug why skills aren't being extracted"""
    
    print("=" * 80)
    print("RESUME PARSING DEBUG")
    print("=" * 80)
    
    # Step 1: Check if file opens
    print("\n1. CHECKING FILE ACCESS...")
    try:
        with open(pdf_path, 'rb') as file:
            print(f"   ✅ File opened successfully: {pdf_path}")
    except Exception as e:
        print(f"   ❌ ERROR: Cannot open file - {e}")
        return
    
    # Step 2: Extract text from PDF
    print("\n2. EXTRACTING TEXT FROM PDF...")
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            print(f"   ✅ PDF has {len(reader.pages)} page(s)")
            
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text()
                text += page_text + "\n"
                print(f"   ✅ Page {i+1} extracted: {len(page_text)} characters")
    except Exception as e:
        print(f"   ❌ ERROR extracting text: {e}")
        return
    
    print(f"\n   Total text extracted: {len(text)} characters")
    
    # Step 3: Show first 500 characters
    print("\n3. FIRST 500 CHARACTERS OF EXTRACTED TEXT:")
    print("-" * 80)
    print(text[:500])
    print("-" * 80)
    
    # Step 4: Search for "SKILLS" section
    print("\n4. SEARCHING FOR 'SKILLS' SECTION...")
    text_lower = text.lower()
    
    if 'skills' in text_lower:
        print("   ✅ Found 'skills' in text!")
        
        # Find position
        skills_index = text_lower.find('skills')
        print(f"   Position: {skills_index}")
        
        # Show context around "skills"
        start = max(0, skills_index - 50)
        end = min(len(text), skills_index + 200)
        print(f"\n   CONTEXT AROUND 'SKILLS':")
        print("-" * 80)
        print(text[start:end])
        print("-" * 80)
    else:
        print("   ❌ 'SKILLS' word NOT found in text!")
    
    # Step 5: Search for specific skills
    print("\n5. SEARCHING FOR SPECIFIC SKILLS...")
    
    test_skills = [
        'python', 'machine learning', 'tensorflow', 'pytorch',
        'nlp', 'flask', 'sql', 'docker', 'git'
    ]
    
    found_skills = []
    for skill in test_skills:
        if skill in text_lower:
            found_skills.append(skill)
            print(f"   ✅ Found: {skill}")
        else:
            print(f"   ❌ NOT found: {skill}")
    
    print(f"\n   Total skills found: {len(found_skills)}/{len(test_skills)}")
    
    # Step 6: Try the extraction function
    print("\n6. TESTING SKILL EXTRACTION FUNCTION...")
    
    extracted_skills = extract_skills_test(text)
    
    total_extracted = sum(len(v) for v in extracted_skills.values())
    print(f"   Total skills extracted: {total_extracted}")
    
    for category, skills in extracted_skills.items():
        if skills:
            print(f"   {category}: {', '.join(skills)}")
    
    # Step 7: Show lines containing skills
    print("\n7. LINES CONTAINING SKILLS:")
    lines = text.split('\n')
    skill_lines = []
    
    for i, line in enumerate(lines):
        line_lower = line.lower()
        for skill in test_skills:
            if skill in line_lower:
                skill_lines.append((i, line.strip(), skill))
                break
    
    if skill_lines:
        print(f"   Found {len(skill_lines)} lines with skills:")
        for line_num, line_text, skill in skill_lines[:10]:  # Show first 10
            print(f"   Line {line_num}: [{skill}] {line_text[:70]}")
    else:
        print("   ❌ No lines found with skills!")
    
    print("\n" + "=" * 80)
    print("DEBUG COMPLETE")
    print("=" * 80)
    
    return text, extracted_skills


def extract_skills_test(text: str):
    """Test skill extraction"""
    skills = {
        'programming_languages': [],
        'ml_ai': [],
        'frameworks': [],
        'cloud_tools': [],
        'databases': []
    }
    
    skill_mapping = {
        'programming_languages': ['python', 'java', 'javascript', 'sql', 'numpy', 'pandas'],
        'ml_ai': ['machine learning', 'deep learning', 'nlp', 'computer vision', 
                 'tensorflow', 'pytorch', 'keras', 'opencv', 'yolo', 'transformers'],
        'frameworks': ['flask', 'fastapi', 'streamlit', 'django', 'react'],
        'cloud_tools': ['aws', 'docker', 'kubernetes', 'git', 'github'],
        'databases': ['mysql', 'postgresql', 'mongodb', 'redis']
    }
    
    text_lower = text.lower()
    
    for category, skill_list in skill_mapping.items():
        for skill in skill_list:
            if skill in text_lower:
                skills[category].append(skill.title())
    
    return skills


# ============================================================================
# RUN THIS TO DEBUG YOUR RESUME
# ============================================================================

if __name__ == "__main__":
    import os
    
    # First, list all PDF files in current directory
    print("\n📂 PDF files in current directory:")
    print("=" * 60)
    
    pdf_files = [f for f in os.listdir('.') if f.endswith('.pdf')]
    
    if not pdf_files:
        print("❌ No PDF files found!")
        print("\nPlease:")
        print("1. Put your resume PDF in this folder")
        print("2. Or provide full path below")
        exit()
    
    for i, pdf in enumerate(pdf_files, 1):
        print(f"{i}. {pdf}")
    
    print("\n" + "=" * 60)
    
    # Let user choose or provide path
    if len(pdf_files) == 1:
        resume_path = pdf_files[0]
        print(f"\n✅ Using: {resume_path}")
    else:
        print("\nEnter file number or full path:")
        choice = input("> ").strip()
        
        if choice.isdigit() and 1 <= int(choice) <= len(pdf_files):
            resume_path = pdf_files[int(choice) - 1]
        else:
            resume_path = choice
    
    print("\nStarting debug for:", resume_path)
    print()
    
    try:
        text, skills = debug_resume_parsing(resume_path)
        
        print("\n\n" + "=" * 80)
        print("RECOMMENDATIONS:")
        print("=" * 80)
        
        total_skills = sum(len(v) for v in skills.values())
        
        if total_skills == 0:
            print("""
❌ NO SKILLS FOUND!

Possible reasons:
1. PDF text extraction failed (text might be in images/scanned)
2. Skills section is in a table/complex format
3. Skills are listed in unusual format

Solutions:
1. Try saving resume as new PDF (Print to PDF)
2. Ensure resume is not scanned (should be searchable text)
3. Upload DOCX version if available
4. Check if skills section uses standard headers: "SKILLS", "Technical Skills"
            """)
        elif total_skills < 5:
            print(f"""
⚠️ ONLY {total_skills} SKILLS FOUND (Expected 15-25)

Your resume likely has more skills than detected.

Solutions:
1. Ensure skills are in plain text (not in tables)
2. Use bullet points for skills
3. Check spelling of skill names
            """)
        else:
            print(f"""
✅ SKILLS EXTRACTION WORKING! Found {total_skills} skills.

If still showing 0 in app, check:
1. Is resume_parser.py using the updated _extract_skills() method?
2. Did you restart the Streamlit app after changes?
3. Are you uploading the same resume file?
            """)
            
    except Exception as e:
        print(f"\n❌ DEBUG FAILED: {e}")
        import traceback
        traceback.print_exc()