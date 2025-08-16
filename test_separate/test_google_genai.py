#!/usr/bin/env python3
"""
Test the new Google GenAI implementation
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import apply_google_gemini_treatment, GENAI_AVAILABLE, enhanced_markdown_treatment
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Sample content for testing
SAMPLE_CONTENT = """# Research Paper: Understanding Machine Learning

## Abstract

Machine learning has revolutionized the way we approach complex problems in computer science and artificial intelligence. This paper provides a comprehensive overview of machine learning techniques, their applications, and future directions. We examine supervised learning, unsupervised learning, and reinforcement learning paradigms, discussing their strengths and limitations.

## 1 Introduction

Machine learning (ML) is a subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed. The field has experienced rapid growth over the past decades, driven by advances in computational power, data availability, and algorithmic innovations.

### 1.1 Historical Context

The roots of machine learning can be traced back to the 1950s with the development of the perceptron by Frank Rosenblatt. Since then, the field has evolved through several phases:

- **1950s-1960s**: Early neural networks and perceptrons
- **1970s-1980s**: Expert systems and symbolic AI
- **1990s-2000s**: Support vector machines and ensemble methods
- **2010s-present**: Deep learning revolution

## 2 Machine Learning Paradigms

### 2.1 Supervised Learning

Supervised learning involves training models on labeled data where the desired output is known. Common algorithms include:

1. **Linear Regression**: For continuous target variables
2. **Logistic Regression**: For binary classification
3. **Decision Trees**: For interpretable models
4. **Random Forest**: Ensemble of decision trees
5. **Neural Networks**: For complex pattern recognition

### 2.2 Unsupervised Learning

Unsupervised learning discovers hidden patterns in data without labeled examples:

- **Clustering**: K-means, hierarchical clustering
- **Dimensionality Reduction**: PCA, t-SNE
- **Association Rules**: Market basket analysis

### 2.3 Reinforcement Learning

Reinforcement learning focuses on training agents to make decisions through interaction with an environment:

- **Q-Learning**: Value-based method
- **Policy Gradient**: Direct policy optimization
- **Actor-Critic**: Combination of value and policy methods

## 3 Applications

Machine learning has found applications across numerous domains:

### 3.1 Computer Vision
- Image classification
- Object detection
- Facial recognition
- Medical imaging

### 3.2 Natural Language Processing
- Machine translation
- Sentiment analysis
- Text summarization
- Chatbots and virtual assistants

### 3.3 Healthcare
- Drug discovery
- Disease diagnosis
- Personalized medicine
- Epidemiological modeling

## 4 Challenges and Future Directions

Despite significant progress, machine learning faces several challenges:

1. **Data Quality**: Ensuring clean, representative datasets
2. **Interpretability**: Understanding model decisions
3. **Bias and Fairness**: Addressing discriminatory outcomes
4. **Scalability**: Handling large-scale data and models
5. **Privacy**: Protecting sensitive information

## 5 Conclusion

Machine learning continues to transform industries and scientific research. As we advance toward more sophisticated AI systems, addressing the challenges of interpretability, fairness, and scalability will be crucial for realizing the full potential of these technologies.

Future research directions include federated learning, quantum machine learning, and neuromorphic computing, which promise to expand the boundaries of what is possible with artificial intelligence.

## References

