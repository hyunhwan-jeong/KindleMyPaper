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
import time
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
    from marker.models import create_model_dict, TableRecPredictor
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
app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve temporary images
app.mount("/temp_images", StaticFiles(directory="temp_images"), name="temp_images")

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
    
    # Clean up old temp images
    cleanup_old_temp_images()
    
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
        print("🔧 Initializing models...")
        models = create_model_dict()
        
        config_parser = ConfigParser({
            'output_dir': os.path.dirname(pdf_path),
            'output_format': 'markdown',
            'debug': False,
            'converter_cls': 'marker.converters.pdf.PdfConverter'
        })
        
        # Get original processors and filter out table processor to avoid tensor stack error
        original_processors = config_parser.get_processors() or []
        filtered_processors = []
        
        for processor in original_processors:
            processor_name = processor.__class__.__name__
            if 'table' not in processor_name.lower():
                filtered_processors.append(processor)
                print(f"✅ Including processor: {processor_name}")
            else:
                print(f"⚠️ Skipping table processor: {processor_name} to avoid tensor stack error")
        
        converter_cls = config_parser.get_converter_cls()
        converter = converter_cls(
            config=config_parser.generate_config_dict(),
            artifact_dict=models,
            processor_list=filtered_processors,
            renderer=config_parser.get_renderer(),
            llm_service=config_parser.get_llm_service(),
        )
        
        # Convert the PDF
        rendered = converter(pdf_path)
        out_folder = config_parser.get_output_folder(pdf_path)
        base_filename = config_parser.get_base_filename(pdf_path)
        save_output(rendered, out_folder, base_filename)
        
        # Find the generated markdown file and images
        output_dir = out_folder
        print(f"🔍 Looking for markdown files in: {output_dir}")
        
        md_files = list(Path(output_dir).glob("*.md"))
        # Support common image formats
        image_extensions = ['*.png', '*.jpg', '*.jpeg', '*.tiff', '*.tif', '*.bmp', '*.gif', '*.webp']
        image_files = []
        for ext in image_extensions:
            image_files.extend(list(Path(output_dir).glob(ext)))
        
        print(f"📝 Markdown files found: {[f.name for f in md_files]}")
        print(f"🖼️ Image files found: {[f.name for f in image_files]}")
        
        if not md_files:
            all_files = list(Path(output_dir).glob("*"))
            raise HTTPException(status_code=500, detail=f"No markdown file generated. Files in directory: {[f.name for f in all_files]}")
        
        md_path = md_files[0]
        
        with open(md_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
        
        # Copy images to temporary directory for serving
        temp_images = []
        session_image_dir = None
        if image_files:
            # Create session-specific directory in temp_images
            session_id = f"session_{file_id}_{int(time.time())}"
            session_image_dir = os.path.join("temp_images", session_id)
            os.makedirs(session_image_dir, exist_ok=True)
            
            for image_file in image_files:
                # Copy image to session directory
                temp_image_path = os.path.join(session_image_dir, image_file.name)
                shutil.copy2(image_file, temp_image_path)
                temp_images.append(f"/temp_images/{session_id}/{image_file.name}")
                print(f"📸 Copied image to temp: {session_id}/{image_file.name}")
        
        # Store session directory for cleanup
        if session_image_dir:
            uploaded_files[file_id + '_images'] = session_image_dir
        
        # Clean up markdown and fix image references
        cleaned_markdown = clean_markdown(markdown_content, file_info['filename'], temp_images)
        
        print(f"✅ Conversion complete: {len(cleaned_markdown)} characters")
        
        # Clean up temporary files
        shutil.rmtree(os.path.dirname(pdf_path))
        del uploaded_files[file_id]
        
        return {
            "markdown": cleaned_markdown,
            "status": "converted",
            "images": temp_images,
            "image_count": len(temp_images)
        }
        
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=500, detail="Conversion timed out (5 minutes)")
    except Exception as e:
        print(f"❌ Conversion error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")

