"""
Script to generate sample EPUB and PDF files for testing the LightNovelParser
"""
from pathlib import Path
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
# import base64

try:
    from ebooklib import epub
except ImportError:
    epub = None

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader
except ImportError:
    raise ImportError("reportlab not installed. Install with: pip install reportlab")


def create_sample_image(text: str, size=(200, 200), color='lightblue') -> BytesIO:
    """Create a simple sample image with text"""
    img = Image.new('RGB', size, color=color)
    draw = ImageDraw.Draw(img)
    
    # Add text to image
    try:
        # Try to use a default font
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
    except Exception:
        # Fallback to default font
        font = ImageFont.load_default()
    
    # Calculate text position (centered)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    position = ((size[0] - text_width) // 2, (size[1] - text_height) // 2)
    
    draw.text(position, text, fill='black', font=font)
    
    # Save to BytesIO
    img_io = BytesIO()
    img.save(img_io, format='PNG')
    img_io.seek(0)
    return img_io


def generate_epub(output_path: str = 'test_files/sample_novel.epub'):
    """Generate a sample EPUB file with chapters and images"""
    if epub is None:
        print("Error: ebooklib not installed. Install with: pip install ebooklib")
        return
    
    # Create EPUB book
    book = epub.EpubBook()
    
    # Set metadata
    book.set_identifier('sample_light_novel_001')
    book.set_title('Sample Light Novel')
    book.set_language('en')
    book.add_author('Test Author')
    
    # Create chapters
    chapters = []
    
    # Prologue
    prologue_content = '''
    <h1>Prologue: The Beginning</h1>
    <p>This is the prologue of our sample light novel.</p>
    <p>It sets the stage for the adventure to come.</p>
    <img src="images/prologue_img1.png" alt="Prologue Image"/>
    <p>The world was at peace, but that was about to change...</p>
    '''
    
    prologue = epub.EpubHtml(title='Prologue',
                            file_name='prologue.xhtml',
                            lang='en')
    prologue.content = prologue_content
    book.add_item(prologue)
    chapters.append(prologue)
    
    # Add prologue image
    img1 = create_sample_image("Prologue\nImage 1", color='lightcoral')
    book.add_item(epub.EpubItem(
        uid="prologue_img1",
        file_name="images/prologue_img1.png",
        media_type="image/png",
        content=img1.read()
    ))
    
    # Chapter 1
    ch1_content = '''
    <h1>Chapter 1: The Hero's Journey</h1>
    <p>Our hero begins their adventure in a small village.</p>
    <img src="images/ch1_img1.png" alt="Chapter 1 Image 1"/>
    <p>The village elder called upon them for an important quest.</p>
    <img src="images/ch1_img2.png" alt="Chapter 1 Image 2"/>
    <p>With determination in their heart, they set off.</p>
    '''
    
    ch1 = epub.EpubHtml(title='Chapter 1',
                       file_name='chapter1.xhtml',
                       lang='en')
    ch1.content = ch1_content
    book.add_item(ch1)
    chapters.append(ch1)
    
    # Add Chapter 1 images
    img2 = create_sample_image("Chapter 1\nImage 1", color='lightgreen')
    book.add_item(epub.EpubItem(
        uid="ch1_img1",
        file_name="images/ch1_img1.png",
        media_type="image/png",
        content=img2.read()
    ))
    
    img3 = create_sample_image("Chapter 1\nImage 2", color='lightyellow')
    book.add_item(epub.EpubItem(
        uid="ch1_img2",
        file_name="images/ch1_img2.png",
        media_type="image/png",
        content=img3.read()
    ))
    
    # Chapter 2
    ch2_content = '''
    <h1>Chapter 2: The First Challenge</h1>
    <p>The hero encounters their first obstacle.</p>
    <p>A fierce monster blocks the path forward.</p>
    <img src="images/ch2_img1.png" alt="Chapter 2 Image"/>
    <p>With courage and skill, they face the challenge head-on.</p>
    '''
    
    ch2 = epub.EpubHtml(title='Chapter 2',
                       file_name='chapter2.xhtml',
                       lang='en')
    ch2.content = ch2_content
    book.add_item(ch2)
    chapters.append(ch2)
    
    # Add Chapter 2 image
    img4 = create_sample_image("Chapter 2\nImage 1", color='lightpink')
    book.add_item(epub.EpubItem(
        uid="ch2_img1",
        file_name="images/ch2_img1.png",
        media_type="image/png",
        content=img4.read()
    ))
    
    # Extra content
    extra_content = '''
    <h1>Extra: Bonus Story</h1>
    <p>This is a bonus chapter that takes place after the main story.</p>
    <p>Our hero reflects on their journey and the friends they made.</p>
    <p>The adventure continues...</p>
    '''
    
    extra = epub.EpubHtml(title='Extra',
                         file_name='extra.xhtml',
                         lang='en')
    extra.content = extra_content
    book.add_item(extra)
    chapters.append(extra)
    
    # Define Table of Contents
    book.toc = chapters
    
    # Add navigation files
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    
    # Define spine
    book.spine = ['nav'] + chapters
    
    # Create output directory
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Write EPUB file
    epub.write_epub(output_path, book)
    print(f"✓ Created EPUB file: {output_path}")


