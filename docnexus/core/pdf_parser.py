import fitz  # PyMuPDF
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class PDFParser:
    """
    Parses PDF files into structured content (Markdown/Text) using PyMuPDF.
    This enables 'Search' and 'Export to Other Formats' for PDFs.
    """

    @staticmethod
    def parse_pdf_to_markdown(file_path):
        """
        Extracts text from a PDF and returns it as a Markdown string.
        
        Args:
            file_path (str or Path): Path to the PDF file.
            
        Returns:
            str:Extracted text content formatted as basic Markdown.
        """
        try:
            doc = fitz.open(file_path)
            md_content = []
            
            # Metadata
            md_content.append(f"# {doc.metadata.get('title', Path(file_path).stem)}\n")
            
            for page_num, page in enumerate(doc):
                text = page.get_text("text")
                md_content.append(f"\n## Page {page_num + 1}\n")
                md_content.append(text)
                
            return "\n".join(md_content)
            
        except Exception as e:
            logger.error(f"Failed to parse PDF {file_path}: {e}")
            return f"> **Error**: Could not parse PDF content: {e}"

    @staticmethod
    def extract_text(file_path):
        """
        Fast text extraction for Search indexing.
        """
        try:
            doc = fitz.open(file_path)
            full_text = ""
            for page in doc:
                full_text += page.get_text() + "\n"
            return full_text
        except Exception as e:
            logger.error(f"PDF Text Extraction Failed: {e}")
            return ""
