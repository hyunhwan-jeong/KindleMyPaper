"""
Unit tests for AI treatment functionality
"""

import pytest
import asyncio
import os
from unittest.mock import Mock, patch, AsyncMock
import sys
import tempfile
import shutil

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import (
    apply_openai_treatment,
    apply_direct_gemini_treatment,
    clean_gemini_response,
    enhanced_markdown_treatment,
    clean_markdown,
    extract_title_from_markdown
)

# Configure pytest-asyncio
pytest_plugins = ('pytest_asyncio',)

class TestCleanGeminiResponse:
    """Test the Gemini response cleaning function"""
    
    def test_remove_markdown_code_blocks(self):
        """Test removal of markdown code blocks"""
        input_text = "```markdown\n# Title\nContent here\n```"
        expected = "# Title\nContent here"
        result = clean_gemini_response(input_text)
        assert result == expected
    
    def test_remove_explanation_sections(self):
        """Test removal of explanation sections"""
        input_text = """# Main Content
This is the main content.

### Explanation
This is an explanation that should be removed."""
        
        expected = "# Main Content\nThis is the main content."
        result = clean_gemini_response(input_text)
        assert result == expected
    
    def test_preserve_academic_content(self):
        """Test that academic content is preserved"""
        input_text = """# Research Paper
## Abstract
This is important academic content.
## Introduction
More academic content here."""
        
        result = clean_gemini_response(input_text)
        assert "Research Paper" in result
        assert "Abstract" in result
        assert "Introduction" in result
        assert "academic content" in result
    
    def test_handle_separator_explanations(self):
        """Test handling of separator-based explanations"""
        input_text = """# Main Content
Real content here.
---
Explanation: This part should be removed."""
        
        result = clean_gemini_response(input_text)
        assert "Real content here." in result
        assert "Explanation:" not in result

class TestContentPreservation:
    """Test content length preservation in AI treatment"""
    
    @pytest.fixture
    def sample_academic_content(self):
        """Sample academic markdown content"""
        return """# Machine Learning in Computer Vision

## Abstract
Computer vision has been revolutionized by machine learning techniques, particularly deep learning. This paper reviews the current state of machine learning applications in computer vision, including object detection, image classification, and semantic segmentation. We discuss recent advances in convolutional neural networks, transformer architectures, and their applications to various computer vision tasks.

## 1 Introduction
Computer vision is a field of artificial intelligence that focuses on enabling computers to interpret and understand visual information from the world. Traditional computer vision methods relied heavily on hand-crafted features and classical machine learning algorithms. However, the advent of deep learning has fundamentally changed the landscape of computer vision research and applications.

The integration of machine learning, particularly deep learning, into computer vision has led to unprecedented performance improvements across various tasks. From image classification to object detection, semantic segmentation to image generation, machine learning techniques have become the backbone of modern computer vision systems.

## 2 Deep Learning Architectures

### 2.1 Convolutional Neural Networks
Convolutional Neural Networks (CNNs) have been the dominant architecture for computer vision tasks for over a decade. Key innovations include:

- **LeNet**: One of the earliest CNN architectures
- **AlexNet**: Demonstrated the power of deep learning for image classification
- **VGG**: Showed the importance of depth in neural networks
- **ResNet**: Introduced residual connections to enable very deep networks
- **DenseNet**: Connected each layer to every other layer in a feed-forward fashion

### 2.2 Transformer Architectures
Recently, transformer architectures originally designed for natural language processing have been successfully adapted for computer vision tasks:

- **Vision Transformer (ViT)**: Applies transformers directly to image patches
- **DETR**: Detection Transformer for object detection
- **Swin Transformer**: Hierarchical vision transformer with shifted windows

## 3 Applications

### 3.1 Image Classification
Image classification remains one of the most fundamental computer vision tasks. Modern deep learning approaches have achieved superhuman performance on datasets like ImageNet.

### 3.2 Object Detection
Object detection involves both localizing and classifying objects within images. Popular approaches include:
- R-CNN family (R-CNN, Fast R-CNN, Faster R-CNN)
- YOLO (You Only Look Once) series
- SSD (Single Shot MultiBox Detector)

### 3.3 Semantic Segmentation
Semantic segmentation assigns a class label to every pixel in an image. Key architectures include:
- FCN (Fully Convolutional Networks)
- U-Net
- DeepLab series

## 4 Challenges and Future Directions

Despite significant progress, several challenges remain:

1. **Data Efficiency**: Current methods require large amounts of labeled data
2. **Robustness**: Models can be sensitive to adversarial attacks
3. **Interpretability**: Deep learning models are often considered "black boxes"
4. **Computational Requirements**: State-of-the-art models require significant computational resources

## 5 Conclusion

Machine learning, particularly deep learning, has transformed computer vision from a field struggling with basic tasks to one achieving superhuman performance on many benchmarks. As we move forward, addressing challenges related to data efficiency, robustness, and interpretability will be crucial for the continued advancement of the field.

## References

[1] LeCun, Y., Bottou, L., Bengio, Y., & Haffner, P. (1998). Gradient-based learning applied to document recognition.
[2] Krizhevsky, A., Sutskever, I., & Hinton, G. E. (2012). ImageNet classification with deep convolutional neural networks.
[3] Simonyan, K., & Zisserman, A. (2014). Very deep convolutional networks for large-scale image recognition."""

    def test_content_length_preservation(self, sample_academic_content):
        """Test that content length is preserved in enhanced treatment"""
        original_length = len(sample_academic_content)
        result = enhanced_markdown_treatment(sample_academic_content, "Fix OCR errors")
        
        # Allow some variation but not dramatic reduction
        length_ratio = len(result) / original_length
        assert length_ratio > 0.8, f"Content too short: {len(result)} vs {original_length} (ratio: {length_ratio:.2f})"
        assert length_ratio < 1.5, f"Content too long: {len(result)} vs {original_length} (ratio: {length_ratio:.2f})"
    
    def test_preserve_structure(self, sample_academic_content):
        """Test that document structure is preserved"""
        result = enhanced_markdown_treatment(sample_academic_content, "Fix formatting")
        
        # Check that main sections are preserved
        assert "# Machine Learning in Computer Vision" in result
        assert "## Abstract" in result
        assert "## 1 Introduction" in result
        assert "### 2.1 Convolutional Neural Networks" in result
        assert "## References" in result

