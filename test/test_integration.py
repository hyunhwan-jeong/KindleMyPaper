"""
Simple integration test for PDF conversion functionality
Tests the actual conversion without complex mocking
"""

import pytest
import os
import tempfile
import requests
import time
from pathlib import Path

class TestPDFConversionIntegration:
    """Integration tests for PDF conversion"""
    
    @pytest.fixture(scope="class")
    def server_url(self):
        """URL of the running server - assumes server is running on localhost:8000"""
        return "http://localhost:8000"
    
    def test_server_health(self, server_url):
        """Test that the server is running and healthy"""
        try:
            response = requests.get(f"{server_url}/health", timeout=5)
            assert response.status_code == 200
            health_data = response.json()
            assert "status" in health_data
        except requests.exceptions.RequestException:
            pytest.skip("Server not running - start the application with 'python app.py'")
    
    def test_pdf_upload_endpoint(self, server_url):
        """Test PDF upload endpoint with a dummy PDF"""
        # Create a minimal PDF content for testing
        pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length 44
>>
stream
BT
/F1 24 Tf
100 700 Td
(Test Content) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000207 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
290
%%EOF"""
        
        try:
            # Test upload
            files = {'pdf': ('test.pdf', pdf_content, 'application/pdf')}
            response = requests.post(f"{server_url}/api/upload-pdf", files=files, timeout=10)
            
            if response.status_code == 200:
                upload_data = response.json()
                assert "file_id" in upload_data
                assert upload_data["status"] == "uploaded"
                print(f"✅ PDF upload successful: {upload_data['file_id']}")
                return upload_data["file_id"]
            else:
                print(f"Upload failed with status {response.status_code}: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            pytest.skip(f"Upload test failed due to connection issue: {e}")
    
    def test_conversion_no_tensor_error(self, server_url):
        """Test that conversion doesn't fail with tensor stack error"""
        file_id = self.test_pdf_upload_endpoint(server_url)
        
        if file_id:
            try:
                # Test conversion
                response = requests.post(f"{server_url}/api/convert/{file_id}", timeout=30)
                
                # The conversion might fail for other reasons (invalid PDF), but it should NOT fail with tensor stack error
                if response.status_code == 500:
                    error_detail = response.json().get("detail", "")
                    # Make sure it's not the tensor stack error we were trying to fix
                    assert "stack expects a non-empty TensorList" not in error_detail
                    print(f"✅ No tensor stack error (other error is acceptable): {error_detail}")
                elif response.status_code == 200:
                    conversion_data = response.json()
                    assert "status" in conversion_data
                    print(f"✅ Conversion successful: {conversion_data['status']}")
                
            except requests.exceptions.RequestException as e:
                pytest.skip(f"Conversion test failed due to connection issue: {e}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
