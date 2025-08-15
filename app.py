from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import tempfile
import shutil
from pathlib import Path
import asyncio
from typing import Optional

# Import marker library
try:
    from marker.converters.pdf import PdfConverter
    from marker.models import create_model_dict
    from marker.output import text_from_rendered
    MARKER_AVAILABLE = True
except ImportError:
    MARKER_AVAILABLE = False
    print("Warning: marker-pdf not installed. PDF conversion will not work.")

# Import for EPUB generation
try:
    import ebooklib
    from ebooklib import epub
    EPUB_AVAILABLE = True
except ImportError:
    EPUB_AVAILABLE = False
    print("Warning: ebooklib not installed. EPUB generation will not work.")

# For AI treatment (optional)
try:
    import openai
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    print("Info: OpenAI not installed. AI treatment will use basic text processing.")

app = FastAPI(title="KindleMyPaper", description="Convert Academic Papers to Kindle Format")

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

# Initialize marker converter
if MARKER_AVAILABLE:
    try:
        converter = PdfConverter(artifact_dict=create_model_dict())
    except Exception as e:
        print(f"Warning: Could not initialize marker converter: {e}")
        converter = None
else:
    converter = None

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main HTML page"""
    try:
        with open("index.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>KindleMyPaper</h1><p>index.html not found</p>")

@app.post("/api/convert-to-markdown")
async def convert_to_markdown(pdf: UploadFile = File(...)):
    """Convert PDF to markdown using marker library"""
    if not MARKER_AVAILABLE or converter is None:
        raise HTTPException(status_code=500, detail="Marker library not available")
    
    if pdf.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        shutil.copyfileobj(pdf.file, tmp_file)
        tmp_path = tmp_file.name
    
    try:
        # Convert PDF to markdown
        rendered = converter(tmp_path)
        text, _, images = text_from_rendered(rendered)
        
        # Clean up temporary file
        os.unlink(tmp_path)
        
        return {"markdown": text, "images": len(images)}
        
    except Exception as e:
        # Clean up temporary file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")

@app.post("/api/apply-treatment")
async def apply_treatment(request: TreatmentRequest):
    """Apply custom treatment to markdown using AI or basic processing"""
    
    if AI_AVAILABLE and os.getenv("OPENAI_API_KEY"):
        try:
            # Use OpenAI for treatment
            client = openai.OpenAI()
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that improves academic paper markdown formatting."},
                    {"role": "user", "content": f"Please apply this treatment: {request.prompt}\n\nTo this markdown:\n{request.markdown}"}
                ],
                max_tokens=4000
            )
            treated_markdown = response.choices[0].message.content
        except Exception as e:
            # Fallback to basic processing
            treated_markdown = basic_markdown_treatment(request.markdown, request.prompt)
    else:
        # Use basic processing
        treated_markdown = basic_markdown_treatment(request.markdown, request.prompt)
    
    return {"treated_markdown": treated_markdown}

def basic_markdown_treatment(markdown: str, prompt: str) -> str:
    """Basic markdown treatment without AI"""
    lines = markdown.split('\n')
    treated_lines = []
    
    for line in lines:
        # Basic improvements
        line = line.strip()
        
        # Fix common OCR issues
        line = line.replace('fi', 'fi')  # ligature fix
        line = line.replace('fl', 'fl')  # ligature fix
        
        # Improve headers (if line is all caps and short, make it a header)
        if len(line) < 100 and line.isupper() and len(line) > 3:
            line = f"## {line.title()}"
        
        # Add proper spacing
        if line and not line.startswith('#') and not line.startswith('-') and not line.startswith('*'):
            if len(line) > 50:  # Likely a paragraph
                treated_lines.append(line)
                treated_lines.append('')  # Add spacing
            else:
                treated_lines.append(line)
        else:
            treated_lines.append(line)
    
    return '\n'.join(treated_lines)

@app.post("/api/generate-epub")
async def generate_epub(request: EpubRequest):
    """Generate EPUB from markdown"""
    if not EPUB_AVAILABLE:
        raise HTTPException(status_code=500, detail="ebooklib not available")
    
    try:
        # Create EPUB book
        book = epub.EpubBook()
        book.set_identifier('kindlemypaper_' + request.title.replace(' ', '_'))
        book.set_title(request.title)
        book.set_language('en')
        book.add_author('Academic Paper')
        
        # Convert markdown to HTML (basic conversion)
        html_content = markdown_to_html(request.markdown)
        
        # Create chapter
        chapter = epub.EpubHtml(title=request.title, file_name='chapter.xhtml', lang='en')
        chapter.content = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>{request.title}</title>
            <style>
                body {{ font-family: serif; line-height: 1.6; margin: 2em; }}
                h1, h2, h3 {{ color: #333; margin-top: 2em; }}
                p {{ margin-bottom: 1em; text-align: justify; }}
                pre, code {{ font-family: monospace; background: #f5f5f5; }}
                blockquote {{ margin-left: 2em; font-style: italic; }}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        '''
        
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
        # Bold and italic
        elif '**' in line or '*' in line:
            line = line.replace('**', '<strong>', 1).replace('**', '</strong>', 1)
            line = line.replace('*', '<em>', 1).replace('*', '</em>', 1)
            html_lines.append(f'<p>{line}</p>')
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
        "status": "healthy",
        "marker_available": MARKER_AVAILABLE,
        "epub_available": EPUB_AVAILABLE,
        "ai_available": AI_AVAILABLE and bool(os.getenv("OPENAI_API_KEY"))
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)