class TestGeminiIntegration:
    """Test Gemini API integration"""
    
    @pytest.fixture
    def mock_gemini_response(self):
        """Mock successful Gemini API response"""
        return {
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": "# Corrected Document\n\nThis is the corrected content with proper formatting."
                    }]
                }
            }]
        }
    
    @pytest.fixture
    def mock_error_response(self):
        """Mock error response from Gemini API"""
        return {
            "error": {
                "code": 400,
                "message": "Invalid request"
            }
        }
    
    @pytest.mark.asyncio
    async def test_gemini_successful_response(self, mock_gemini_response):
        """Test successful Gemini API call"""
        with patch('aiohttp.ClientSession.post') as mock_post:
            # Setup mock response
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_gemini_response)
            mock_post.return_value.__aenter__.return_value = mock_response
            
            # Test the function
            result = await apply_direct_gemini_treatment(
                "# Test Document\nContent here",
                "Fix errors",
                "gemini-2.5-pro",
                "test-api-key"
            )
            
            assert "Corrected Document" in result
            assert len(result) > 0
    
    @pytest.mark.asyncio
    async def test_gemini_error_handling(self, mock_error_response):
        """Test Gemini API error handling"""
        with patch('aiohttp.ClientSession.post') as mock_post:
            # Setup mock error response
            mock_response = AsyncMock()
            mock_response.status = 400
            mock_response.json = AsyncMock(return_value=mock_error_response)
            mock_post.return_value.__aenter__.return_value = mock_response
            
            # Test that exception is raised
            with pytest.raises(Exception) as exc_info:
                await apply_direct_gemini_treatment(
                    "# Test Document\nContent here",
                    "Fix errors",
                    "gemini-2.5-pro",
                    "test-api-key"
                )
            
            assert "Gemini API error 400" in str(exc_info.value)

class TestMarkdownProcessing:
    """Test markdown processing utilities"""
    
    def test_extract_title_from_markdown(self):
        """Test title extraction from markdown"""
        markdown_with_title = "# Research Paper Title\n\nContent here..."
        title = extract_title_from_markdown(markdown_with_title)
        assert title == "Research Paper Title"
        
        # Test fallback
        markdown_without_title = "Content without title..."
        title = extract_title_from_markdown(markdown_without_title)
        assert title == "Academic Paper"
    
    def test_clean_markdown_image_handling(self):
        """Test image reference cleaning in markdown"""
        content = """# Test Paper
        
![](_page_1_image.png)
[Image #1] broken reference
Some content here."""
        
        image_urls = ["/temp_images/session_123/figure1.png"]
        result = clean_markdown(content, "test.pdf", image_urls)
        
        # Should fix broken image references with the specific pattern the function looks for
        assert "![Figure 1](/temp_images/session_123/figure1.png)" in result
    
    def test_clean_markdown_title_handling(self):
        """Test title cleaning in markdown"""
        content = """# test.pdf

## Introduction
Content here..."""
        
        result = clean_markdown(content, "test.pdf", [])
        
        # Should not have duplicate filename title
        lines = result.split('\n')
        title_lines = [line for line in lines if line.startswith('# ')]
        assert len(title_lines) <= 1

