"""
OCR and preprocessing pipeline for document extraction.
"""
import io
import logging
from pathlib import Path
from typing import List, Optional, Tuple
import cv2
import numpy as np
import pytesseract
from pdf2image import convert_from_bytes, convert_from_path
from PIL import Image
import camelot
import pdfplumber

from src.models.schemas import OCRResult, TableData, BoundingBox
from src.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class OCREngine:
    """OCR engine using Tesseract."""
    
    def __init__(self, tesseract_path: Optional[str] = None):
        """Initialize OCR engine."""
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        else:
            pytesseract.pytesseract.tesseract_cmd = settings.tesseract_path
    
    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """Preprocess image for better OCR results."""
        # Convert PIL to OpenCV format
        img_array = np.array(image)
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        
        # Noise removal
        denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
        
        # Thresholding
        _, thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Convert back to PIL
        return Image.fromarray(thresh)
    
    def extract_text_with_boxes(self, image: Image.Image, page_num: int = 0) -> List[OCRResult]:
        """Extract text with bounding boxes from image."""
        try:
            # Preprocess
            processed = self.preprocess_image(image)
            
            # Get OCR data
            data = pytesseract.image_to_data(processed, output_type=pytesseract.Output.DICT, lang=settings.ocr_language)
            
            results = []
            for i in range(len(data['text'])):
                if data['text'][i].strip():
                    bbox = BoundingBox(
                        x=data['left'][i],
                        y=data['top'][i],
                        width=data['width'][i],
                        height=data['height'][i],
                        page=page_num
                    )
                    
                    result = OCRResult(
                        text=data['text'][i],
                        confidence=float(data['conf'][i]) / 100.0,
                        bounding_box=bbox,
                        page_number=page_num
                    )
                    results.append(result)
            
            return results
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return []
    
    def extract_full_text(self, image: Image.Image) -> str:
        """Extract full text from image."""
        try:
            processed = self.preprocess_image(image)
            text = pytesseract.image_to_string(processed, lang=settings.ocr_language)
            return text
        except Exception as e:
            logger.error(f"Text extraction failed: {e}")
            return ""


class TableExtractor:
    """Extract tables from PDFs using Camelot and pdfplumber."""
    
    @staticmethod
    def extract_with_camelot(pdf_path: str, pages: str = 'all') -> List[TableData]:
        """Extract tables using Camelot (lattice method for bordered tables)."""
        try:
            tables = camelot.read_pdf(pdf_path, pages=pages, flavor='lattice')
            results = []
            
            for i, table in enumerate(tables):
                df = table.df
                
                # First row as headers
                headers = df.iloc[0].tolist()
                rows = df.iloc[1:].values.tolist()
                
                table_data = TableData(
                    headers=headers,
                    rows=rows,
                    page_number=table.page,
                    confidence=table.accuracy / 100.0
                )
                results.append(table_data)
            
            return results
        except Exception as e:
            logger.error(f"Camelot extraction failed: {e}")
            return []
    
    @staticmethod
    def extract_with_pdfplumber(pdf_path: str) -> List[TableData]:
        """Extract tables using pdfplumber (better for borderless tables)."""
        try:
            results = []
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    tables = page.extract_tables()
                    for table in tables:
                        if table and len(table) > 1:
                            headers = table[0]
                            rows = table[1:]
                            
                            table_data = TableData(
                                headers=headers,
                                rows=rows,
                                page_number=page_num,
                                confidence=0.85  # pdfplumber doesn't provide confidence
                            )
                            results.append(table_data)
            
            return results
        except Exception as e:
            logger.error(f"PDFPlumber extraction failed: {e}")
            return []
    
    def extract_tables(self, pdf_path: str) -> List[TableData]:
        """Extract tables using both methods and merge results."""
        camelot_tables = self.extract_with_camelot(pdf_path)
        plumber_tables = self.extract_with_pdfplumber(pdf_path)
        
        # Use camelot if available, otherwise pdfplumber
        return camelot_tables if camelot_tables else plumber_tables


class DocumentPreprocessor:
    """Main document preprocessing pipeline."""
    
    def __init__(self):
        """Initialize preprocessor with OCR and table extractors."""
        self.ocr_engine = OCREngine()
        self.table_extractor = TableExtractor()
    
    def pdf_to_images(self, pdf_path: str) -> List[Image.Image]:
        """Convert PDF to images."""
        try:
            images = convert_from_path(pdf_path, dpi=300)
            return images
        except Exception as e:
            logger.error(f"PDF to image conversion failed: {e}")
            return []
    
    def pdf_bytes_to_images(self, pdf_bytes: bytes) -> List[Image.Image]:
        """Convert PDF bytes to images."""
        try:
            images = convert_from_bytes(pdf_bytes, dpi=300)
            return images
        except Exception as e:
            logger.error(f"PDF bytes to image conversion failed: {e}")
            return []
    
    def process_document(self, file_path: str) -> Tuple[List[OCRResult], List[TableData], str]:
        """
        Process document and extract OCR results, tables, and full text.
        
        Returns:
            Tuple of (ocr_results, tables, full_text)
        """
        path = Path(file_path)
        
        if path.suffix.lower() == '.pdf':
            return self.process_pdf(file_path)
        elif path.suffix.lower() in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
            return self.process_image(file_path)
        else:
            logger.error(f"Unsupported file type: {path.suffix}")
            return [], [], ""
    
    def process_pdf(self, pdf_path: str) -> Tuple[List[OCRResult], List[TableData], str]:
        """Process PDF document."""
        logger.info(f"Processing PDF: {pdf_path}")
        
        # Extract tables
        tables = self.table_extractor.extract_tables(pdf_path)
        
        # Convert to images and run OCR
        images = self.pdf_to_images(pdf_path)
        ocr_results = []
        full_text_parts = []
        
        for i, image in enumerate(images):
            page_results = self.ocr_engine.extract_text_with_boxes(image, page_num=i)
            ocr_results.extend(page_results)
            
            page_text = self.ocr_engine.extract_full_text(image)
            full_text_parts.append(f"--- Page {i+1} ---\n{page_text}")
        
        full_text = "\n\n".join(full_text_parts)
        
        logger.info(f"Extracted {len(ocr_results)} text blocks and {len(tables)} tables")
        return ocr_results, tables, full_text
    
    def process_image(self, image_path: str) -> Tuple[List[OCRResult], List[TableData], str]:
        """Process image document."""
        logger.info(f"Processing image: {image_path}")
        
        image = Image.open(image_path)
        ocr_results = self.ocr_engine.extract_text_with_boxes(image, page_num=0)
        full_text = self.ocr_engine.extract_full_text(image)
        
        logger.info(f"Extracted {len(ocr_results)} text blocks")
        return ocr_results, [], full_text
