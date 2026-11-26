import os
import sys
from pathlib import Path
import docx
import win32com.client
from build_complete_report import generate_document

def scan_page_numbers_in_word(doc_path):
    word = win32com.client.Dispatch("Word.Application")
    word.Visible = False
    doc = word.Documents.Open(str(doc_path))
    
    # We want to find the page numbers of each section
    toc_keys = [
        "CERTIFICATION",
        "CHAPTER ONE: INTRODUCTION",
        "1.1 Background of the Study",
        "1.2 Statement of the Problem",
        "1.3 Aim and Objectives of the Study",
        "1.4 Research Questions",
        "1.5 Significance of the Study",
        "1.6 Scope and Delimitations of the Study",
        "1.7 Definition of Terms",
        "1.8 Organization of the Report",
        "CHAPTER TWO: LITERATURE REVIEW",
        "2.1 Introduction",
        "2.2 Conceptual Framework",
        "2.3 The Evolution of Autonomous Web Agents",
        "2.4 Large Language Models (LLMs) in Web Navigation and Reasoning",
        "2.5 Chrome DevTools Protocol (CDP) & DOM State Representation",
        "2.6 Multimodal Vision & Grounding in Web Tasks",
        "2.7 Continuous Voice Interfaces & Dual-Engine Speech Processing",
        "2.8 E-Commerce Intelligence & Deep Information Extraction",
        "2.9 Review of Related Works & Contemporary Autonomous Agent Frameworks",
        "2.10 Summary of the Literature Review and Research Gap",
        "CHAPTER THREE: METHODOLOGY",
        "3.1 Introduction",
        "3.2 Architectural Design & System Framework",
        "3.3 Team Organization and Workflow",
        "3.4 Data Ingestion and Semantic DOM Parsing Pipeline",
        "3.5 Smart Intent Routing Engine",
        "3.6 5-Stage Visual Execution Pipeline Design",
        "3.7 Dual-Engine Voice System & Gemini Cloud STT Fallback Architecture",
        "3.8 Deep Market Search Engine Implementation",
        "3.9 Security, Error Recovery, and Resilient Multi-Model Fallback Mechanics",
        "3.10 System Deployment and Cloudflare Zero-Trust Tunnel Architecture",
        "CHAPTER FOUR: RESULTS AND DISCUSSION",
        "4.1 Introduction",
        "4.2 Experimental Setup and Test Environments",
        "4.3 Evaluation of Intent Classification Accuracy and Latency",
        "4.4 Performance Analysis of the 5-Stage Execution Feed",
        "4.5 Real-Time Voice Interaction & Latency Benchmark",
        "4.6 Deep Information Extraction & Jumia E-Commerce Case Study",
        "4.7 Autonomous Live Browser Navigation & CDP Interaction Results",
        "4.8 Error Recovery and Multi-Model Fallback Resilience Under Traffic Spikes",
        "4.9 Discussion of Findings & Academic Implications",
        "CHAPTER FIVE: CONCLUSION AND RECOMMENDATIONS",
        "5.1 Summary of Findings",
        "5.2 Contributions to Knowledge",
        "5.3 Limitations of the Study",
        "5.4 Recommendations for Future Research",
        "5.5 Final Remarks",
        "REFERENCES"
    ]
    
    page_map = {}
    
    # Iterate through paragraphs in the Word document
    for para in doc.Paragraphs:
        text = para.Range.Text.strip()
        for key in toc_keys:
            if key not in page_map and (text == key or text.startswith(key)):
                # wdActiveEndPageNumber = 3
                pg = para.Range.Information(3)
                page_map[key] = pg
                break
                
    doc.Close()
    word.Quit()
    return page_map

def main():
    proj_dir = Path("C:/Users/Laptop/OneDrive/Documenten/group 6 agent")
    doc_path = proj_dir / "Group 6 Report.docx"
    pdf_path = proj_dir / "Group 6 Report.pdf"
    desktop_dir = Path("C:/Users/Laptop/OneDrive/Desktop")
    docs_dir = Path("C:/Users/Laptop/OneDrive/Documenten")
    
    print("Step 1: Generating Initial Draft...")
    doc = generate_document()
    doc.save(str(doc_path))
    
    print("Step 2: Scanning Real Word Page Numbers via Word COM...")
    raw_page_map = scan_page_numbers_in_word(doc_path)
    print("Found page mappings:")
    for k, v in raw_page_map.items():
        print(f"  {k} -> Page {v}")
        
    # Preliminary pages use Roman numerals
    # Certification is on page ii
    formatted_page_map = {}
    formatted_page_map["CERTIFICATION"] = "ii"
    
    for k, v in raw_page_map.items():
        if k != "CERTIFICATION":
            formatted_page_map[k] = str(v)
            
    print("\nStep 3: Re-generating Document with Synchronized Table of Contents...")
    doc_final = generate_document(toc_page_map=formatted_page_map)
    doc_final.save(str(doc_path))
    
    print("\nStep 4: Exporting PDF and Checking for Empty Pages...")
    word = win32com.client.Dispatch("Word.Application")
    word.Visible = False
    doc_w = word.Documents.Open(str(doc_path))
    doc_w.SaveAs(str(pdf_path), FileFormat=17) # 17 is wdFormatPDF
    
    total_pages = doc_w.ComputeStatistics(2) # wdStatisticPages = 2
    print(f"Total Pages in Word: {total_pages}")
    
    # Check each page for content
    empty_pages = []
    for p in range(1, total_pages + 1):
        # Go to page
        r_start = doc_w.GoTo(1, 1, p) # wdGoToPage=1, wdGoToAbsolute=1
        if p == total_pages:
            end_pos = doc_w.Content.End
        else:
            r_next = doc_w.GoTo(1, 1, p + 1)
            end_pos = r_next.Start
            
        page_range = doc_w.Range(r_start.Start, end_pos)
        page_text = page_range.Text.strip()
        first_line = page_text.split('\r')[0][:40] if page_text else "<EMPTY>"
        print(f"Page {p}: Length={len(page_text)} | First: {first_line}")
        if len(page_text) == 0:
            empty_pages.append(p)
            
    doc_w.Close()
    word.Quit()
    
    if empty_pages:
        print(f"\n[WARNING] Found empty pages: {empty_pages}")
    else:
        print("\n[SUCCESS] VERIFIED: ZERO EMPTY PAGES in entire document!")
        
    print("\nStep 5: Copying Polished Files to Desktop & Documents...")
    import shutil
    shutil.copyfile(str(doc_path), str(desktop_dir / "Group 6 Report.docx"))
    shutil.copyfile(str(pdf_path), str(desktop_dir / "Group 6 Report.pdf"))
    shutil.copyfile(str(doc_path), str(docs_dir / "Group 6 Report.docx"))
    shutil.copyfile(str(pdf_path), str(docs_dir / "Group 6 Report.pdf"))
    print("[OK] All files successfully saved and verified!")

if __name__ == "__main__":
    main()
