#!/usr/bin/env python3
"""
Script to verify that the content preservation fixes are working
This can be run by the user to test the improvements
"""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from app import apply_direct_gemini_treatment, enhanced_markdown_treatment
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Sample academic content to test
TEST_CONTENT = """# Learning Transferable Visual Models From Natural Language Supervision

## Abstract

State-of-the-art computer vision systems are trained to predict a fixed set of predetermined object categories. This restricted form of supervision limits their generality and usability since additional labeled data is needed to specify any other visual concept. Learning directly from raw text about images is a promising alternative which leverages a much broader source of supervision. We demonstrate that the simple pre-training task of predicting which caption goes with which image is an efficient and scalable way to learn SOTA image representations from scratch on a dataset of 400 million (image, text) pairs collected from the internet.

After pre-training, natural language is used to reference learned visual concepts (or describe new ones) enabling zero-shot transfer of the model to downstream tasks. We study the performance of this approach by benchmarking on over 30 different existing computer vision datasets, spanning tasks such as OCR, action recognition in videos, geo-localization, and many types of fine-grained object classification. The model transfers non-trivially to most tasks and is often competitive with a fully-supervised baseline without needing any task-specific training.

For instance, we match the accuracy of the original ResNet-50 on ImageNet zero-shot without using any of the 1.28 million labeled examples it was trained on. We release our code and pre-trained model weights at https://github.com/OpenAI/CLIP.

## 1 Introduction

Learning from natural language supervision offers a promising alternative to the standard approach of learning from clean labeled datasets. Natural language provides a much broader and richer source of supervision for visual learning compared to gold standard "crowd-sourced labeling" which typically focuses on common objects and scenes. By learning to associate images with natural language descriptions, we can potentially build more generalizable visual representations.

The key insight underlying our approach is that natural language provides a natural way to specify visual concepts. Traditional computer vision systems require careful curation of labeled datasets for each task. In contrast, learning from text paired with images allows the model to learn about a much broader set of visual concepts through the abundant supervision available in text.

## 2 Approach

### 2.1 Natural Language Supervision

We demonstrate that natural language can be used as a training signal for learning visual representations. Our approach is motivated by work in natural language processing that has shown the effectiveness of learning from natural language supervision.

### 2.2 Creating a Sufficiently Large Dataset

Existing work has typically used datasets of up to a few hundred thousand image-text pairs. We created a new dataset of 400 million image-text pairs collected from a variety of publicly available sources on the internet.

### 2.3 Selecting an Efficient Pre-Training Method

We considered several approaches for learning from image-text pairs:

1. **Predictive objective**: Predict the exact words of the text given the image
2. **Contrastive objective**: Predict which text goes with which image

We found that the contrastive approach was significantly more efficient computationally while achieving better performance.

## 3 Experiments

### 3.1 Zero-Shot Transfer

We evaluate our pre-trained model on a wide variety of tasks in a zero-shot setting. Zero-shot transfer involves using the model on a new task without any task-specific training.

**Results on ImageNet**: Our model achieves 76.2% top-1 accuracy on ImageNet without using any of the 1.28 million labeled training examples. This matches the performance of the original ResNet-50 that was trained on the full ImageNet training set.

**Results on other datasets**: We evaluate on over 30 different existing computer vision datasets. Our model shows strong performance across a diverse range of tasks including:

- **OCR Tasks**: Street View House Numbers (SVHN), etc.
- **Action Recognition**: Kinetics-400, UCF-101
- **Fine-grained Classification**: Stanford Cars, Food-101
- **Geo-localization**: Various location datasets

### 3.2 Representation Learning

To understand what our model learns, we analyze the learned representations through various probing tasks and visualization techniques.

## 4 Comparison to Prior Work

Our work builds on several lines of research:

**Learning from web data**: Prior work has explored learning from noisy web-scale data. However, most approaches focus on curated datasets or require significant preprocessing.

**Vision-language models**: Several recent models have explored joint training on vision and language tasks. Our work differs in scale and the simplicity of the training objective.

**Zero-shot learning**: Traditional zero-shot learning typically relies on attribute descriptions or class embeddings. Our approach uses natural language descriptions directly.

## 5 Limitations

While our approach shows promising results, there are several limitations:

1. **Computational requirements**: Training requires significant computational resources
2. **Data quality**: The model can inherit biases present in the training data
3. **Performance gaps**: Zero-shot performance still lags behind fully supervised methods on some tasks

## 6 Broader Impacts

The development of more capable AI systems raises important questions about potential societal impacts. We discuss several considerations:

**Surveillance**: Improved computer vision capabilities could be used for surveillance applications
**Bias**: Models trained on internet data may perpetuate societal biases
**Job displacement**: Automation of visual recognition tasks may affect employment

## 7 Conclusion

We have shown that learning visual representations from natural language supervision is a promising approach that enables strong zero-shot transfer performance. By scaling up both the dataset size and model capacity, we achieve competitive results across a wide range of computer vision tasks without task-specific training.

Our work suggests that natural language provides a rich source of supervision for visual learning. Future work could explore even larger scales of training data and more sophisticated training objectives.

## References

[1] Radford, A., Kim, J. W., Hallacy, C., Ramesh, A., Goh, G., Agarwal, S., ... & Sutskever, I. (2021). Learning transferable visual models from natural language supervision. In International Conference on Machine Learning (pp. 8748-8763). PMLR.

[2] Additional references would be listed here in a real paper...

## Appendix

### A.1 Dataset Details

Our dataset consists of 400 million image-text pairs collected from various sources:
- Wikipedia articles and captions
- Image sharing websites  
- Social media platforms
- Stock photo websites

### A.2 Model Architecture

The model consists of two main components:
1. **Image Encoder**: A vision transformer or ResNet architecture
2. **Text Encoder**: A transformer-based language model

### A.3 Training Details

Training hyperparameters:
- Batch size: 32,768
- Learning rate: 5e-4 with cosine annealing
- Training steps: 400,000
- Hardware: 256 V100 GPUs"""

