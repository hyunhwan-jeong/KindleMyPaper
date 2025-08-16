#!/usr/bin/env python3
"""
Test script for AI treatment functionality
Tests the full pipeline: PDF -> Markdown -> AI Treatment
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, os.getcwd())

from marker.models import create_model_dict
from marker.config.parser import ConfigParser
from marker.output import save_output
import asyncio
import aiohttp
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_ai_treatment_pipeline(pdf_path: str):
    """Test the complete AI treatment pipeline"""
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found: {pdf_path}")
        return
    
    print(f"🔍 Testing AI treatment pipeline with: {pdf_path}")
    print("=" * 60)
    
    # Step 1: Convert PDF to Markdown using Marker
    print("📄 Step 1: Converting PDF to Markdown...")
    
    try:
        models = create_model_dict()
        temp_dir = tempfile.mkdtemp()
        
        config_parser = ConfigParser({
            'output_dir': temp_dir,
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
        md_files = list(Path(out_folder).glob("*.md"))
        if not md_files:
            print("❌ No markdown file generated")
            return
        
        md_path = md_files[0]
        with open(md_path, 'r', encoding='utf-8') as f:
            original_markdown = f.read()
        
        print(f"✅ Markdown conversion complete:")
        print(f"   Original length: {len(original_markdown)} characters")
        print(f"   First 200 chars: {original_markdown[:200]}...")
        print()
        
        # Clean up temporary files
        shutil.rmtree(temp_dir)
        
    except Exception as e:
        print(f"❌ Markdown conversion failed: {e}")
        return
    
    # Step 2: Apply AI Treatment using Gemini
    print("🤖 Step 2: Applying AI Treatment with Gemini...")
    
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        model = os.getenv("OPENAI_MODEL", "gemini-2.5-pro")
        
        if not api_key:
            print("❌ No API key found in environment")
            return
        
        system_prompt = """You are an expert academic paper processor. Your task is to improve the quality of markdown extracted from PDFs while preserving ALL content. Focus on:
1. Fixing OCR errors and text recognition mistakes
2. Improving formatting and structure
3. Enhancing readability while preserving academic integrity
4. Correcting citation formats and references
5. Improving table and figure formatting

CRITICAL REQUIREMENTS:
- PRESERVE ALL ORIGINAL CONTENT - do not summarize, shorten, or omit any text
- Fix errors but keep the same length and detail level
- Maintain the complete document structure
- Return the FULL corrected document, not a summary
- Do not wrap in code blocks or add explanations
- Process the entire document from beginning to end"""
        
        user_prompt = """Read the given Markdown and correct it according to the following rules:
- Do not alter the meaning or context of the content.
- Do not paraphrase or rephrase sentences.
- If an image or text block is placed in the wrong position, move it to its correct location.
- Fix LaTeX or equation syntax errors to ensure proper rendering.
- Replace any incorrectly displayed symbols or special characters with their correct versions.
- Maintain valid Markdown formatting throughout.
- Fix common OCR errors while preserving academic terminology.
- Improve citation formatting and reference structure.
- Ensure proper heading hierarchy and document structure."""
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": f"{system_prompt}\n\nUser instructions: {user_prompt}\n\nMarkdown to process:\n\n{original_markdown}"
                }]
            }],
            "generationConfig": {
                "thinkingConfig": {
                    "thinkingBudget": -1
                }
            }
        }
        
        print(f"🔧 Using model: {model}")
        print(f"📊 Input length: {len(original_markdown)} characters")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'candidates' in data and data['candidates']:
                        raw_result = data['candidates'][0]['content']['parts'][0]['text']
                        
                        print(f"📝 Raw Gemini response length: {len(raw_result)} characters")
                        print(f"📝 First 200 chars of response: {raw_result[:200]}...")
                        print()
                        
                        # Clean response
                        import re
                        cleaned_result = raw_result.strip()
                        
                        # Remove markdown code blocks
                        cleaned_result = re.sub(r'^```\\w*\\n', '', cleaned_result, flags=re.MULTILINE)
                        cleaned_result = re.sub(r'\\n```$', '', cleaned_result, flags=re.MULTILINE)
                        cleaned_result = re.sub(r'^```$', '', cleaned_result, flags=re.MULTILINE)
                        
                        print(f"🧹 Cleaned response length: {len(cleaned_result)} characters")
                        print(f"📊 Compression ratio: {len(cleaned_result)/len(original_markdown)*100:.1f}%")
                        print()
                        
                        # Analysis
                        if len(cleaned_result) < len(original_markdown) * 0.8:
                            print("⚠️  WARNING: Significant content reduction detected!")
                            print(f"   Expected similar length (~{len(original_markdown)} chars)")
                            print(f"   Got: {len(cleaned_result)} chars")
                            print(f"   Loss: {len(original_markdown) - len(cleaned_result)} chars ({(1-len(cleaned_result)/len(original_markdown))*100:.1f}%)")
                        else:
                            print("✅ Content length preserved appropriately")
                        
                        # Save results for inspection
                        with open("test_original.md", "w", encoding="utf-8") as f:
                            f.write(original_markdown)
                        
                        with open("test_treated.md", "w", encoding="utf-8") as f:
                            f.write(cleaned_result)
                        
                        print("💾 Results saved:")
                        print("   test_original.md - Original markdown")
                        print("   test_treated.md - AI treated markdown")
                        
                    else:
                        print(f"❌ Unexpected response format: {data}")
                else:
                    error_data = await response.json()
                    print(f"❌ Gemini API error {response.status}: {error_data}")
        
    except Exception as e:
        print(f"❌ AI treatment failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    pdf_path = "/Volumes/SSD2TB/Downloads/2302.12854v2.pdf"
    asyncio.run(test_ai_treatment_pipeline(pdf_path))