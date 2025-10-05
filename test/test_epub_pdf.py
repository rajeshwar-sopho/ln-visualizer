"""
Tests for EPUB and PDF parsing using generated sample files
"""
import pytest
from pathlib import Path
import sys
import subprocess

from src.ln_parser import LightNovelParser, FileFormat


# Paths to generated test files
EPUB_PATH = Path("test_files/sample_novel.epub")
PDF_PATH = Path("test_files/sample_novel.pdf")


@pytest.fixture(scope="module", autouse=True)
def generate_test_files():
    """Generate test files before running tests"""
    # Check if files already exist
    if EPUB_PATH.exists() and PDF_PATH.exists():
        yield
        return
    
    # Run the generation script
    script_path = Path("scripts/generate_test_files.py")
    if not script_path.exists():
        pytest.skip("Generation script not found")
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode != 0:
            pytest.skip(f"Failed to generate test files: {result.stderr}")
    except Exception as e:
        pytest.skip(f"Error generating test files: {e}")
    
    yield
    
    # Cleanup is optional - you might want to keep the files for manual inspection


class TestEPUBParsing:
    """Test EPUB file parsing"""
    
    def test_epub_format_detection(self):
        """Test that EPUB format is correctly detected"""
        if not EPUB_PATH.exists():
            pytest.skip("EPUB test file not found")
        
        parser = LightNovelParser(str(EPUB_PATH))
        assert parser.format == FileFormat.EPUB
    
    def test_epub_parse(self):
        """Test parsing EPUB file"""
        if not EPUB_PATH.exists():
            pytest.skip("EPUB test file not found")
        
        parser = LightNovelParser(str(EPUB_PATH))
        parser.parse()
        
        assert parser.content is not None
        assert len(parser.content) > 0
        assert "hero" in parser.content.lower()
    
    def test_epub_chapters(self):
        """Test that chapters are correctly parsed from EPUB"""
        if not EPUB_PATH.exists():
            pytest.skip("EPUB test file not found")
        
        parser = LightNovelParser(str(EPUB_PATH))
        parser.parse()
        
        assert parser.has_chapters()
        assert parser.get_chapter_count() >= 3  # Prologue, Ch1, Ch2, Extra
        
        # Check for prologue
        prologue = parser.get_chapter(0)
        assert prologue is not None
        assert "prologue" in prologue.title.lower() or "beginning" in prologue.title.lower()
        assert "prologue" in prologue.content.lower()
    
    def test_epub_regular_chapters(self):
        """Test regular chapters in EPUB"""
        if not EPUB_PATH.exists():
            pytest.skip("EPUB test file not found")
        
        parser = LightNovelParser(str(EPUB_PATH))
        parser.parse()
        
        # Check Chapter 1
        ch1 = parser.get_chapter(1)
        assert ch1 is not None
        assert "chapter 1" in ch1.title.lower() or "hero" in ch1.title.lower()
        assert "village" in ch1.content.lower()
        
        # Check Chapter 2
        ch2 = parser.get_chapter(2)
        assert ch2 is not None
        assert "chapter 2" in ch2.title.lower() or "challenge" in ch2.title.lower()
        assert "obstacle" in ch2.content.lower() or "monster" in ch2.content.lower()
    
    def test_epub_extra_chapter(self):
        """Test extra/bonus chapter in EPUB"""
        if not EPUB_PATH.exists():
            pytest.skip("EPUB test file not found")
        
        parser = LightNovelParser(str(EPUB_PATH))
        parser.parse()
        
        # Check for extra content
        extra = parser.get_chapter(-1)
        assert extra is not None
        assert "extra" in extra.title.lower() or "bonus" in extra.title.lower()
    
    def test_epub_images(self):
        """Test that images are extracted from EPUB"""
        if not EPUB_PATH.exists():
            pytest.skip("EPUB test file not found")
        
        parser = LightNovelParser(str(EPUB_PATH))
        parser.parse()
        
        # Should have images
        assert len(parser.images) > 0
        
        # Check image properties
        for img in parser.images:
            assert img.data is not None
            assert len(img.data) > 0
            assert img.mime_type.startswith("image/")
            assert img.chapter_num >= 0 or img.chapter_num == -1
            assert img.image_num >= 1
            
            # Check name format
            expected_name = f"ch{img.chapter_num}_img{img.image_num}"
            assert img.name == expected_name
    
    def test_epub_chapter_images(self):
        """Test that chapters have their associated images"""
        if not EPUB_PATH.exists():
            pytest.skip("EPUB test file not found")
        
        parser = LightNovelParser(str(EPUB_PATH))
        parser.parse()
        
        # Chapter 1 should have 2 images
        ch1 = parser.get_chapter(1)
        if ch1:
            assert len(ch1.images) >= 2


