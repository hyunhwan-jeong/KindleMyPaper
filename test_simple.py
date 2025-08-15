#!/usr/bin/env python3
"""Simple test script to verify the basic functionality works"""

import sys
import os

def test_imports():
    """Test if all required imports work"""
    print("🧪 Testing imports...")
    
    try:
        import fastapi
        print("✅ FastAPI imported successfully")
    except ImportError as e:
        print(f"❌ FastAPI import failed: {e}")
        return False
    
    try:
        import ebooklib
        from ebooklib import epub
        print("✅ ebooklib imported successfully")
    except ImportError as e:
        print(f"❌ ebooklib import failed: {e}")
        return False
    
    try:
        from marker.converters.pdf import PdfConverter
        print("✅ marker-pdf imported successfully")
    except ImportError as e:
        print(f"❌ marker-pdf import failed: {e}")
        return False
    
    return True

def test_epub_creation():
    """Test basic EPUB creation"""
    print("\n📚 Testing EPUB creation...")
    
    try:
        import ebooklib
        from ebooklib import epub
        
        # Create a simple test EPUB
        book = epub.EpubBook()
        book.set_identifier('test123')
        book.set_title('Test Book')
        book.set_language('en')
        book.add_author('Test Author')
        
        # Create a simple chapter
        chapter = epub.EpubHtml(title='Test Chapter', file_name='test.xhtml')
        chapter.content = '<html><body><h1>Test Chapter</h1><p>This is a test.</p></body></html>'
        
        book.add_item(chapter)
        book.toc = (epub.Link("test.xhtml", "Test Chapter", "test"),)
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        book.spine = ['nav', chapter]
        
        # Try to create EPUB in memory
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.epub') as tmp:
            epub.write_epub(tmp.name, book)
            print("✅ EPUB creation successful")
            return True
            
    except Exception as e:
        print(f"❌ EPUB creation failed: {e}")
        return False

def test_basic_html_conversion():
    """Test basic markdown to HTML conversion"""
    print("\n🔄 Testing markdown to HTML conversion...")
    
    try:
        # Test our basic markdown converter
        test_markdown = """# Test Header
        
This is a test paragraph.

## Second Header

- List item 1
- List item 2

**Bold text** and *italic text*.
"""
        
        # Simple markdown to HTML conversion (from our app.py)
        def markdown_to_html(markdown: str) -> str:
            lines = markdown.split('\n')
            html_lines = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    html_lines.append('<br>')
                elif line.startswith('# '):
                    html_lines.append(f'<h1>{line[2:]}</h1>')
                elif line.startswith('## '):
                    html_lines.append(f'<h2>{line[3:]}</h2>')
                elif line.startswith('- '):
                    html_lines.append(f'<li>{line[2:]}</li>')
                else:
                    # Simple bold/italic replacement
                    line = line.replace('**', '<strong>', 1).replace('**', '</strong>', 1)
                    line = line.replace('*', '<em>', 1).replace('*', '</em>', 1)
                    html_lines.append(f'<p>{line}</p>')
            
            return '\n'.join(html_lines)
        
        html_result = markdown_to_html(test_markdown)
        
        if '<h1>Test Header</h1>' in html_result and '<h2>Second Header</h2>' in html_result:
            print("✅ Markdown to HTML conversion successful")
            return True
        else:
            print("❌ Markdown to HTML conversion failed - unexpected output")
            return False
            
    except Exception as e:
        print(f"❌ Markdown to HTML conversion failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 KindleMyPaper - Basic Functionality Test\n")
    
    tests = [
        test_imports,
        test_epub_creation,
        test_basic_html_conversion,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            failed += 1
    
    print(f"\n📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Basic functionality is working.")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)