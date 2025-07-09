from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import uvicorn
import logging
import os
from dotenv import load_dotenv

# Load environment variables first
dotenv_path = os.path.join(os.path.dirname(__file__), "app", ".env")
load_dotenv(dotenv_path)

# Import after loading env vars
try:
    from app.logic import (
        process_file_and_generate_quiz, 
        list_available_models,
        save_uploaded_file,
        get_recent_uploads,
        get_document_quiz,
        search_recent_uploads,
        delete_uploaded_file
    )
except ImportError as e:
    logging.error(f"Failed to import app.logic: {e}")
    raise

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Quiz Generator API",
    description="Upload any file and generate quiz questions using Gemini AI",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Check API key and available models on startup"""
    api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
    if not api_key:
        logger.error("No API key found! Please set GEMINI_API_KEY or GOOGLE_API_KEY in your .env file")
    else:
        try:
            models = list_available_models()
            logger.info(f"Available models: {models}")
            if "gemini-pro" not in models:
                logger.error("Gemini Pro model not available with this API key")
            else:
                logger.info("API key and model verified - service ready")
        except Exception as e:
            logger.error(f"Startup verification failed: {e}")

@app.get("/")
def read_root():
    return {
        "message": "Quiz Generator API",
        "version": "1.0.0",
        "endpoints": {
            "POST /generate-quiz": "Upload a file to generate quiz questions (legacy)",
            "POST /upload": "Upload and save file to database with quiz generation",
            "GET /recent-uploads": "Get recent uploaded documents",
            "GET /quiz/{document_id}": "Get quiz for specific document",
            "GET /search": "Search uploaded documents",
            "DELETE /document/{document_id}": "Delete uploaded document",
            "GET /health": "Health check endpoint",
            "GET /models": "List available models",
            "GET /": "API information"
        },
        "supported_formats": ["txt", "pdf", "docx", "xlsx", "xls", "csv"]
    }

# @app.post("/upload")
# async def upload_file(
#     file: UploadFile = File(..., description="File to upload and process"),
#     num_questions: Optional[int] = Form(5, description="Number of questions to generate (1-10)")
# ):
#     """
#     Upload a file, save it to database, and generate quiz questions
    
#     - **file**: The file to upload (supports txt, pdf, docx, xlsx, xls, csv)
#     - **num_questions**: Number of questions to generate (default: 5, max: 10)
#     """
    
#     logger.info(f"Received file upload: {file.filename}, size: {file.size}")
    
#     # Check if API key is available
#     api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
#     if not api_key:
#         raise HTTPException(
#             status_code=500, 
#             detail="API key not configured. Please contact administrator."
#         )
    
#     # Validate file size (max 10MB)
#     if file.size and file.size > 10 * 1024 * 1024:
#         raise HTTPException(status_code=413, detail="File too large. Maximum size is 10MB.")
    
#     # Validate number of questions
#     if num_questions < 1 or num_questions > 10:
#         raise HTTPException(status_code=400, detail="Number of questions must be between 1 and 10.")
    
#     # Validate file type
#     allowed_extensions = ['txt', 'pdf', 'docx', 'xlsx', 'xls', 'csv']
#     file_extension = file.filename.lower().split('.')[-1] if file.filename else ''
    
#     if file_extension not in allowed_extensions:
#         raise HTTPException(
#             status_code=400, 
#             detail=f"Unsupported file type. Supported formats: {', '.join(allowed_extensions)}"
#         )
    
#     try:
#         # Read file content
#         file_content = await file.read()
#         logger.info(f"File content read: {len(file_content)} bytes")
        
#         # Save to database and generate quiz
#         result = save_uploaded_file(file_content, file.filename, num_questions)
        
#         logger.info(f"File uploaded and quiz generated successfully. Document ID: {result['document_id']}")
        
#         return JSONResponse(
#             content={
#                 "success": True,
#                 "message": "File uploaded and quiz generated successfully",
#                 "data": result
#             },
#             status_code=201
#         )
        
