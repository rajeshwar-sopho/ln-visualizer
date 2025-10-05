import pytest
from pathlib import Path
import tempfile
import base64
from src.ln_parser import (
    LightNovelParser,
    FileFormat,
    Chapter,
    ImageData
)


@pytest.fixture
def temp_txt_file():
    """Create a temporary text file with chapter structure"""
    content = """Prologue: The Beginning

This is the prologue content.
It sets up the story.

Chapter 1: First Adventure

This is the first chapter.
The hero begins their journey.

Chapter 2: The Challenge

The hero faces their first challenge.
They must overcome obstacles.

Extra: Bonus Content

This is extra content after the main story.
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(content)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


@pytest.fixture
def temp_simple_txt_file():
    """Create a simple text file without chapters"""
    content = "This is a simple light novel without chapter markers.\nJust plain text content."
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(content)
        temp_path = f.name
    
    yield temp_path
    
    Path(temp_path).unlink(missing_ok=True)


class TestLightNovelParser:
    """Test cases for LightNovelParser"""
    
    def test_detect_format_txt(self, temp_txt_file):
        """Test format detection for TXT files"""
        parser = LightNovelParser(temp_txt_file)
        assert parser.format == FileFormat.TXT
    
    def test_file_not_found(self):
        """Test error when file doesn't exist"""
        with pytest.raises(FileNotFoundError):
            LightNovelParser("nonexistent_file.txt")
    
    def test_unsupported_format(self):
        """Test error for unsupported file format"""
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as f:
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError, match="Unsupported file format"):
                LightNovelParser(temp_path)
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def test_parse_simple_txt(self, temp_simple_txt_file):
        """Test parsing simple text without chapters"""
        parser = LightNovelParser(temp_simple_txt_file)
        parser.parse()
        
        assert parser.content is not None
        assert "simple light novel" in parser.content
        assert len(parser.content) > 0
    
    def test_parse_txt_with_chapters(self, temp_txt_file):
        """Test parsing text file with chapter markers"""
        parser = LightNovelParser(temp_txt_file)
        parser.parse()
        
        assert parser.content is not None
        assert parser.has_chapters()
        assert parser.get_chapter_count() > 0
        
        # Check for prologue (chapter 0)
        prologue = parser.get_chapter(0)
        assert prologue is not None
        assert "prologue" in prologue.title.lower()
        
        # Check for regular chapters
        ch1 = parser.get_chapter(1)
        assert ch1 is not None
        assert "First Adventure" in ch1.title or "1" in ch1.title
        
        # Check for extras (chapter -1)
        extra = parser.get_chapter(-1)
        assert extra is not None
        assert "extra" in extra.title.lower() or "bonus" in extra.title.lower()
    
    def test_chapter_number_detection(self, temp_txt_file):
        """Test chapter number detection logic"""
        parser = LightNovelParser(temp_txt_file)
        parser.parse()
        
        # Test prologue detection
        assert parser._detect_chapter_number("Prologue: Start", 99) == 0
        assert parser._detect_chapter_number("Introduction", 99) == 0
        
        # Test extra detection
        assert parser._detect_chapter_number("Extra: Bonus", 99) == -1
        assert parser._detect_chapter_number("Epilogue", 99) == -1
        
        # Test regular chapter detection
        assert parser._detect_chapter_number("Chapter 5", 99) == 5
        assert parser._detect_chapter_number("Ch. 10", 99) == 10
        
        # Test default
        assert parser._detect_chapter_number("Some Random Title", 42) == 42
    
    def test_roman_numeral_parsing(self, temp_txt_file):
        """Test parsing of Roman numerals in chapter numbers"""
        parser = LightNovelParser(temp_txt_file)
        
        assert parser._parse_chapter_number("I") == 1
        assert parser._parse_chapter_number("V") == 5
        assert parser._parse_chapter_number("X") == 10
        assert parser._parse_chapter_number("IV") == 4
        assert parser._parse_chapter_number("IX") == 9
        assert parser._parse_chapter_number("XIV") == 14
    
    def test_get_chapter(self, temp_txt_file):
        """Test getting specific chapters"""
        parser = LightNovelParser(temp_txt_file)
        parser.parse()
        
        # Test getting existing chapter
        ch1 = parser.get_chapter(1)
        assert ch1 is not None
        assert isinstance(ch1, Chapter)
        
        # Test getting non-existent chapter
        ch_none = parser.get_chapter(999)
        assert ch_none is None
    
    def test_chapter_model(self):
        """Test Chapter Pydantic model"""
        chapter = Chapter(
            number=1,
            title="Test Chapter",
            content="This is test content",
            images=[]
        )
        
        assert chapter.number == 1
        assert chapter.title == "Test Chapter"
        assert chapter.content == "This is test content"
        assert len(chapter.images) == 0
    
    def test_image_data_model(self):
        """Test ImageData Pydantic model"""
        img_data = ImageData(
            chapter_num=1,
            image_num=2,
            data=base64.b64encode(b"fake_image_data").decode('utf-8'),
            mime_type="image/png"
        )
        
        assert img_data.chapter_num == 1
        assert img_data.image_num == 2
        assert img_data.name == "ch1_img2"
        assert img_data.mime_type == "image/png"
    
    def test_chapter_boundary_detection(self, temp_txt_file):
        """Test chapter boundary detection"""
        parser = LightNovelParser(temp_txt_file)
        
        assert parser._is_chapter_boundary("Chapter 1")
        assert parser._is_chapter_boundary("CHAPTER 5")
        assert parser._is_chapter_boundary("Ch. 10")
        assert not parser._is_chapter_boundary("Just some text")
    
    def test_title_extraction(self, temp_txt_file):
        """Test title extraction from text"""
        parser = LightNovelParser(temp_txt_file)
        
        text = "Chapter 1: The Beginning\n\nThis is the content..."
        title = parser._extract_title_from_text(text)
        assert "Chapter 1" in title or "Beginning" in title
        
        # Test with empty text
        title_empty = parser._extract_title_from_text("")
        assert title_empty == "Untitled Chapter"


class TestFileFormatEnum:
    """Test FileFormat enum"""
    
    def test_enum_values(self):
        """Test enum has correct values"""
        assert FileFormat.TXT.value == "txt"
        assert FileFormat.EPUB.value == "epub"
        assert FileFormat.PDF.value == "pdf"
    
    def test_enum_membership(self):
        """Test enum membership"""
        assert "txt" in [f.value for f in FileFormat]
        assert "epub" in [f.value for f in FileFormat]
        assert "pdf" in [f.value for f in FileFormat]