async def test_gemini_preservation():
    """Test Gemini content preservation with the updated prompts"""
    
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gemini-2.5-pro")
    
    if not api_key:
        print("⚠️  No API key found. Testing enhanced markdown treatment instead.")
        test_enhanced_treatment()
        return
    
    print("🔍 Testing Gemini Content Preservation")
    print("=" * 50)
    print(f"📊 Original content length: {len(TEST_CONTENT)} characters")
    print()
    
    # Test the improved prompt
    test_prompt = "Fix any OCR errors and improve formatting, but preserve all content exactly."
    
    try:
        result = await apply_direct_gemini_treatment(
            TEST_CONTENT,
            test_prompt,
            model,
            api_key
        )
        
        print()
        print("🎯 RESULTS:")
        print(f"   Original length: {len(TEST_CONTENT)} characters")
        print(f"   Result length: {len(result)} characters")
        print(f"   Retention rate: {len(result)/len(TEST_CONTENT)*100:.1f}%")
        
        if len(result) >= len(TEST_CONTENT) * 0.9:
            print("✅ SUCCESS: Content length preserved well!")
        elif len(result) >= len(TEST_CONTENT) * 0.7:
            print("⚠️  WARNING: Some content reduction, but acceptable")
        else:
            print("❌ FAILURE: Significant content loss detected")
        
        # Save results for inspection
        with open("test_original_content.md", "w", encoding="utf-8") as f:
            f.write(TEST_CONTENT)
        
        with open("test_gemini_result.md", "w", encoding="utf-8") as f:
            f.write(result)
        
        print()
        print("💾 Files saved:")
        print("   test_original_content.md - Original content")
        print("   test_gemini_result.md - Gemini processed content")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        print("Testing enhanced markdown treatment instead...")
        test_enhanced_treatment()

def test_enhanced_treatment():
    """Test the enhanced markdown treatment (non-AI fallback)"""
    
    print("🔍 Testing Enhanced Markdown Treatment (Fallback)")
    print("=" * 50)
    print(f"📊 Original content length: {len(TEST_CONTENT)} characters")
    
    # Test enhanced treatment
    result = enhanced_markdown_treatment(
        TEST_CONTENT, 
        "Fix OCR errors and improve formatting"
    )
    
    print()
    print("🎯 RESULTS:")
    print(f"   Original length: {len(TEST_CONTENT)} characters")
    print(f"   Result length: {len(result)} characters")
    print(f"   Retention rate: {len(result)/len(TEST_CONTENT)*100:.1f}%")
    
    if len(result) >= len(TEST_CONTENT) * 0.8:
        print("✅ SUCCESS: Enhanced treatment preserves content well!")
    else:
        print("⚠️  Some content variation in enhanced treatment")
    
    # Save results for inspection
    with open("test_enhanced_result.md", "w", encoding="utf-8") as f:
        f.write(result)
    
    print()
    print("💾 File saved: test_enhanced_result.md")

def main():
    """Main test function"""
    print("🧪 Content Preservation Verification Script")
    print("=" * 60)
    print()
    
    # Check if we can test with Gemini API
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key and api_key.startswith("AIza"):
        print("🔑 Gemini API key detected - testing with real API")
        asyncio.run(test_gemini_preservation())
    else:
        print("🔄 No valid API key - testing enhanced treatment only")
        test_enhanced_treatment()
    
    print()
    print("✅ Verification complete!")
    print()
    print("📝 How to interpret results:")
    print("   • 90%+ retention: Excellent content preservation")
    print("   • 70-90% retention: Good, minor acceptable losses")
    print("   • <70% retention: Poor, content being truncated")

if __name__ == "__main__":
    main()