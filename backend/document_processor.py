"""
Document Processing Module
Handles PDF and TXT file processing for the Smart Research Assistant
"""

import os
import PyPDF2
from typing import Optional, Tuple
import streamlit as st

class DocumentProcessor:
    """Handles document upload and text extraction"""
    
    def __init__(self):
        self.supported_formats = ['.pdf', '.txt']
        self.max_file_size = 10 * 1024 * 1024  # 10MB limit
    
    def validate_file(self, uploaded_file) -> Tuple[bool, str]:
        """
        Validate uploaded file format and size
        
        Args:
            uploaded_file: Streamlit uploaded file object
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if uploaded_file is None:
            return False, "No file uploaded"
        
        # Check file extension
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()
        if file_extension not in self.supported_formats:
            return False, f"Unsupported file format. Please upload {', '.join(self.supported_formats)} files only."
        
        # Check file size
        if uploaded_file.size > self.max_file_size:
            return False, f"File size too large. Maximum size allowed is {self.max_file_size // (1024*1024)}MB."
        
        return True, ""
    
    def extract_text_from_pdf(self, uploaded_file) -> str:
        """
        Extract text content from PDF file
        
        Args:
            uploaded_file: Streamlit uploaded file object
            
        Returns:
            Extracted text content
        """
        try:
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            text_content = ""
            
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text.strip():
                        text_content += f"\n--- Page {page_num + 1} ---\n"
                        text_content += page_text
                except Exception as e:
                    st.warning(f"Could not extract text from page {page_num + 1}: {str(e)}")
                    continue
            
            if not text_content.strip():
                raise ValueError("No text could be extracted from the PDF")
            
            return text_content
        
        except Exception as e:
            raise ValueError(f"Error processing PDF: {str(e)}")
    
    def extract_text_from_txt(self, uploaded_file) -> str:
        """
        Extract text content from TXT file
        
        Args:
            uploaded_file: Streamlit uploaded file object
            
        Returns:
            Text content
        """
        try:
            # Try different encodings
            encodings = ['utf-8', 'utf-16', 'latin-1', 'ascii']
            
            for encoding in encodings:
                try:
                    uploaded_file.seek(0)  # Reset file pointer
                    content = uploaded_file.read().decode(encoding)
                    if content.strip():
                        return content
                except UnicodeDecodeError:
                    continue
            
            raise ValueError("Could not decode the text file with any supported encoding")
        
        except Exception as e:
            raise ValueError(f"Error processing TXT file: {str(e)}")
    
    def process_document(self, uploaded_file) -> Tuple[bool, str, str]:
        """
        Main method to process uploaded document
        
        Args:
            uploaded_file: Streamlit uploaded file object
            
        Returns:
            Tuple of (success, text_content, error_message)
        """
        try:
            # Validate file
            is_valid, error_msg = self.validate_file(uploaded_file)
            if not is_valid:
                return False, "", error_msg
            
            # Extract text based on file type
            file_extension = os.path.splitext(uploaded_file.name)[1].lower()
            
            if file_extension == '.pdf':
                text_content = self.extract_text_from_pdf(uploaded_file)
            elif file_extension == '.txt':
                text_content = self.extract_text_from_txt(uploaded_file)
            else:
                return False, "", "Unsupported file format"
            
            # Basic text validation
            if not text_content or len(text_content.strip()) < 50:
                return False, "", "Document appears to be empty or too short to process"
            
            return True, text_content, ""
        
        except Exception as e:
            return False, "", str(e)
    
    def save_uploaded_file(self, uploaded_file, upload_dir: str = "uploads") -> str:
        """
        Save uploaded file to disk
        
        Args:
            uploaded_file: Streamlit uploaded file object
            upload_dir: Directory to save the file
            
        Returns:
            Path to saved file
        """
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, uploaded_file.name)
        
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getvalue())
        
        return file_path