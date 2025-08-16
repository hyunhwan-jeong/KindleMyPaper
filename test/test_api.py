#!/usr/bin/env python3
"""
Test script to test KindleMyPaper API endpoints
"""

import requests
import time
import tempfile
import os

def download_test_pdf():
    """Download test PDF from arXiv"""
    url = "https://arxiv.org/pdf/2503.17587"
    print(f"📥 Downloading test PDF from {url}...")
    
    response = requests.get(url)
    if response.status_code != 200:
        print(f"❌ Failed to download PDF: {response.status_code}")
        return None
    
    # Save to temp file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    temp_file.write(response.content)
    temp_file.close()
    
    print(f"✅ Downloaded PDF: {temp_file.name} ({len(response.content)} bytes)")
    return temp_file.name

def test_api():
    """Test the KindleMyPaper API"""
    base_url = "http://localhost:8000"
    
    print(f"\n🧪 Testing KindleMyPaper API at {base_url}")
    print("=" * 50)
    
    # Step 1: Check health
    print("1️⃣ Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"Health check: {response.status_code}")
        if response.status_code == 200:
            health_data = response.json()
            print(f"   Status: {health_data.get('status')}")
            print(f"   Marker available: {health_data.get('marker_available')}")
            print(f"   Pandoc available: {health_data.get('pandoc_available')}")
        else:
            print(f"❌ Health check failed: {response.text}")
            return
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        print("Make sure the server is running at http://localhost:8000")
        return
    
    # Step 2: Download test PDF
    pdf_path = download_test_pdf()
    if not pdf_path:
        return
    
    try:
        # Step 3: Upload PDF
        print("\n2️⃣ Testing PDF upload...")
        with open(pdf_path, 'rb') as f:
            files = {'pdf': ('test_paper.pdf', f, 'application/pdf')}
            response = requests.post(f"{base_url}/api/upload-pdf", files=files)
        
        print(f"Upload status: {response.status_code}")
        if response.status_code == 200:
            upload_data = response.json()
            file_id = upload_data.get('file_id')
            print(f"   File ID: {file_id}")
            print(f"   Filename: {upload_data.get('filename')}")
            print(f"   Size: {upload_data.get('size')} bytes")
        else:
            print(f"❌ Upload failed: {response.text}")
            return
        
        # Step 4: Convert PDF
        print("\n3️⃣ Testing PDF conversion...")
        print("⏳ This may take a while with CPU processing...")
        
        start_time = time.time()
        response = requests.post(f"{base_url}/api/convert/{file_id}", timeout=600)  # 10 minutes
        end_time = time.time()
        
        print(f"Conversion status: {response.status_code}")
        print(f"Time taken: {end_time - start_time:.1f} seconds")
        
        if response.status_code == 200:
            convert_data = response.json()
            markdown = convert_data.get('markdown', '')
            print(f"✅ Conversion successful!")
            print(f"   Markdown length: {len(markdown)} characters")
            print(f"   First 200 characters:\n   {markdown[:200]}...")
            
            # Step 5: Test EPUB generation
            print("\n4️⃣ Testing EPUB generation...")
            epub_data = {
                'markdown': markdown,
                'title': 'Test Academic Paper'
            }
            response = requests.post(f"{base_url}/api/generate-epub", json=epub_data)
            
            print(f"EPUB generation status: {response.status_code}")
            if response.status_code == 200:
                print(f"✅ EPUB generated successfully!")
                print(f"   Content-Type: {response.headers.get('content-type')}")
                print(f"   Content-Length: {len(response.content)} bytes")
                
                # Save EPUB for inspection
                with open('test_output.epub', 'wb') as f:
                    f.write(response.content)
                print(f"   Saved as: test_output.epub")
            else:
                print(f"❌ EPUB generation failed: {response.text}")
        else:
            print(f"❌ Conversion failed: {response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out (10 minutes)")
    except Exception as e:
        print(f"❌ Error during API test: {e}")
    finally:
        # Cleanup
        if os.path.exists(pdf_path):
            os.unlink(pdf_path)
            print(f"\n🧹 Cleaned up temporary PDF file")

if __name__ == "__main__":
    test_api()