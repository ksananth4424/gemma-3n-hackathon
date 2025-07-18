"""
PDF Content Processor using PyMuPDF with OCR fallback
"""

import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import logging
from pathlib import Path
from typing import Optional

from ..utils.config_manager import ConfigManager

logger = logging.getLogger('accessibility_assistant.pdf_processor')


class PDFProcessor:
    """
    PDF content extraction with OCR fallback for scanned documents
    """
    
    def __init__(self, config_manager: ConfigManager):
        self.config = config_manager
        self._setup_ocr()
        
    def _setup_ocr(self):
        """Configure OCR settings"""
        # Set up Tesseract path if specified in config
        tesseract_path = self.config.get('ai', 'tesseract_path')
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
    
    def extract_content(self, file_path: str) -> str:
        """
        Extract text content from PDF file
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Extracted text content
        """
        try:
            doc = fitz.open(file_path)
            full_text = ""
            total_pages = len(doc)
            
            logger.info(f"Processing PDF with {total_pages} pages")
            
            for page_num in range(total_pages):
                page = doc[page_num]
                
                # Extract text directly
                text = page.get_text()
                
                # If no text found, try OCR
                if not text.strip():
                    logger.debug(f"No text found on page {page_num + 1}, attempting OCR")
                    text = self._ocr_page(page)
                
                if text.strip():
                    full_text += f"\n--- Page {page_num + 1} ---\n"
                    full_text += text
                
                # Progress logging for large documents
                if page_num % 10 == 0 and page_num > 0:
                    logger.debug(f"Processed {page_num}/{total_pages} pages")
            
            doc.close()
            
            # Clean and normalize text
            cleaned_text = self._clean_text(full_text)
            logger.info(f"Extracted {len(cleaned_text)} characters from PDF")
            
            return cleaned_text
            
        except Exception as e:
            logger.error(f"Error extracting PDF content from {file_path}: {e}")
            raise
    
    def _ocr_page(self, page) -> str:
        """
        Perform OCR on a PDF page
        
        Args:
            page: PyMuPDF page object
            
        Returns:
            OCR-extracted text
        """
        try:
            # Convert page to high-resolution image for better OCR
            mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better quality
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            
            # Perform OCR using Tesseract
            image = Image.open(io.BytesIO(img_data))
            
            # OCR configuration for better accuracy
            custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz .,!?;:-'
            
            text = pytesseract.image_to_string(image, config=custom_config)
            
            return text
            
        except Exception as e:
            logger.warning(f"OCR failed: {e}")
            return ""
    
    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize extracted text
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove excessive whitespace while preserving paragraph breaks
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            cleaned_line = ' '.join(line.split())  # Remove extra spaces
            if cleaned_line:
                cleaned_lines.append(cleaned_line)
        
        # Join with single newlines
        cleaned_text = '\n'.join(cleaned_lines)
        
        # Remove common OCR artifacts
        cleaned_text = self._fix_ocr_errors(cleaned_text)
        
        return cleaned_text
    
    def _fix_ocr_errors(self, text: str) -> str:
        """
        Fix common OCR errors
        
        Args:
            text: Text with potential OCR errors
            
        Returns:
            Text with corrections applied
        """
        # Common OCR corrections
        corrections = {
            'l': 'I',  # lowercase l often mistaken for I
            'rn': 'm',  # rn often mistaken for m
            '0': 'O',   # zero often mistaken for O in words
            '5': 'S',   # 5 often mistaken for S in words
        }
        
        # Apply corrections carefully to avoid false positives
        words = text.split()
        corrected_words = []
        
        for word in words:
            # Only apply corrections to words that look suspicious
            if len(word) > 1:
                corrected_word = word
                for wrong, right in corrections.items():
                    # Simple heuristic corrections
                    if word.startswith('l') and len(word) > 2:
                        corrected_word = 'I' + corrected_word[1:]
                corrected_words.append(corrected_word)
            else:
                corrected_words.append(word)
        
        return ' '.join(corrected_words)
    
    def get_document_info(self, file_path: str) -> dict:
        """
        Get metadata about the PDF document
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Dictionary with document metadata
        """
        try:
            doc = fitz.open(file_path)
            
            metadata = {
                'page_count': len(doc),
                'title': doc.metadata.get('title', ''),
                'author': doc.metadata.get('author', ''),
                'subject': doc.metadata.get('subject', ''),
                'creator': doc.metadata.get('creator', ''),
                'encrypted': doc.needs_pass,
                'file_size': Path(file_path).stat().st_size
            }
            
            doc.close()
            return metadata
            
        except Exception as e:
            logger.error(f"Error getting PDF metadata: {e}")
            return {}
    
    def is_scanned_pdf(self, file_path: str) -> bool:
        """
        Detect if PDF is likely scanned (image-based)
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            True if likely scanned, False otherwise
        """
        try:
            doc = fitz.open(file_path)
            
            # Check first few pages for text content
            pages_to_check = min(3, len(doc))
            text_found = False
            
            for page_num in range(pages_to_check):
                page = doc[page_num]
                text = page.get_text().strip()
                
                if len(text) > 50:  # Threshold for meaningful text
                    text_found = True
                    break
            
            doc.close()
            return not text_found
            
        except Exception as e:
            logger.error(f"Error checking if PDF is scanned: {e}")
            return False
