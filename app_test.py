#!/usr/bin/env python3
"""Lightweight test version of the app without marker library"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import tempfile
import shutil
from pathlib import Path

# Import for EPUB generation
import ebooklib
from ebooklib import epub

app = FastAPI(title="KindleMyPaper Test", description="Test version without marker")

# Enable CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
app.mount("/static", StaticFiles(directory="."), name="static")

# Pydantic models
class TreatmentRequest(BaseModel):
    markdown: str
    prompt: str

class EpubRequest(BaseModel):
    markdown: str
    title: str

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main HTML page"""
    try:
        with open("index.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>KindleMyPaper Test</h1><p>index.html not found</p>")

@app.post("/api/convert-to-markdown")
async def convert_to_markdown(pdf: UploadFile = File(...)):
    """Mock PDF to markdown conversion for testing"""
    if pdf.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    # Mock markdown conversion - in real app this would use marker
    mock_markdown = f"""# {pdf.filename.replace('.pdf', '')}

## Abstract
This is a mock conversion of your PDF file. In the real application, this would be converted using the marker library for high-quality PDF to markdown conversion.

## Introduction
The marker library provides excellent PDF to markdown conversion with:
- High accuracy OCR
- Table extraction
- Image preservation
- Mathematical formula support

## Method
Your uploaded file: **{pdf.filename}**
File size: **{pdf.size} bytes**

## Results
The conversion would normally extract:
- All text content
- Images and figures
- Tables and equations
- References and citations

## Conclusion
This mock conversion demonstrates the workflow. The real conversion would happen here with marker library processing.

---
*Mock conversion for testing purposes*
"""
    
    return {"markdown": mock_markdown, "images": 0}

@app.post("/api/apply-treatment")
async def apply_treatment(request: TreatmentRequest):
    """Mock treatment application"""
    treated_markdown = f"""# Treated Document

**Applied treatment:** {request.prompt}

---

{request.markdown}

---

**Treatment Notes:**
- This is a mock treatment for testing
- In the real app, this would use AI or advanced text processing
- The treatment would improve formatting, fix OCR errors, and enhance readability
"""
    
    return {"treated_markdown": treated_markdown}

@app.post("/api/generate-epub")
async def generate_epub(request: EpubRequest):
    """Generate EPUB from markdown"""
    try:
        # Create EPUB book
        book = epub.EpubBook()
        book.set_identifier('kindlemypaper_test_' + request.title.replace(' ', '_'))
        book.set_title(request.title)
        book.set_language('en')
        book.add_author('KindleMyPaper Test')
        
        # Convert markdown to HTML (basic conversion)
        html_content = markdown_to_html(request.markdown)
        
        # Create chapter
        chapter = epub.EpubHtml(title=request.title, file_name='chapter.xhtml', lang='en')
        chapter.content = f'''<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>{request.title}</title>
    <style>
        body {{ 
            font-family: Georgia, serif; 
            line-height: 1.6; 
            margin: 2em; 
            max-width: 800px;
        }}
        h1, h2, h3 {{ 
            color: #333; 
            margin-top: 2em; 
            margin-bottom: 1em;
        }}
        p {{ 
            margin-bottom: 1em; 
            text-align: justify; 
        }}
        pre, code {{ 
            font-family: 'Courier New', monospace; 
            background: #f5f5f5; 
            padding: 0.5em;
            border-radius: 3px;
        }}
        blockquote {{ 
            margin-left: 2em; 
            font-style: italic; 
            border-left: 3px solid #ccc;
            padding-left: 1em;
        }}
        hr {{
            border: none;
            border-top: 1px solid #ccc;
            margin: 2em 0;
        }}
    </style>
</head>
<body>
    {html_content}
</body>
</html>'''
        
        # Add chapter to book
        book.add_item(chapter)
        
        # Create table of contents
        book.toc = (epub.Link("chapter.xhtml", request.title, "chapter"),)
        
        # Add navigation files
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        
        # Create spine
        book.spine = ['nav', chapter]
        
        # Save EPUB to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".epub") as tmp_file:
            epub.write_epub(tmp_file.name, book)
            tmp_path = tmp_file.name
        
        # Return file
        return FileResponse(
            tmp_path,
            media_type="application/epub+zip",
            filename=f"{request.title}.epub",
            background=lambda: os.unlink(tmp_path)  # Clean up after sending
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"EPUB generation failed: {str(e)}")

def markdown_to_html(markdown: str) -> str:
    """Basic markdown to HTML conversion"""
    lines = markdown.split('\n')
    html_lines = []
    in_code_block = False
    
    for line in lines:
        if line.strip().startswith('```'):
            if in_code_block:
                html_lines.append('</pre>')
                in_code_block = False
            else:
                html_lines.append('<pre>')
                in_code_block = True
            continue
            
        if in_code_block:
            html_lines.append(line)
            continue
            
        # Headers
        if line.startswith('# '):
            html_lines.append(f'<h1>{line[2:]}</h1>')
        elif line.startswith('## '):
            html_lines.append(f'<h2>{line[3:]}</h2>')
        elif line.startswith('### '):
            html_lines.append(f'<h3>{line[4:]}</h3>')
        elif line.startswith('---'):
            html_lines.append('<hr>')
        # Bold and italic
        elif '**' in line or '*' in line:
            # Simple bold/italic processing
            processed_line = line
            while '**' in processed_line:
                processed_line = processed_line.replace('**', '<strong>', 1).replace('**', '</strong>', 1)
            while '*' in processed_line and '<strong>' not in processed_line:
                processed_line = processed_line.replace('*', '<em>', 1).replace('*', '</em>', 1)
            if processed_line.strip():
                html_lines.append(f'<p>{processed_line}</p>')
        # Regular paragraph
        elif line.strip():
            html_lines.append(f'<p>{line}</p>')
        # Empty line
        else:
            html_lines.append('<br>')
    
    return '\n'.join(html_lines)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy - test mode",
        "marker_available": False,
        "epub_available": True,
        "ai_available": False,
        "note": "This is the test version without marker library"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)  # Use port 8001 for test