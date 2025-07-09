import os
import io
import google.generativeai as genai
from typing import List, Dict, Any
import PyPDF2
from docx import Document
import pandas as pd
import openpyxl
from dotenv import load_dotenv
import json
import logging
from datetime import datetime
import uuid

# Import database models and functions
from app.model.db import (
    get_db, create_document_record, get_recent_documents, 
    get_document_by_id, update_document_quiz_status,
    delete_document, search_documents, UploadedDocument
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def configure_gemini():
    """Configure Gemini AI with proper error handling"""
    api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
    
    if not api_key:
        raise ValueError("API key not found. Please set GEMINI_API_KEY or GOOGLE_API_KEY in your .env file")
    
    try:
        genai.configure(
            api_key=api_key,
            transport='rest',
            client_options={"api_endpoint": "generativelanguage.googleapis.com"}
        )
        logger.info("Gemini AI configured successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to configure Gemini AI: {e}")
        raise

def list_available_models():
    """List all available models"""
    try:
        configure_gemini()
        models = []
        for m in genai.list_models():
            # Simplify model names (remove full path)
            model_name = m.name.split('/')[-1]
            models.append(model_name)
        return models
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        raise

# Initialize Gemini configuration
configure_gemini()

class FileProcessor:
    """Handles different file types and extracts text content"""
    
    @staticmethod
    def extract_text_from_file(file_content: bytes, filename: str) -> str:
        """Extract text content from various file types"""
        file_extension = filename.lower().split('.')[-1]
        
        try:
            if file_extension == 'txt':
                return file_content.decode('utf-8')
            
            elif file_extension == 'pdf':
                return FileProcessor._extract_from_pdf(file_content)
            
            elif file_extension == 'docx':
                return FileProcessor._extract_from_docx(file_content)
            
            elif file_extension in ['xlsx', 'xls']:
                return FileProcessor._extract_from_excel(file_content)
            
            elif file_extension == 'csv':
                return FileProcessor._extract_from_csv(file_content)
            
            else:
                try:
                    return file_content.decode('utf-8')
                except UnicodeDecodeError:
                    return f"Unsupported file type: {file_extension}"
        
        except Exception as e:
            logger.error(f"Error processing file {filename}: {e}")
            return f"Error processing file: {str(e)}"
    
    @staticmethod
    def _extract_from_pdf(file_content: bytes) -> str:
        """Extract text from PDF file"""
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            logger.error(f"Error extracting from PDF: {e}")
            raise
    
    @staticmethod
    def _extract_from_docx(file_content: bytes) -> str:
        """Extract text from DOCX file"""
        try:
            doc = Document(io.BytesIO(file_content))
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            logger.error(f"Error extracting from DOCX: {e}")
            raise
    
    @staticmethod
    def _extract_from_excel(file_content: bytes) -> str:
        """Extract text from Excel file"""
        try:
            df = pd.read_excel(io.BytesIO(file_content))
            return df.to_string()
        except Exception as e:
            logger.error(f"Error extracting from Excel: {e}")
            raise
    
    @staticmethod
    def _extract_from_csv(file_content: bytes) -> str:
        """Extract text from CSV file"""
        try:
            df = pd.read_csv(io.BytesIO(file_content))
            return df.to_string()
        except Exception as e:
            logger.error(f"Error extracting from CSV: {e}")
            raise

class QuizGenerator:
    """Generates quiz questions using Gemini AI"""
    
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    def generate_quiz(self, content: str, num_questions: int = 5) -> List[Dict[str, Any]]:
        """Generate quiz questions from content using Gemini AI"""
        
        content_preview = content[:4000] if len(content) > 4000 else content
        
        prompt = f"""
        Generate exactly {num_questions} multiple choice quiz questions based on this content.
        For each question provide:
        1. A clear question
        2. Four options (A-D)
        3. The correct answer
        4. A brief explanation
        
        Return ONLY a valid JSON array with this structure:
        [
            {{
                "question": "Question text?",
                "options": {{
                    "A": "Option A",
                    "B": "Option B",
                    "C": "Option C",
                    "D": "Option D"
                }},
                "correct_answer": "A",
                "explanation": "Explanation text"
            }}
        ]
        
        Content:
        {content_preview}
        """
        
        try:
            response = self.model.generate_content(prompt)
            
            if not response.text:
                raise ValueError("Empty response from Gemini")
            
            # Clean and parse the response
            response_text = response.text.strip()
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0]
            elif '```' in response_text:
                response_text = response_text.split('```')[1]
                
            quiz_data = json.loads(response_text)
            
            # Validate the structure
            if not isinstance(quiz_data, list):
                raise ValueError("Invalid response format - expected array")
            
            return quiz_data[:num_questions]
            
        except Exception as e:
            logger.error(f"Quiz generation error: {e}")
            return self._create_fallback_quiz(content, num_questions)
    
    def _create_fallback_quiz(self, content: str, num_questions: int) -> List[Dict[str, Any]]:
        """Create fallback quiz questions"""
        questions = []
        for i in range(num_questions):
            questions.append({
                "question": f"Sample question {i+1} about the uploaded content?",
                "options": {
                    "A": "Correct answer",
                    "B": "Incorrect option 1",
                    "C": "Incorrect option 2",
                    "D": "Incorrect option 3"
                },
                "correct_answer": "A",
                "explanation": "This is a sample question because the quiz generator encountered an error"
            })
        return questions