class TestContentTruncationPrevention:
    """Tests to prevent content truncation issues"""
    
    def test_long_content_preservation(self):
        """Test that long academic content is preserved"""
        # Create a long academic document
        long_content = """# Comprehensive Research Study

## Abstract
""" + "This is a very detailed abstract that contains important information. " * 20 + """

## Introduction
""" + "The introduction provides crucial context and background information that cannot be omitted. " * 30 + """

## Methodology
""" + "Our methodology involves several complex steps that must be documented in detail. " * 25 + """

## Results
""" + "The results section contains critical findings that support our conclusions. " * 40 + """

## Discussion
""" + "The discussion analyzes our findings in the context of existing literature. " * 35 + """

## Conclusion
""" + "Our conclusions summarize the key contributions of this research work. " * 15
        
        original_length = len(long_content)
        
        # Test enhanced treatment
        result = enhanced_markdown_treatment(long_content, "Fix minor errors")
        
        # Should preserve most content
        retention_ratio = len(result) / original_length
        assert retention_ratio > 0.90, f"Too much content lost: {retention_ratio:.2%} retained"
        
        # Should preserve all major sections
        sections = ["Abstract", "Introduction", "Methodology", "Results", "Discussion", "Conclusion"]
        for section in sections:
            assert section in result, f"Section '{section}' was removed"

class TestPromptOptimization:
    """Test different prompt strategies for content preservation"""
    
    @pytest.fixture
    def content_preservation_prompts(self):
        """Different prompt strategies to test"""
        return [
            {
                "name": "Length Emphasis",
                "system": "Preserve ALL content length. Do not summarize or shorten anything.",
                "user": "Fix errors but keep exact same length"
            },
            {
                "name": "Section Preservation", 
                "system": "Maintain every section and paragraph. Only fix obvious errors.",
                "user": "Fix formatting while preserving all sections"
            },
            {
                "name": "Academic Integrity",
                "system": "This is an academic document. Preserve all research content.",
                "user": "Improve readability without losing academic content"
            }
        ]
    
    def test_prompt_strategies(self, content_preservation_prompts):
        """Test that different prompt strategies preserve content"""
        # Use a sample content for testing
        sample_content = """# Research Paper
## Abstract
This is important research content that should not be shortened.
## Introduction
Detailed introduction with multiple paragraphs of content.
## Conclusion
Final thoughts and research outcomes."""
        
        for prompt_config in content_preservation_prompts:
            # Simulate what would happen with the prompt
            # (In real test, this would call the AI service)
            result = enhanced_markdown_treatment(
                sample_content, 
                prompt_config["user"]
            )
            
            # Verify content preservation
            original_length = len(sample_content)
            result_length = len(result)
            retention_ratio = result_length / original_length
            
            assert retention_ratio > 0.8, f"Prompt '{prompt_config['name']}' caused too much content loss"

class TestRealWorldScenarios:
    """Test real-world usage scenarios"""
    
    def test_pdf_conversion_pipeline(self):
        """Test the complete PDF processing pipeline (without actual PDF)"""
        # Simulate what marker would produce
        simulated_marker_output = """# 2023 Annual Report

## Executive Summary
This report summarizes our findings...

![Image #1](_page_1_image.png)

## Financial Results
Our financial performance this year...

### Revenue Analysis
Revenue increased by 15%...

### Cost Structure
Operating costs were managed effectively...

## Future Outlook
Looking ahead to next year..."""
        
        # Test cleaning
        cleaned = clean_markdown(simulated_marker_output, "annual_report.pdf", [])
        
        # Should have proper title
        assert "# 2023 Annual Report" in cleaned or "# Annual Report" in cleaned
        
        # Should handle broken image references
        assert "[Image #1]" not in cleaned or "*[Figure/Image available in original PDF]*" in cleaned
    
    def test_error_recovery(self):
        """Test recovery from various error conditions"""
        # Test with malformed markdown
        malformed_markdown = "# Title\n\nSome content...\n**Bold without closing\n\nMore content..."
        
        result = enhanced_markdown_treatment(malformed_markdown, "Fix formatting")
        
        # Should still preserve content even with formatting issues
        assert "Title" in result
        assert "Some content" in result
        assert "More content" in result

# Integration test that can be run manually with real API
@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_gemini_integration():
    """Integration test with real Gemini API - requires API key"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("No API key available for integration test")
    
    test_content = """# Test Document

## Introduction
This is a test document to verify that Gemini preserves content length properly.

## Content
Here is some content that should be preserved in its entirety without summarization or truncation."""
    
    result = await apply_direct_gemini_treatment(
        test_content,
        "Fix any minor errors but preserve all content",
        "gemini-2.5-pro",
        api_key
    )
    
    # Check content preservation
    original_length = len(test_content)
    result_length = len(result)
    retention_ratio = result_length / original_length
    
    assert retention_ratio > 0.8, f"Real API test failed: only {retention_ratio:.2%} content retained"
    assert "Test Document" in result
    assert "Introduction" in result

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])