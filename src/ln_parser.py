from pathlib import Path
from typing import List, Dict, Optional, Tuple
from enum import Enum
import re
from pydantic import BaseModel, Field
import base64
from io import BytesIO

try:
    import ebooklib
    from ebooklib import epub
    from bs4 import BeautifulSoup
except ImportError:
    ebooklib = None
    epub = None
    BeautifulSoup = None

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None


class FileFormat(str, Enum):
    """Supported file formats for light novels"""
    TXT = "txt"
    EPUB = "epub"
    PDF = "pdf"


class ImageData(BaseModel):
    """Model for storing image data"""
    chapter_num: int
    image_num: int
    data: str  # Base64 encoded image data
    mime_type: str
    
    @property
    def name(self) -> str:
        """Generate image name from chapter and image number"""
        return f"ch{self.chapter_num}_img{self.image_num}"


class Chapter(BaseModel):
    """Model for a book chapter"""
    number: int  # 0 for prologue, -1 for extras
    title: str
    content: str
    images: List[ImageData] = Field(default_factory=list)


class LightNovelParser:
    """Parser for light novel documents in various formats"""
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        self.format = self._detect_format()
        self.content: Optional[str] = None
        self.chapters: List[Chapter] = []
        self.images: List[ImageData] = []
        
    def _detect_format(self) -> FileFormat:
        """Detect file format based on extension"""
        ext = self.file_path.suffix.lower().lstrip('.')
        try:
            return FileFormat(ext)
        except ValueError:
            raise ValueError(f"Unsupported file format: {ext}. Supported formats: txt, epub, pdf")
    
    def parse(self) -> None:
        """Parse the document based on its format"""
        if self.format == FileFormat.TXT:
            self._parse_txt()
        elif self.format == FileFormat.EPUB:
            self._parse_epub()
        elif self.format == FileFormat.PDF:
            self._parse_pdf()
    
    def _parse_txt(self) -> None:
        """Parse plain text file"""
        with open(self.file_path, 'r', encoding='utf-8') as f:
            self.content = f.read()
        
        # Try to detect chapters in text
        self._detect_chapters_in_text(self.content)
    
    def _parse_epub(self) -> None:
        """Parse EPUB file"""
        if epub is None:
            raise ImportError("ebooklib is required for EPUB support. Install with: pip install ebooklib beautifulsoup4")
        
        book = epub.read_epub(self.file_path)
        
        chapter_num = 1
        image_counter = {}  # Track images per chapter
        
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                # Parse HTML content
                soup = BeautifulSoup(item.get_content(), 'html.parser')
                text = soup.get_text(separator='\n', strip=True)
                
                # Extract images from this chapter
                chapter_images = []
                for img in soup.find_all('img'):
                    img_src = img.get('src')
                    if img_src:
                        # Find the image in the book
                        for book_item in book.get_items_of_type(ebooklib.ITEM_IMAGE):
                            if img_src in book_item.get_name():
                                if chapter_num not in image_counter:
                                    image_counter[chapter_num] = 0
                                image_counter[chapter_num] += 1
                                
                                img_data = ImageData(
                                    chapter_num=chapter_num,
                                    image_num=image_counter[chapter_num],
                                    data=base64.b64encode(book_item.get_content()).decode('utf-8'),
                                    mime_type=book_item.media_type
                                )
                                chapter_images.append(img_data)
                                self.images.append(img_data)
                
                # Determine chapter number based on title
                title = soup.find(['h1', 'h2', 'h3'])
                title_text = title.get_text(strip=True) if title else f"Chapter {chapter_num}"
                
                detected_num = self._detect_chapter_number(title_text, chapter_num)
                
                chapter = Chapter(
                    number=detected_num,
                    title=title_text,
                    content=text,
                    images=chapter_images
                )
                self.chapters.append(chapter)
                chapter_num += 1
        
        # Sort chapters by number
        self.chapters.sort(key=lambda x: x.number)
        
        # Combine all content
        self.content = "\n\n".join([f"{ch.title}\n\n{ch.content}" for ch in self.chapters])
    
    def _parse_pdf(self) -> None:
        """Parse PDF file"""
        if fitz is None:
            raise ImportError("PyMuPDF is required for PDF support. Install with: pip install PyMuPDF")
        
        doc = fitz.open(self.file_path)
        full_text = []
        chapter_num = 1
        current_chapter_text = []
        current_chapter_images = []
        image_counter = {}
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            full_text.append(text)
            
            # Extract images from page
            image_list = page.get_images()
            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = doc.extract_image(xref)
                
                if chapter_num not in image_counter:
                    image_counter[chapter_num] = 0
                image_counter[chapter_num] += 1
                
                img_data = ImageData(
                    chapter_num=chapter_num,
                    image_num=image_counter[chapter_num],
                    data=base64.b64encode(base_image["image"]).decode('utf-8'),
                    mime_type=f"image/{base_image['ext']}"
                )
                current_chapter_images.append(img_data)
                self.images.append(img_data)
            
            # Check if we hit a new chapter
            current_chapter_text.append(text)
            if self._is_chapter_boundary(text):
                # Save previous chapter
                if current_chapter_text:
                    chapter_content = "\n".join(current_chapter_text)
                    title = self._extract_title_from_text(chapter_content)
                    detected_num = self._detect_chapter_number(title, chapter_num)
                    
                    chapter = Chapter(
                        number=detected_num,
                        title=title,
                        content=chapter_content,
                        images=current_chapter_images
                    )
                    self.chapters.append(chapter)
                
                # Reset for next chapter
                current_chapter_text = []
                current_chapter_images = []
                chapter_num += 1
        
        # Add last chapter
        if current_chapter_text:
            chapter_content = "\n".join(current_chapter_text)
            title = self._extract_title_from_text(chapter_content)
            detected_num = self._detect_chapter_number(title, chapter_num)
            
            chapter = Chapter(
                number=detected_num,
                title=title,
                content=chapter_content,
                images=current_chapter_images
            )
            self.chapters.append(chapter)
        
        self.content = "\n\n".join(full_text)
        doc.close()
    
    def _detect_chapters_in_text(self, text: str) -> None:
        """Detect chapters in plain text content"""
        # Enhanced patterns to match various chapter formats
        patterns = [
            (r'(?:^|\n)(Prologue|PROLOGUE|Introduction|INTRODUCTION)[\s:.\-]+(.+?)(?=\n|$)', 'prologue'),
            (r'(?:^|\n)(Chapter|CHAPTER|Ch\.|ch\.)\s*(\d+|[IVXLCDM]+)[\s:.\-]*(.+?)(?=\n|$)', 'chapter'),
            (r'(?:^|\n)(Extra|EXTRA|Epilogue|EPILOGUE|Afterword|AFTERWORD|Bonus|BONUS)[\s:.\-]*(.+?)(?=\n|$)', 'extra'),
        ]
        
        all_matches = []
        
        # Find all chapter markers with their types
        for pattern, chapter_type in patterns:
            for match in re.finditer(pattern, text, re.MULTILINE | re.IGNORECASE):
                all_matches.append((match, chapter_type))
        
        # Sort by position in text
        all_matches.sort(key=lambda m: m[0].start())
        
        if not all_matches:
            # No chapters detected, treat as single content
            return
        
        for i, (match, chapter_type) in enumerate(all_matches):
            start = match.start()
            end = all_matches[i + 1][0].start() if i + 1 < len(all_matches) else len(text)
            
            chapter_text = text[start:end].strip()
            
            # Determine chapter number and title based on type
            if chapter_type == 'prologue':
                chapter_num = 0
                title = match.group(0).strip()
            elif chapter_type == 'extra':
                chapter_num = -1
                title = match.group(0).strip()
            else:  # regular chapter
                # Extract the chapter number
                num_str = match.group(2)
                chapter_num = self._parse_chapter_number(num_str)
                title = match.group(0).strip()
            
            chapter = Chapter(
                number=chapter_num,
                title=title,
                content=chapter_text,
                images=[]
            )
            self.chapters.append(chapter)
    
    def _detect_chapter_number(self, title: str, default: int) -> int:
        """Detect chapter number from title"""
        title_lower = title.lower()
        
        # Check for prologue
        if any(word in title_lower for word in ['prologue', 'prolog', 'introduction']):
            return 0
        
        # Check for extras/epilogue
        if any(word in title_lower for word in ['extra', 'epilogue', 'afterword', 'bonus']):
            return -1
        
        # Try to extract number
        match = re.search(r'(?:chapter|ch\.?)\s*(\d+)', title_lower)
        if match:
            return int(match.group(1))
        
        # Try standalone number
        match = re.search(r'\b(\d+)\b', title)
        if match:
            return int(match.group(1))
        
        return default
    
    def _parse_chapter_number(self, num_str: str) -> int:
        """Parse chapter number from string (handles Roman numerals)"""
        try:
            return int(num_str)
        except ValueError:
            # Try Roman numeral
            roman_map = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
            num = 0
            prev_value = 0
            for char in reversed(num_str.upper()):
                value = roman_map.get(char, 0)
                if value < prev_value:
                    num -= value
                else:
                    num += value
                prev_value = value
            return num if num > 0 else 1
    
    def _is_chapter_boundary(self, text: str) -> bool:
        """Check if text contains a chapter boundary marker"""
        patterns = [
            r'(?:^|\n)Chapter\s+\d+',
            r'(?:^|\n)CHAPTER\s+\d+',
            r'(?:^|\n)Ch\.\s*\d+',
        ]
        return any(re.search(pattern, text) for pattern in patterns)
    
    def _extract_title_from_text(self, text: str) -> str:
        """Extract chapter title from text"""
        lines = text.strip().split('\n')
        if lines:
            # First non-empty line is likely the title
            for line in lines:
                if line.strip():
                    return line.strip()[:100]  # Limit title length
        return "Untitled Chapter"
    
    def get_chapter(self, chapter_num: int) -> Optional[Chapter]:
        """Get a specific chapter by number"""
        for chapter in self.chapters:
            if chapter.number == chapter_num:
                return chapter
        return None
    
    def get_chapter_count(self) -> int:
        """Get total number of chapters"""
        return len(self.chapters)
    
    def has_chapters(self) -> bool:
        """Check if document has been parsed into chapters"""
        return len(self.chapters) > 0