def generate_pdf(output_path: str = 'test_files/sample_novel.pdf'):
    """Generate a sample PDF file with chapters and images"""
    if canvas is None:
        print("Error: reportlab not installed. Install with: pip install reportlab")
        return
    
    # Create output directory
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Create PDF
    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter
    
    # Prologue
    c.setFont("Helvetica-Bold", 24)
    c.drawString(50, height - 100, "Prologue: The Beginning")
    
    c.setFont("Helvetica", 12)
    y_position = height - 150
    prologue_text = [
        "This is the prologue of our sample light novel.",
        "It sets the stage for the adventure to come.",
        "",
        "The world was at peace, but that was about to change..."
    ]
    
    for line in prologue_text:
        c.drawString(50, y_position, line)
        y_position -= 20
    
    # Add prologue image
    img1 = create_sample_image("Prologue\nImage 1", color='lightcoral')
    c.drawImage(ImageReader(img1), 50, y_position - 220, width=200, height=200)
    
    # New page for Chapter 1
    c.showPage()
    
    c.setFont("Helvetica-Bold", 24)
    c.drawString(50, height - 100, "Chapter 1: The Hero's Journey")
    
    c.setFont("Helvetica", 12)
    y_position = height - 150
    ch1_text = [
        "Our hero begins their adventure in a small village.",
        "The village elder called upon them for an important quest.",
    ]
    
    for line in ch1_text:
        c.drawString(50, y_position, line)
        y_position -= 20
    
    # Add Chapter 1 images
    img2 = create_sample_image("Chapter 1\nImage 1", color='lightgreen')
    c.drawImage(ImageReader(img2), 50, y_position - 220, width=200, height=200)
    
    y_position -= 240
    c.drawString(50, y_position, "With determination in their heart, they set off.")
    y_position -= 40
    
    img3 = create_sample_image("Chapter 1\nImage 2", color='lightyellow')
    c.drawImage(ImageReader(img3), 50, y_position - 220, width=200, height=200)
    
    # New page for Chapter 2
    c.showPage()
    
    c.setFont("Helvetica-Bold", 24)
    c.drawString(50, height - 100, "Chapter 2: The First Challenge")
    
    c.setFont("Helvetica", 12)
    y_position = height - 150
    ch2_text = [
        "The hero encounters their first obstacle.",
        "A fierce monster blocks the path forward.",
    ]
    
    for line in ch2_text:
        c.drawString(50, y_position, line)
        y_position -= 20
    
    img4 = create_sample_image("Chapter 2\nImage 1", color='lightpink')
    c.drawImage(ImageReader(img4), 50, y_position - 220, width=200, height=200)
    
    y_position -= 240
    c.drawString(50, y_position, "With courage and skill, they face the challenge head-on.")
    
    # New page for Extra
    c.showPage()
    
    c.setFont("Helvetica-Bold", 24)
    c.drawString(50, height - 100, "Extra: Bonus Story")
    
    c.setFont("Helvetica", 12)
    y_position = height - 150
    extra_text = [
        "This is a bonus chapter that takes place after the main story.",
        "Our hero reflects on their journey and the friends they made.",
        "The adventure continues..."
    ]
    
    for line in extra_text:
        c.drawString(50, y_position, line)
        y_position -= 20
    
    # Save PDF
    c.save()
    print(f"✓ Created PDF file: {output_path}")


def main():
    """Generate both sample files"""
    print("Generating sample test files...")
    print()
    
    try:
        generate_epub()
    except Exception as e:
        print(f"✗ Error generating EPUB: {e}")
    
    try:
        generate_pdf()
    except Exception as e:
        print(f"✗ Error generating PDF: {e}")
    
    print()
    print("Done! Files created in 'test_files/' directory")


if __name__ == '__main__':
    main()