def clean_markdown(content: str, filename: str, temp_image_urls: list = None) -> str:
    """Clean up markdown content and fix image references"""
    lines = content.split('\n')
    cleaned_lines = []
    
    title_set = False
    temp_image_urls = temp_image_urls or []
    image_index = 0
    
    for line in lines:
        # Skip page number patterns
        if line.strip().startswith('## Page ') and line.strip().endswith(line.strip().split()[-1].isdigit()):
            continue
            
        # Fix broken image references
        if line.strip().startswith('![](_page_') or '[Image #' in line:
            # Replace with actual image if available
            if image_index < len(temp_image_urls):
                image_url = temp_image_urls[image_index]
                cleaned_lines.append(f"![Figure {image_index + 1}]({image_url})")
                image_index += 1
            else:
                cleaned_lines.append("*[Figure/Image available in original PDF]*")
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

def extract_title_from_markdown(markdown: str) -> str:
    """Extract the H1 title from markdown content"""
    lines = markdown.split('\n')
    
    for line in lines:
        if line.startswith('# '):
            return line[2:].strip()
    
    return "Academic Paper"

def cleanup_old_temp_images():
    """Clean up temp images older than 1 hour"""
    temp_images_dir = Path("temp_images")
    if not temp_images_dir.exists():
        return
    
    current_time = time.time()
    for session_dir in temp_images_dir.iterdir():
        if session_dir.is_dir():
            # Extract timestamp from directory name
            try:
                if session_dir.name.startswith('session_'):
                    dir_timestamp = int(session_dir.name.split('_')[-1])
                    # Remove directories older than 1 hour (3600 seconds)
                    if current_time - dir_timestamp > 3600:
                        shutil.rmtree(session_dir)
                        print(f"🧹 Cleaned up old temp images: {session_dir.name}")
            except (ValueError, IndexError):
                # Skip directories with unexpected naming
                pass

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
        # Extract proper title from markdown H1
        extracted_title = extract_title_from_markdown(request.markdown)
        
        # Use filename as author (remove .pdf extension and clean up)
        author_from_filename = request.title.replace('.pdf', '').replace('_', ' ').replace('-', ' ')
        
        # Create temporary directory for pandoc
        temp_dir = tempfile.mkdtemp()
        md_path = os.path.join(temp_dir, 'document.md')
        epub_path = os.path.join(temp_dir, 'document.epub')
        
        # Copy images to temp directory and fix markdown paths
        markdown_content = request.markdown
        if '/temp_images/' in markdown_content:
            images_dir = os.path.join(temp_dir, 'images')
            os.makedirs(images_dir, exist_ok=True)
            
            # Find all image references and copy images
            import re
            image_pattern = r'!\[([^\]]*)\]\(/temp_images/([^/]+)/([^)]+)\)'
            
            def replace_image_path(match):
                alt_text = match.group(1)
                session_id = match.group(2)
                image_filename = match.group(3)
                
                # Copy image from temp_images to temp directory
                temp_session_path = os.path.join('temp_images', session_id, image_filename)
                epub_image_path = os.path.join(images_dir, image_filename)
                
                if os.path.exists(temp_session_path):
                    shutil.copy2(temp_session_path, epub_image_path)
                    print(f"📸 Copied image for EPUB: {image_filename}")
                    return f'![{alt_text}](images/{image_filename})'
                else:
                    print(f"⚠️ Image not found for EPUB: {temp_session_path}")
                    return match.group(0)  # Return original if image not found
            
            markdown_content = re.sub(image_pattern, replace_image_path, markdown_content)
        
        # Write markdown to temp file
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        # Use pandoc to convert markdown to EPUB
        result = subprocess.run([
            'pandoc',
            md_path,
            '-o', epub_path,
            f'--metadata=title:{extracted_title}',
            f'--metadata=author:{author_from_filename}',
            '--metadata=language:en',
            '--toc',  # Add table of contents
            '--toc-depth=3'
        ], capture_output=True, text=True, cwd=temp_dir)
        
        if result.returncode != 0:
            print(f"❌ Pandoc failed: {result.stderr}")
            shutil.rmtree(temp_dir)
            raise HTTPException(status_code=500, detail=f"EPUB generation failed: {result.stderr}")
        
        if not os.path.exists(epub_path):
            shutil.rmtree(temp_dir)
            raise HTTPException(status_code=500, detail="EPUB file was not created")
        
        print(f"✅ EPUB generated: {epub_path}")
        
        # Define cleanup function
        def cleanup_temp_dir():
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
        
        # Return the EPUB file
        return FileResponse(
            epub_path,
            media_type="application/epub+zip",
            filename=f"{extracted_title}.epub",
            background=cleanup_temp_dir
        )
        
    except Exception as e:
        if 'temp_dir' in locals() and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
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