#     except ValueError as e:
#         logger.error(f"ValueError: {e}")
#         raise HTTPException(status_code=400, detail=str(e))
#     except Exception as e:
#         logger.error(f"Unexpected error: {e}")
#         raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.get("/recent-uploads")
async def get_recent_files(limit: int = Query(10, description="Number of recent uploads to return (max 50)")):
    """
    Get recent uploaded documents
    
    - **limit**: Number of recent uploads to return (default: 10, max: 50)
    """
    try:
        if limit > 50:
            limit = 50
        
        recent_files = get_recent_uploads(limit)
        
        return JSONResponse(
            content={
                "success": True,
                "data": recent_files,
                "count": len(recent_files)
            },
            status_code=200
        )
        
    except Exception as e:
        logger.error(f"Error fetching recent uploads: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching recent uploads: {str(e)}")

@app.get("/quiz/{document_id}")
async def get_quiz_by_document_id(document_id: int):
    """
    Get quiz for a specific document
    
    - **document_id**: ID of the document to get quiz for
    """
    try:
        quiz = get_document_quiz(document_id)
        
        return JSONResponse(
            content={
                "success": True,
                "data": quiz
            },
            status_code=200
        )
        
    except ValueError as e:
        logger.error(f"ValueError for document {document_id}: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting quiz for document {document_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting quiz: {str(e)}")

@app.get("/search")
async def search_documents(
    q: str = Query(..., description="Search term"),
    limit: int = Query(10, description="Number of results to return (max 50)")
):
    """
    Search uploaded documents by filename or content
    
    - **q**: Search term
    - **limit**: Number of results to return (default: 10, max: 50)
    """
    try:
        if limit > 50:
            limit = 50
        
        results = search_recent_uploads(q, limit)
        
        return JSONResponse(
            content={
                "success": True,
                "data": results,
                "count": len(results),
                "search_term": q
            },
            status_code=200
        )
        
    except Exception as e:
        logger.error(f"Error searching documents: {e}")
        raise HTTPException(status_code=500, detail=f"Error searching documents: {str(e)}")

@app.delete("/document/{document_id}")
async def delete_document(document_id: int):
    """
    Delete an uploaded document
    
    - **document_id**: ID of the document to delete
    """
    try:
        success = delete_uploaded_file(document_id)
        
        if success:
            return JSONResponse(
                content={
                    "success": True,
                    "message": f"Document {document_id} deleted successfully"
                },
                status_code=200
            )
        else:
            raise HTTPException(status_code=404, detail=f"Document {document_id} not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document {document_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")

@app.post("/generate-quiz")
async def upload_file(
    file: UploadFile = File(..., description="File to upload and process"),
    num_questions: Optional[int] = Form(5, description="Number of questions to generate (1-10)")
):
    """
    Upload a file, save it to database, and generate quiz questions
    
    - **file**: The file to upload (supports txt, pdf, docx, xlsx, xls, csv)
    - **num_questions**: Number of questions to generate (default: 5, max: 10)
    """
    
    logger.info(f"Received file upload: {file.filename}, size: {file.size}")
    
    # Check if API key is available
    api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
    if not api_key:
        raise HTTPException(
            status_code=500, 
            detail="API key not configured. Please contact administrator."
        )
    
    # Validate file size (max 10MB)
    if file.size and file.size > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 10MB.")
    
    # Validate number of questions
    if num_questions < 1 or num_questions > 10:
        raise HTTPException(status_code=400, detail="Number of questions must be between 1 and 10.")
    
    # Validate file type
    allowed_extensions = ['txt', 'pdf', 'docx', 'xlsx', 'xls', 'csv']
    file_extension = file.filename.lower().split('.')[-1] if file.filename else ''
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type. Supported formats: {', '.join(allowed_extensions)}"
        )
    
    try:
        # Read file content
        file_content = await file.read()
        logger.info(f"File content read: {len(file_content)} bytes")
        
        # Save to database and generate quiz
        result = save_uploaded_file(file_content, file.filename, num_questions)
        
        logger.info(f"File uploaded and quiz generated successfully. Document ID: {result['document_id']}")
        
        return JSONResponse(
            content={
                "success": True,
                "message": "File uploaded and quiz generated successfully",
                "data": result
            },
            status_code=201
        )
        
    except ValueError as e:
        logger.error(f"ValueError: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.get("/health")
def health_check():
    """Health check endpoint"""
    api_key_available = bool(os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY'))
    
    return {
        "status": "healthy" if api_key_available else "degraded",
        "service": "Quiz Generator API",
        "api_key_configured": api_key_available
    }

@app.get("/models")
def get_available_models():
    """List available models endpoint"""
    try:
        models = list_available_models()
        return {
            "success": True,
            "models": models,
            "count": len(models)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error listing models: {str(e)}"
        )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)