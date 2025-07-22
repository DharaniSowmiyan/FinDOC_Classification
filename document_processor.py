import streamlit as st
import PyPDF2
import io
from PIL import Image
import pytesseract
from docx import Document

class DocumentProcessor:
    """
    Handles text extraction from various document formats
    """
    
    def __init__(self):
        pass
    
    def extract_text(self, uploaded_file):
        """
        Extract text from uploaded file. For images, return the image object.
        """
        try:
            file_type = uploaded_file.type
            
            if file_type == 'application/pdf':
                return self._extract_from_pdf(uploaded_file)
            elif file_type.startswith('image/'):
                # For images, we will now return the image object directly
                return Image.open(uploaded_file)
            elif file_type == 'text/plain':
                return self._extract_from_text(uploaded_file)
            elif file_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
                return self._extract_from_docx(uploaded_file)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
                
        except Exception as e:
            st.error(f"Error processing document: {str(e)}")
            return None
    
    def _extract_from_pdf(self, uploaded_file):
        """Extract text from PDF file"""
        try:
            # Create a PDF reader object
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
            
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            
            return text.strip()
        except Exception as e:
            raise Exception(f"Failed to extract text from PDF: {str(e)}")
    
    def _extract_from_image(self, uploaded_file):
        """This function is now obsolete and will be removed."""
        pass
    
    def _extract_from_text(self, uploaded_file):
        """Extract text from plain text file"""
        try:
            # Read text file
            text = uploaded_file.read().decode('utf-8')
            return text.strip()
        except UnicodeDecodeError:
            try:
                # Try with different encoding
                uploaded_file.seek(0)
                text = uploaded_file.read().decode('latin-1')
                return text.strip()
            except Exception as e:
                raise Exception(f"Failed to decode text file: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to read text file: {str(e)}")
    
    def _extract_from_docx(self, uploaded_file):
        """Extract text from Word document"""
        try:
            # Read DOCX file
            doc = Document(io.BytesIO(uploaded_file.read()))
            
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            
            return text.strip()
        except Exception as e:
            raise Exception(f"Failed to extract text from Word document: {str(e)}")
