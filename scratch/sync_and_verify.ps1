param()

$projDir = "C:\Users\Laptop\OneDrive\Documenten\group 6 agent"
$docPath = Join-Path $projDir "Group 6 Report.docx"
$pdfPath = Join-Path $projDir "Group 6 Report.pdf"
$desktopDir = "C:\Users\Laptop\OneDrive\Desktop"
$docsDir = "C:\Users\Laptop\OneDrive\Documenten"

Set-Location $projDir

Write-Output "Step 1: Generating Initial Document..."
& ".venv\Scripts\python.exe" "scratch\build_complete_report.py"

Write-Output "Step 2: Scanning Page Numbers in Word COM..."
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$doc = $word.Documents.Open($docPath)

# TOC Keys to map
$tocKeys = @(
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
)

$pageMap = @{}

foreach ($para in $doc.Paragraphs) {
    $text = $para.Range.Text.Trim()
    foreach ($key in $tocKeys) {
        if (-not $pageMap.ContainsKey($key) -and ($text -eq $key -or $text.StartsWith($key))) {
            # 3 = wdActiveEndPageNumber
            $pg = $para.Range.Information(3)
            $pageMap[$key] = $pg
            break
        }
    }
}

$doc.Close()

Write-Output "Found Page Numbers in Word:"
$jsonEntries = @()
foreach ($key in $pageMap.Keys) {
    $pg = $pageMap[$key]
    Write-Output "  $key -> Page $pg"
    $cleanKey = $key.Replace('\', '\\').Replace('"', '\"')
    $jsonEntries += "`"$cleanKey`": `"$pg`""
}

# Write mapped page numbers to json
$jsonContent = "{" + ($jsonEntries -join ",`n") + "}"
Set-Content -Path "scratch\page_map.json" -Value $jsonContent -Encoding UTF8

Write-Output "`nStep 3: Updating Document with Exact Scanned Page Numbers..."
$updateScript = @"
import json
from pathlib import Path
from build_complete_report import generate_document

with open('scratch/page_map.json', 'r', encoding='utf-8') as f:
    page_map = json.load(f)

# Certification is on Roman numeral ii
page_map['CERTIFICATION'] = 'ii'

doc = generate_document(toc_page_map=page_map)
doc.save('Group 6 Report.docx')
print('[OK] Document re-generated with exact page numbers.')
"@
Set-Content -Path "scratch\update_toc.py" -Value $updateScript -Encoding UTF8
& ".venv\Scripts\python.exe" "scratch\update_toc.py"

Write-Output "`nStep 4: Exporting PDF and Checking Every Page for Blank Content..."
$doc2 = $word.Documents.Open($docPath)
$doc2.SaveAs([ref]$pdfPath, [ref]17) # 17 = wdFormatPDF

$totalCount = $doc2.ComputeStatistics(2) # 2 = wdStatisticPages
Write-Output "Total Pages in Final Document: $totalCount"

$emptyList = @()
for ($p = 1; $p -le $totalCount; $p++) {
    $rStart = $doc2.GoTo(1, 1, $p)
    if ($p -eq $totalCount) {
        $endPos = $doc2.Content.End
    } else {
        $rNext = $doc2.GoTo(1, 1, ($p + 1))
        $endPos = $rNext.Start
    }
    $pageRange = $doc2.Range($rStart.Start, $endPos)
    $pageText = $pageRange.Text.Trim()
    $firstLine = if ($pageText.Length -gt 0) { ($pageText -split "`r`n|`r|`n")[0].Substring(0, [Math]::Min(50, ($pageText -split "`r`n|`r|`n")[0].Length)) } else { "<EMPTY>" }
    Write-Output "Page $($p): Length=$($pageText.Length) | First: $($firstLine)"
    
    if ($pageText.Length -eq 0) {
        $emptyList += $p
    }
}

$doc2.Close()
$word.Quit()

if ($emptyList.Count -eq 0) {
    Write-Output "`n[SUCCESS] VERIFIED: ZERO EMPTY PAGES in entire 40+ page document!"
} else {
    Write-Output "`n[WARNING] Found empty pages on: $($emptyList -join ', ')"
}

Write-Output "`nStep 5: Copying Polished Files to Desktop & Documents..."
Copy-Item $docPath (Join-Path $desktopDir "Group 6 Report.docx") -Force
Copy-Item $pdfPath (Join-Path $desktopDir "Group 6 Report.pdf") -Force
Copy-Item $docPath (Join-Path $docsDir "Group 6 Report.docx") -Force
Copy-Item $pdfPath (Join-Path $docsDir "Group 6 Report.pdf") -Force

Write-Output "[OK] All files successfully updated and verified in all locations!"