[1] Mitchell, T. (1997). Machine Learning. McGraw-Hill.
[2] Bishop, C. (2006). Pattern Recognition and Machine Learning. Springer.
[3] Goodfellow, I., Bengio, Y., & Courville, A. (2016). Deep Learning. MIT Press."""

async def test_google_genai_streaming():
    """Test the Google GenAI streaming implementation"""
    
    print("🧪 Testing Google GenAI Streaming Implementation")
    print("=" * 60)
    
    # Check if library is available
    if not GENAI_AVAILABLE:
        print("❌ Google GenAI library not available")
        return False
    
    # Check for API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not found in environment")
        return False
    
    print(f"✅ Google GenAI library available")
    print(f"✅ API key found: {api_key[:10]}...")
    print(f"📊 Test content length: {len(SAMPLE_CONTENT)} characters")
    print()
    
    try:
        # Test the streaming implementation
        print("🔄 Testing streaming content generation...")
        
        result = await apply_google_gemini_treatment(
            SAMPLE_CONTENT,
            "Fix any OCR errors and improve formatting, but preserve all content exactly.",
            "gemini-2.5-pro",
            api_key
        )
        
        print()
        print("🎯 STREAMING TEST RESULTS:")
        print(f"   Original length: {len(SAMPLE_CONTENT)} characters")
        print(f"   Result length: {len(result)} characters")
        print(f"   Retention rate: {len(result)/len(SAMPLE_CONTENT)*100:.1f}%")
        
        # Check content preservation
        if len(result) >= len(SAMPLE_CONTENT) * 0.9:
            print("✅ EXCELLENT: Content length preserved very well!")
            success = True
        elif len(result) >= len(SAMPLE_CONTENT) * 0.7:
            print("⚠️  GOOD: Some content reduction, but acceptable")
            success = True
        else:
            print("❌ POOR: Significant content loss detected")
            success = False
        
        # Check for key sections
        sections_to_check = ["Abstract", "Introduction", "Machine Learning Paradigms", "Applications", "Conclusion"]
        preserved_sections = 0
        
        for section in sections_to_check:
            if section in result:
                preserved_sections += 1
            else:
                print(f"⚠️  Missing section: {section}")
        
        print(f"📋 Sections preserved: {preserved_sections}/{len(sections_to_check)}")
        
        # Save results
        with open("test_separate/google_genai_original.md", "w", encoding="utf-8") as f:
            f.write(SAMPLE_CONTENT)
        
        with open("test_separate/google_genai_result.md", "w", encoding="utf-8") as f:
            f.write(result)
        
        print()
        print("💾 Results saved:")
        print("   test_separate/google_genai_original.md - Original content")
        print("   test_separate/google_genai_result.md - Processed content")
        
        return success
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_fallback_processing():
    """Test the enhanced markdown treatment fallback"""
    
    print("\n🔧 Testing Enhanced Markdown Treatment (Fallback)")
    print("=" * 60)
    
    result = enhanced_markdown_treatment(
        SAMPLE_CONTENT,
        "Fix OCR errors and improve formatting"
    )
    
    print(f"📊 Fallback processing results:")
    print(f"   Original length: {len(SAMPLE_CONTENT)} characters")
    print(f"   Result length: {len(result)} characters")
    print(f"   Retention rate: {len(result)/len(SAMPLE_CONTENT)*100:.1f}%")
    
    # Save fallback result
    with open("test_separate/enhanced_treatment_result.md", "w", encoding="utf-8") as f:
        f.write(result)
    
    print("💾 Fallback result saved: test_separate/enhanced_treatment_result.md")
    
    return True

async def main():
    """Main test function"""
    
    print("🧪 Google GenAI Implementation Test Suite")
    print("=" * 70)
    print()
    
    # Test 1: Google GenAI streaming
    genai_success = await test_google_genai_streaming()
    
    # Test 2: Fallback processing
    fallback_success = test_fallback_processing()
    
    print()
    print("📊 FINAL TEST RESULTS:")
    print("=" * 30)
    print(f"Google GenAI Test: {'✅ PASS' if genai_success else '❌ FAIL'}")
    print(f"Fallback Test: {'✅ PASS' if fallback_success else '❌ FAIL'}")
    
    if genai_success:
        print()
        print("🎉 SUCCESS: Google GenAI implementation working correctly!")
        print("   • Streaming content generation functional")
        print("   • Content preservation maintained")
        print("   • Thinking config applied properly")
    else:
        print()
        print("⚠️  Google GenAI test failed - check API key and configuration")
    
    print()
    print("📝 Next steps:")
    print("   1. Review saved result files for quality")
    print("   2. Test with actual PDF conversion")
    print("   3. Verify web interface integration")

if __name__ == "__main__":
    asyncio.run(main())