# 📚 KindleMyPaper

Convert Academic Papers (PDF) to Kindle-friendly EPUB format with AI-powered markdown editing.

## Features

- **PDF to Markdown**: Uses [marker](https://github.com/datalab-to/marker) library for high-quality PDF to markdown conversion
- **AI-Powered Editing**: Optional AI treatment to improve markdown formatting and fix OCR errors
- **EPUB Generation**: Creates Kindle-compatible EPUB files
- **Web Interface**: Simple, intuitive browser-based interface
- **Image Preservation**: Maintains images from original PDF

## Quick Start

### 1. Install Dependencies

```bash
# Clone the repository
git clone https://github.com/yourusername/KindleMyPaper.git
cd KindleMyPaper

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Optional: Set up AI Treatment

If you want AI-powered markdown treatment, create a `.env` file:

```bash
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. Run the Application

```bash
python app.py
```

The application will be available at `http://localhost:8000`

## Usage

1. **Upload PDF**: Drag and drop or select your academic paper (PDF format)
2. **Convert**: Click "Convert to Markdown" to process the PDF
3. **Edit**: Review and edit the markdown, optionally apply AI treatment
4. **Generate**: Click "Generate EPUB" to create the Kindle-compatible file
5. **Download**: Download your EPUB file

## System Requirements

- Python 3.10+
- At least 4GB RAM (for marker library)
- GPU recommended for faster processing (optional)

## Dependencies

- **FastAPI**: Web framework
- **marker-pdf**: PDF to markdown conversion
- **ebooklib**: EPUB generation
- **openai**: AI-powered treatment (optional)

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │     Backend      │    │    Libraries    │
│   (HTML/CSS/JS) │────│   (FastAPI)      │────│   marker-pdf    │
│                 │    │                  │    │   ebooklib      │
│   - File Upload │    │ - PDF Processing │    │   openai        │
│   - Markdown    │    │ - AI Treatment   │    │                 │
│   - EPUB Gen    │    │ - EPUB Creation  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## API Endpoints

- `GET /` - Main web interface
- `POST /api/convert-to-markdown` - Convert PDF to markdown
- `POST /api/apply-treatment` - Apply AI treatment to markdown
- `POST /api/generate-epub` - Generate EPUB from markdown
- `GET /health` - Health check and feature availability

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Acknowledgments

- [marker](https://github.com/datalab-to/marker) - Excellent PDF to markdown conversion
- [ebooklib](https://github.com/aerkalov/ebooklib) - EPUB generation
- Academic community for inspiration

## Troubleshooting

### Common Issues

1. **Marker installation fails**:
   ```bash
   # Install with conda if pip fails
   conda install -c conda-forge marker-pdf
   ```

2. **GPU not detected**:
   - Marker will automatically fall back to CPU
   - For faster processing, ensure CUDA is properly installed

3. **Large PDFs timeout**:
   - Consider splitting large PDFs into smaller sections
   - Increase timeout in app.py if needed

### Health Check

Visit `/health` endpoint to check which features are available:

```json
{
    "status": "healthy",
    "marker_available": true,
    "epub_available": true,
    "ai_available": true
}
```