def process_file_and_generate_quiz(file_content: bytes, filename: str, num_questions: int = 5) -> Dict[str, Any]:
    """Main function to process file and generate quiz"""
    try:
        content = FileProcessor.extract_text_from_file(file_content, filename)
        
        if not content or content.startswith("Error"):
            raise ValueError(f"Failed to extract content: {content[:200]}")
        
        quiz_generator = QuizGenerator()
        quiz_questions = quiz_generator.generate_quiz(content, num_questions)
        
        return {
            "filename": filename,
            "content_preview": content[:500] + "..." if len(content) > 500 else content,
            "total_questions": len(quiz_questions),
            "questions": quiz_questions
        }
        
    except Exception as e:
        logger.error(f"Processing error: {e}")
        return {
            "filename": filename,
            "content_preview": "Error processing file",
            "total_questions": 1,
            "questions": [{
                "question": "Error generating quiz",
                "options": {
                    "A": "Check file format",
                    "B": "Check API key",
                    "C": "Try again later",
                    "D": "Contact support"
                },
                "correct_answer": "A",
                "explanation": str(e)[:200]
            }]
        }

# New database-integrated functions
def save_uploaded_file(file_content: bytes, original_filename: str, num_questions: int = 5) -> Dict[str, Any]:
    """Save uploaded file to database and generate quiz"""
    db = next(get_db())
    try:
        # Generate unique filename
        file_extension = original_filename.lower().split('.')[-1]
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        
        # Extract content
        content_text = FileProcessor.extract_text_from_file(file_content, original_filename)
        content_preview = content_text[:500] + "..." if len(content_text) > 500 else content_text
        
        # Save to database
        document = create_document_record(
            db=db,
            filename=unique_filename,
            original_filename=original_filename,
            file_content=file_content,
            file_extension=file_extension,
            content_text=content_text,
            content_preview=content_preview
        )
        
        # Generate quiz
        quiz_generator = QuizGenerator()
        quiz_questions = quiz_generator.generate_quiz(content_text, num_questions)
        
        # Update document with quiz status
        update_document_quiz_status(
            db=db,
            document_id=document.id,
            quiz_generated=True,
            quiz_questions_count=len(quiz_questions)
        )
        
        return {
            "document_id": document.id,
            "filename": original_filename,
            "content_preview": content_preview,
            "total_questions": len(quiz_questions),
            "questions": quiz_questions,
            "upload_date": document.upload_date.isoformat(),
            "file_size": document.file_size
        }
        
    except Exception as e:
        logger.error(f"Error saving uploaded file: {e}")
        # Update document with error status
        if 'document' in locals():
            update_document_quiz_status(
                db=db,
                document_id=document.id,
                quiz_generated=False,
                error_message=str(e)
            )
        raise
    finally:
        db.close()

def get_recent_uploads(limit: int = 10) -> List[Dict[str, Any]]:
    """Get recent uploaded documents for frontend display"""
    db = next(get_db())
    try:
        documents = get_recent_documents(db, limit)
        return [
            {
                "id": doc.id,
                "filename": doc.original_filename,
                "file_extension": doc.file_extension,
                "file_size": doc.file_size,
                "upload_date": doc.upload_date.isoformat(),
                "processed": doc.processed,
                "quiz_generated": doc.quiz_generated,
                "quiz_questions_count": doc.quiz_questions_count,
                "content_preview": doc.content_preview,
                "error_message": doc.error_message
            }
            for doc in documents
        ]
    except Exception as e:
        logger.error(f"Error fetching recent uploads: {e}")
        raise
    finally:
        db.close()

def get_document_quiz(document_id: int) -> Dict[str, Any]:
    """Get quiz for a specific document"""
    db = next(get_db())
    try:
        document = get_document_by_id(db, document_id)
        if not document:
            raise ValueError(f"Document {document_id} not found")
        
        if not document.quiz_generated:
            raise ValueError("Quiz not generated for this document")
        
        # Re-generate quiz from stored content
        quiz_generator = QuizGenerator()
        quiz_questions = quiz_generator.generate_quiz(document.content_text, document.quiz_questions_count)
        
        return {
            "document_id": document.id,
            "filename": document.original_filename,
            "content_preview": document.content_preview,
            "total_questions": len(quiz_questions),
            "questions": quiz_questions,
            "upload_date": document.upload_date.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting document quiz: {e}")
        raise
    finally:
        db.close()

def search_recent_uploads(search_term: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Search recent uploads by filename or content"""
    db = next(get_db())
    try:
        documents = search_documents(db, search_term, limit)
        return [
            {
                "id": doc.id,
                "filename": doc.original_filename,
                "file_extension": doc.file_extension,
                "file_size": doc.file_size,
                "upload_date": doc.upload_date.isoformat(),
                "processed": doc.processed,
                "quiz_generated": doc.quiz_generated,
                "quiz_questions_count": doc.quiz_questions_count,
                "content_preview": doc.content_preview
            }
            for doc in documents
        ]
    except Exception as e:
        logger.error(f"Error searching uploads: {e}")
        raise
    finally:
        db.close()

def delete_uploaded_file(document_id: int) -> bool:
    """Delete an uploaded file from database"""
    db = next(get_db())
    try:
        return delete_document(db, document_id)
    except Exception as e:
        logger.error(f"Error deleting uploaded file: {e}")
        raise
    finally:
        db.close()