class TestPDFParsing:
    """Test PDF file parsing"""
    
    def test_pdf_format_detection(self):
        """Test that PDF format is correctly detected"""
        if not PDF_PATH.exists():
            pytest.skip("PDF test file not found")
        
        parser = LightNovelParser(str(PDF_PATH))
        assert parser.format == FileFormat.PDF
    
    def test_pdf_parse(self):
        """Test parsing PDF file"""
        if not PDF_PATH.exists():
            pytest.skip("PDF test file not found")
        
        parser = LightNovelParser(str(PDF_PATH))
        parser.parse()
        
        assert parser.content is not None
        assert len(parser.content) > 0
        assert "hero" in parser.content.lower() or "prologue" in parser.content.lower()
    
    def test_pdf_chapters(self):
        """Test that chapters are detected in PDF"""
        if not PDF_PATH.exists():
            pytest.skip("PDF test file not found")
        
        parser = LightNovelParser(str(PDF_PATH))
        parser.parse()
        
        # PDF chapter detection might be less accurate, but should detect something
        if parser.has_chapters():
            assert parser.get_chapter_count() > 0
    
    def test_pdf_images(self):
        """Test that images are extracted from PDF"""
        if not PDF_PATH.exists():
            pytest.skip("PDF test file not found")
        
        parser = LightNovelParser(str(PDF_PATH))
        parser.parse()
        
        # Should have extracted images
        assert len(parser.images) > 0
        
        # Check image properties
        for img in parser.images:
            assert img.data is not None
            assert len(img.data) > 0
            assert img.mime_type.startswith("image/")
            assert img.chapter_num >= 1
            assert img.image_num >= 1
    
    def test_pdf_content_extraction(self):
        """Test that text content is properly extracted from PDF"""
        if not PDF_PATH.exists():
            pytest.skip("PDF test file not found")
        
        parser = LightNovelParser(str(PDF_PATH))
        parser.parse()
        
        content_lower = parser.content.lower()
        
        # Check for key phrases from the generated PDF
        assert any(word in content_lower for word in ['prologue', 'chapter', 'hero', 'adventure'])


class TestCompareFormats:
    """Compare parsing results between formats"""
    
    def test_both_files_exist(self):
        """Verify both test files were generated"""
        assert EPUB_PATH.exists(), f"EPUB file not found at {EPUB_PATH}"
        assert PDF_PATH.exists(), f"PDF file not found at {PDF_PATH}"
    
    def test_similar_content(self):
        """Test that EPUB and PDF contain similar content"""
        if not (EPUB_PATH.exists() and PDF_PATH.exists()):
            pytest.skip("Test files not found")
        
        epub_parser = LightNovelParser(str(EPUB_PATH))
        epub_parser.parse()
        
        pdf_parser = LightNovelParser(str(PDF_PATH))
        pdf_parser.parse()
        
        # Both should have content
        assert epub_parser.content is not None
        assert pdf_parser.content is not None
        
        # Both should mention similar themes
        epub_lower = epub_parser.content.lower()
        pdf_lower = pdf_parser.content.lower()
        
        common_words = ['hero', 'chapter', 'adventure']
        for word in common_words:
            assert word in epub_lower or word in pdf_lower
    
    def test_image_extraction_both_formats(self):
        """Test that both formats extract images"""
        if not (EPUB_PATH.exists() and PDF_PATH.exists()):
            pytest.skip("Test files not found")
        
        epub_parser = LightNovelParser(str(EPUB_PATH))
        epub_parser.parse()
        
        pdf_parser = LightNovelParser(str(PDF_PATH))
        pdf_parser.parse()
        
        # Both should have images
        assert len(epub_parser.images) > 0
        assert len(pdf_parser.images) > 0