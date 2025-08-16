#!/usr/bin/env python3
"""
Simple test for Gemini AI treatment - focuses on the content preservation issue
"""

import os
import asyncio
import aiohttp
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Sample academic markdown content (simulating what marker would produce)
SAMPLE_MARKDOWN = """# Learning Transferable Visual Models From Natural Language Supervision

## Abstract

State-of-the-art computer vision systems are trained to predict a fixed set of predetermined object categories. This restricted form of supervision limits their generality and usability since additional labeled data is needed to specify any other visual concept. Learning directly from raw text about images is a promising alternative which leverages a much broader source of supervision. We demonstrate that the simple pre-training task of predicting which caption goes with which image is an efficient and scalable way to learn SOTA image representations from scratch on a dataset of 400 million (image, text) pairs collected from the internet. After pre-training, natural language is used to reference learned visual concepts (or describe new ones) enabling zero-shot transfer of the model to downstream tasks. We study the performance of this approach by benchmarking on over 30 different existing computer vision datasets, spanning tasks such as OCR, action recognition in videos, geo-localization, and many types of fine-grained object classification. The model transfers non-trivially to most tasks and is often competitive with a fully-supervised baseline without needing any task-specific training. For instance, we match the accuracy of the original ResNet-50 on ImageNet zero-shot without using any of the 1.28 million labeled examples it was trained on. We release our code and pre-trained model weights at https://github.com/OpenAI/CLIP.

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

async def test_gemini_content_preservation():
    """Test if Gemini preserves content length"""
    
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gemini-2.5-pro")
    
    if not api_key:
        print("❌ No API key found in environment")
        return
    
    print(f"🔍 Testing Gemini content preservation")
    print(f"🔧 Model: {model}")
    print(f"📊 Original content length: {len(SAMPLE_MARKDOWN)} characters")
    print("=" * 60)
    
    # Test different prompt approaches
    test_prompts = [
        {
            "name": "Current System Prompt",
            "system": """You are an expert academic paper processor. Your task is to improve the quality of markdown extracted from PDFs while preserving ALL content. Focus on:
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
- Process the entire document from beginning to end""",
            "user": "Fix any OCR errors and improve formatting, but preserve all content exactly."
        },
        {
            "name": "Emphasis on Length",
            "system": """You are a document editor. Your ONLY job is to fix OCR errors and formatting issues while keeping EXACTLY THE SAME CONTENT LENGTH.

CRITICAL RULES:
- DO NOT SUMMARIZE OR SHORTEN ANYTHING
- DO NOT REMOVE ANY SENTENCES OR PARAGRAPHS  
- DO NOT CHANGE THE MEANING
- ONLY fix obvious OCR mistakes like "rn" → "m", "cl" → "d", etc.
- ONLY improve markdown formatting
- The output must be nearly the same length as the input
- Return the COMPLETE document, every single section""",
            "user": "Fix OCR errors and formatting. Return the complete document with same length."
        }
    ]
    
    for i, prompt_config in enumerate(test_prompts, 1):
        print(f"\n🧪 Test {i}: {prompt_config['name']}")
        print("-" * 40)
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": f"{prompt_config['system']}\n\nUser instructions: {prompt_config['user']}\n\nMarkdown to process:\n\n{SAMPLE_MARKDOWN}"
                }]
            }],
            "generationConfig": {
                "thinkingConfig": {
                    "thinkingBudget": -1
                }
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'candidates' in data and data['candidates']:
                            raw_result = data['candidates'][0]['content']['parts'][0]['text']
                            
                            # Clean response
                            import re
                            cleaned_result = raw_result.strip()
                            cleaned_result = re.sub(r'^```\w*\n', '', cleaned_result, flags=re.MULTILINE)
                            cleaned_result = re.sub(r'\n```$', '', cleaned_result, flags=re.MULTILINE)
                            cleaned_result = re.sub(r'^```$', '', cleaned_result, flags=re.MULTILINE)
                            
                            print(f"📝 Raw response length: {len(raw_result)} characters")
                            print(f"🧹 Cleaned response length: {len(cleaned_result)} characters")
                            print(f"📊 Retention rate: {len(cleaned_result)/len(SAMPLE_MARKDOWN)*100:.1f}%")
                            
                            # Save for inspection
                            filename = f"test_result_{i}.md"
                            with open(filename, "w", encoding="utf-8") as f:
                                f.write(cleaned_result)
                            print(f"💾 Result saved to: {filename}")
                            
                            if len(cleaned_result) < len(SAMPLE_MARKDOWN) * 0.8:
                                print("⚠️  Content significantly shortened!")
                            else:
                                print("✅ Content length preserved well")
                            
                        else:
                            print(f"❌ Unexpected response format: {data}")
                    else:
                        error_data = await response.json()
                        print(f"❌ API error {response.status}: {error_data}")
        
        except Exception as e:
            print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_gemini_content_preservation())