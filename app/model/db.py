import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, LargeBinary, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
import logging
from typing import List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'mysql://root:password@localhost:3306/quiz_generator')

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=False  # Set to True for SQL query logging
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

class UploadedDocument(Base):
    """Model for storing uploaded documents"""
    __tablename__ = "uploaded_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False, index=True)
    original_filename = Column(String(255), nullable=False)
    file_extension = Column(String(10), nullable=False)
    file_size = Column(Integer, nullable=False)  # Size in bytes
    file_content = Column(LargeBinary, nullable=False)  # Store actual file content
    content_text = Column(Text, nullable=True)  # Extracted text content
    content_preview = Column(Text, nullable=True)  # First 500 characters
    upload_date = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    processed = Column(Boolean, default=False, nullable=False)
    quiz_generated = Column(Boolean, default=False, nullable=False)
    quiz_questions_count = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<UploadedDocument(id={self.id}, filename='{self.filename}', upload_date='{self.upload_date}')>"

class QuizSession(Base):
    """Model for storing quiz sessions"""
    __tablename__ = "quiz_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, nullable=False, index=True)
    session_token = Column(String(255), nullable=False, unique=True, index=True)
    created_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed = Column(Boolean, default=False, nullable=False)
    score = Column(Integer, nullable=True)
    total_questions = Column(Integer, nullable=False)
    correct_answers = Column(Integer, default=0, nullable=False)
    
    def __repr__(self):
        return f"<QuizSession(id={self.id}, document_id={self.document_id}, score={self.score})>"

# Database utility functions
def get_db() -> Session:
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except SQLAlchemyError as e:
        logger.error(f"Error creating database tables: {e}")
        raise

def create_document_record(
    db: Session,
    filename: str,
    original_filename: str,
    file_content: bytes,
    file_extension: str,
    content_text: Optional[str] = None,
    content_preview: Optional[str] = None
) -> UploadedDocument:
    """Create a new document record in the database"""
    try:
        document = UploadedDocument(
            filename=filename,
            original_filename=original_filename,
            file_extension=file_extension,
            file_size=len(file_content),
            file_content=file_content,
            content_text=content_text,
            content_preview=content_preview,
            processed=content_text is not None,
            quiz_generated=False
        )
        
        db.add(document)
        db.commit()
        db.refresh(document)
        
        logger.info(f"Document record created: {document.id}")
        return document
        
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error creating document record: {e}")
        raise

def get_recent_documents(db: Session, limit: int = 10) -> List[UploadedDocument]:
    """Get recent uploaded documents"""
    try:
        documents = db.query(UploadedDocument)\
            .order_by(UploadedDocument.upload_date.desc())\
            .limit(limit)\
            .all()
        return documents
    except SQLAlchemyError as e:
        logger.error(f"Error fetching recent documents: {e}")
        raise

def get_document_by_id(db: Session, document_id: int) -> Optional[UploadedDocument]:
    """Get document by ID"""
    try:
        return db.query(UploadedDocument).filter(UploadedDocument.id == document_id).first()
    except SQLAlchemyError as e:
        logger.error(f"Error fetching document {document_id}: {e}")
        raise

def update_document_quiz_status(
    db: Session,
    document_id: int,
    quiz_generated: bool = True,
    quiz_questions_count: int = 0,
    error_message: Optional[str] = None
) -> bool:
    """Update document quiz generation status"""
    try:
        document = db.query(UploadedDocument).filter(UploadedDocument.id == document_id).first()
        if document:
            document.quiz_generated = quiz_generated
            document.quiz_questions_count = quiz_questions_count
            if error_message:
                document.error_message = error_message
            db.commit()
            logger.info(f"Document {document_id} quiz status updated")
            return True
        return False
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error updating document quiz status: {e}")
        raise

def delete_document(db: Session, document_id: int) -> bool:
    """Delete a document from the database"""
    try:
        document = db.query(UploadedDocument).filter(UploadedDocument.id == document_id).first()
        if document:
            db.delete(document)
            db.commit()
            logger.info(f"Document {document_id} deleted successfully")
            return True
        return False
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error deleting document {document_id}: {e}")
        raise

def search_documents(db: Session, search_term: str, limit: int = 10) -> List[UploadedDocument]:
    """Search documents by filename or content"""
    try:
        documents = db.query(UploadedDocument)\
            .filter(
                (UploadedDocument.original_filename.contains(search_term)) |
                (UploadedDocument.content_preview.contains(search_term))
            )\
            .order_by(UploadedDocument.upload_date.desc())\
            .limit(limit)\
            .all()
        return documents
    except SQLAlchemyError as e:
        logger.error(f"Error searching documents: {e}")
        raise

# Initialize database on import
try:
    init_db()
    logger.info("Database initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize database: {e}")
