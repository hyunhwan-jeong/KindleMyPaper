"""
Test PDF conversion functionality
"""

import pytest
import asyncio
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
import sys

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import convert_pdf, uploaded_files

# Configure pytest-asyncio
pytest_plugins = ('pytest_asyncio',)

class TestPDFConversion:
    """Test PDF conversion functionality"""
    
    @pytest.fixture
    def sample_pdf_path(self):
        """Create a mock PDF file for testing"""
        # Create a temporary PDF file (this would be a real PDF in practice)
        temp_dir = tempfile.mkdtemp()
        pdf_path = os.path.join(temp_dir, "test_paper.pdf")
        
        # Create a dummy PDF file (in real tests, you'd use a real PDF)
        with open(pdf_path, 'wb') as f:
            f.write(b"%PDF-1.4\n%Test PDF content")
        
        yield pdf_path
        
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def mock_file_info(self, sample_pdf_path):
        """Mock file info for uploaded PDF"""
        file_id = "test_paper"
        file_info = {
            'filename': 'test_paper.pdf',
            'path': sample_pdf_path,
            'size': 1024
        }
        uploaded_files[file_id] = file_info
        yield file_id, file_info
        
        # Cleanup
        if file_id in uploaded_files:
            del uploaded_files[file_id]
    
    @pytest.mark.asyncio
    async def test_conversion_success(self, mock_file_info):
        """Test successful PDF conversion"""
        file_id, file_info = mock_file_info
        
        # Mock marker conversion components
        with patch('app.create_model_dict') as mock_models, \
             patch('app.ConfigParser') as mock_config_parser, \
             patch('app.save_output') as mock_save_output, \
             patch('builtins.open', create=True) as mock_open, \
             patch('app.Path') as mock_path:
            
            # Setup mocks
            mock_models.return_value = {"mock": "models"}
            
            mock_config_instance = Mock()
            mock_config_parser.return_value = mock_config_instance
            mock_config_instance.get_converter_cls.return_value = Mock()
            mock_config_instance.get_processors.return_value = []
            mock_config_instance.get_renderer.return_value = Mock()
            mock_config_instance.get_llm_service.return_value = Mock()
            mock_config_instance.generate_config_dict.return_value = {}
            mock_config_instance.get_output_folder.return_value = "/tmp/output"
            mock_config_instance.get_base_filename.return_value = "test_paper"
            
            # Mock converter
            mock_converter_cls = mock_config_instance.get_converter_cls.return_value
            mock_converter = Mock()
            mock_converter_cls.return_value = mock_converter
            mock_converter.return_value = "mock_rendered_content"
            
            # Mock file operations
            mock_md_file = Mock()
            mock_md_file.name = "test_paper.md"
            mock_path.return_value.glob.return_value = [mock_md_file]
            
            mock_open.return_value.__enter__.return_value.read.return_value = "# Test Paper\n\nThis is test content."
            
            # Call the function
            result = await convert_pdf(file_id)
            
            # Assertions
            assert result["status"] == "converted"
            assert "markdown" in result
            assert "images" in result
            assert "image_count" in result
            assert len(result["markdown"]) > 0
    
    @pytest.mark.asyncio
    async def test_conversion_file_not_found(self):
        """Test conversion with non-existent file"""
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc_info:
            await convert_pdf("non_existent_file")
        
        # Should raise HTTPException with 404 status
        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail.lower()
    
    @pytest.mark.asyncio
    async def test_conversion_table_error_fallback(self, mock_file_info):
        """Test that table processing errors are handled gracefully"""
        file_id, file_info = mock_file_info
        
        with patch('app.create_model_dict') as mock_models, \
             patch('app.ConfigParser') as mock_config_parser:
            
            # Setup mocks to simulate table processing error
            mock_models.return_value = {"mock": "models"}
            
            mock_config_instance = Mock()
            mock_config_parser.return_value = mock_config_instance
            
            # Mock converter that raises the specific table error
            mock_converter_cls = Mock()
            mock_converter = Mock()
            mock_converter_cls.return_value = mock_converter
            mock_converter.side_effect = RuntimeError("stack expects a non-empty TensorList")
            
            mock_config_instance.get_converter_cls.return_value = mock_converter_cls
            mock_config_instance.get_processors.return_value = []
            mock_config_instance.get_renderer.return_value = Mock()
            mock_config_instance.get_llm_service.return_value = Mock()
            mock_config_instance.generate_config_dict.return_value = {}
            
            # The conversion should handle the error gracefully
            with pytest.raises(Exception) as exc_info:
                await convert_pdf(file_id)
            
            # Should contain helpful error message about table processing
            error_message = str(exc_info.value).lower()
            assert "table" in error_message or "complex" in error_message

if __name__ == "__main__":
    pytest.main([__file__])
