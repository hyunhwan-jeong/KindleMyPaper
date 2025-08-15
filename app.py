from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import tempfile
import shutil
import subprocess
from pathlib import Path
import json
from typing import Optional

# For AI treatment (optional)
try:
    import openai
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    print("Info: OpenAI not installed. AI treatment will use basic text processing.")

# For PDF to markdown conversion
try:
    from marker.models import create_model_dict
    from marker.config.parser import ConfigParser
    from marker.output import save_output
    MARKER_AVAILABLE = True
except ImportError:
    MARKER_AVAILABLE = False
    print("Info: Marker not installed. PDF conversion will not work.")

app = FastAPI(title="KindleMyPaper v2", description="Convert Academic Papers to Kindle Format - Two-Step Process")

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

# Global storage for uploaded files
uploaded_files = {}

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main HTML page"""
    try:
        with open("index.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>KindleMyPaper</h1><p>index.html not found</p>")

@app.post("/api/upload-pdf")
async def upload_pdf(pdf: UploadFile = File(...)):
    """Step 1: Upload PDF file"""
    if pdf.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    # Create temporary file
    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, pdf.filename)
    
    with open(temp_path, "wb") as f:
        shutil.copyfileobj(pdf.file, f)
    
    # Store file info
    file_id = pdf.filename.replace('.pdf', '').replace(' ', '_')
    uploaded_files[file_id] = {
        'path': temp_path,
        'filename': pdf.filename,
        'size': os.path.getsize(temp_path)
    }
    
    print(f"📤 Uploaded: {pdf.filename} ({uploaded_files[file_id]['size']} bytes)")
    
    return {
        "file_id": file_id,
        "filename": pdf.filename,
        "size": uploaded_files[file_id]['size'],
        "status": "uploaded"
    }

@app.post("/api/convert/{file_id}")
async def convert_pdf(file_id: str):
    """Step 2: Convert uploaded PDF to markdown using marker_single"""
    
    if file_id not in uploaded_files:
        raise HTTPException(status_code=404, detail="File not found. Please upload first.")
    
    file_info = uploaded_files[file_id]
    pdf_path = file_info['path']
    
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="PDF file no longer exists")
    
    try:
        print(f"🔄 Converting {file_info['filename']} using marker...")
        
        if not MARKER_AVAILABLE:
            raise HTTPException(status_code=500, detail="Marker not installed")
        
        # Use marker directly in Python
        models = create_model_dict()
        config_parser = ConfigParser({
            'output_dir': os.path.dirname(pdf_path),
            'output_format': 'markdown',
            'debug': False,
            'converter_cls': 'marker.converters.pdf.PdfConverter'
        })
        
        converter_cls = config_parser.get_converter_cls()
        converter = converter_cls(
            config=config_parser.generate_config_dict(),
            artifact_dict=models,
            processor_list=config_parser.get_processors(),
            renderer=config_parser.get_renderer(),
            llm_service=config_parser.get_llm_service(),
        )
        
        # Convert the PDF
        rendered = converter(pdf_path)
        out_folder = config_parser.get_output_folder(pdf_path)
        base_filename = config_parser.get_base_filename(pdf_path)
        save_output(rendered, out_folder, base_filename)
        
        # Find the generated markdown file
        output_dir = out_folder
        print(f"🔍 Looking for markdown files in: {output_dir}")
        
        md_files = list(Path(output_dir).glob("*.md"))
        print(f"📝 Markdown files found: {[f.name for f in md_files]}")
        
        if not md_files:
            all_files = list(Path(output_dir).glob("*"))
            raise HTTPException(status_code=500, detail=f"No markdown file generated. Files in directory: {[f.name for f in all_files]}")
        
        md_path = md_files[0]
        
        with open(md_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
        
        # Clean up markdown - remove page numbers, fix title
        cleaned_markdown = clean_markdown(markdown_content, file_info['filename'])
        
        print(f"✅ Conversion complete: {len(cleaned_markdown)} characters")
        
        # Clean up temporary files
        shutil.rmtree(os.path.dirname(pdf_path))
        del uploaded_files[file_id]
        
        return {
            "markdown": cleaned_markdown,
            "status": "converted"
        }
        
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=500, detail="Conversion timed out (5 minutes)")
    except Exception as e:
        print(f"❌ Conversion error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")

def clean_markdown(content: str, filename: str) -> str:
    """Clean up markdown content"""
    lines = content.split('\n')
    cleaned_lines = []
    
    title_set = False
    
    for line in lines:
        # Skip page number patterns
        if line.strip().startswith('## Page ') and line.strip().endswith(line.strip().split()[-1].isdigit()):
            continue
            
        # Fix title - use first real heading as title, not filename
        if line.startswith('# ') and not title_set:
            title_set = True
            cleaned_lines.append(line)
        elif line.startswith('#') and line.strip() != f"# {filename.replace('.pdf', '')}":
            cleaned_lines.append(line)
        elif not line.startswith('# '):
            cleaned_lines.append(line)
    
    # If no title was found, add one based on first heading or filename
    if not title_set:
        for i, line in enumerate(cleaned_lines):
            if line.startswith('## '):
                cleaned_lines.insert(0, f"# {line[3:]}")
                cleaned_lines.pop(i + 1)
                break
        else:
            # Fallback to filename without extension
            title = filename.replace('.pdf', '').replace('_', ' ').replace('-', ' ').title()
            cleaned_lines.insert(0, f"# {title}\n")
    
    return '\n'.join(cleaned_lines)

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
    """Generate EPUB from markdown using pandoc"""
    
    try:
        # Create temporary files
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as md_file:
            md_file.write(request.markdown)
            md_path = md_file.name
        
        epub_path = md_path.replace('.md', '.epub')
        
        # Use pandoc to convert markdown to EPUB
        result = subprocess.run([
            'pandoc',
            md_path,
            '-o', epub_path,
            f'--metadata=title:{request.title}',
            '--metadata=author:Academic Paper',
            '--metadata=language:en',
            '--toc',  # Add table of contents
            '--toc-depth=3'
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Pandoc failed: {result.stderr}")
            os.unlink(md_path)
            raise HTTPException(status_code=500, detail=f"EPUB generation failed: {result.stderr}")
        
        if not os.path.exists(epub_path):
            os.unlink(md_path)
            raise HTTPException(status_code=500, detail="EPUB file was not created")
        
        print(f"✅ EPUB generated: {epub_path}")
        
        # Return the EPUB file
        return FileResponse(
            epub_path,
            media_type="application/epub+zip",
            filename=f"{request.title}.epub",
            background=lambda: [os.unlink(md_path), os.unlink(epub_path)]
        )
        
    except Exception as e:
        if 'md_path' in locals() and os.path.exists(md_path):
            os.unlink(md_path)
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
    
    # Check if marker_single is available
    try:
        result = subprocess.run(['marker_single', '--help'], capture_output=True, text=True)
        marker_available = result.returncode == 0
    except FileNotFoundError:
        marker_available = False
    
    # Check if pandoc is available
    try:
        result = subprocess.run(['pandoc', '--version'], capture_output=True, text=True)
        pandoc_available = result.returncode == 0
    except FileNotFoundError:
        pandoc_available = False
    
    return {
        "status": "healthy",
        "marker_available": marker_available,
        "pandoc_available": pandoc_available,
        "ai_available": AI_AVAILABLE and bool(os.getenv("OPENAI_API_KEY")),
        "version": "2.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)