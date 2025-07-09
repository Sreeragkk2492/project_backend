# Database Setup Guide

This guide will help you set up the MySQL database for the Quiz Generator application.

## Prerequisites

1. **MySQL Server** - Make sure MySQL is installed and running on your system
2. **Python Dependencies** - Install the required Python packages

## Quick Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Database Connection

Create a `.env` file in your project root with the following content:

```env
# Database Configuration
DATABASE_URL=mysql://username:password@localhost:3306/quiz_generator

# Alternative: Individual database settings
DB_HOST=localhost
DB_PORT=3306
DB_NAME=quiz_generator
DB_USER=your_username
DB_PASSWORD=your_password

# Gemini AI Configuration
GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. Run Database Setup Script

```bash
python setup_database.py
```

This script will:
- Create the database if it doesn't exist
- Test the connection
- Create all necessary tables

## Manual Setup

If you prefer to set up the database manually:

### 1. Create Database

Connect to MySQL and create the database:

```sql
CREATE DATABASE quiz_generator;
```

### 2. Create User (Optional)

```sql
CREATE USER 'quiz_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON quiz_generator.* TO 'quiz_user'@'localhost';
FLUSH PRIVILEGES;
```

### 3. Initialize Tables

The tables will be created automatically when you run the application, or you can run:

```python
from app.model.db import init_db
init_db()
```

## Database Schema

The application creates two main tables:

### `uploaded_documents`
- `id` - Primary key
- `filename` - Unique filename (UUID)
- `original_filename` - Original uploaded filename
- `file_extension` - File extension
- `file_size` - File size in bytes
- `file_content` - Binary file content
- `content_text` - Extracted text content
- `content_preview` - First 500 characters
- `upload_date` - Upload timestamp
- `processed` - Whether file was processed
- `quiz_generated` - Whether quiz was generated
- `quiz_questions_count` - Number of quiz questions
- `error_message` - Error message if any

### `quiz_sessions`
- `id` - Primary key
- `document_id` - Reference to uploaded document
- `session_token` - Unique session identifier
- `created_date` - Session creation timestamp
- `completed` - Whether quiz was completed
- `score` - Quiz score
- `total_questions` - Total questions in quiz
- `correct_answers` - Number of correct answers

## API Endpoints for Frontend

The following functions are available for your frontend:

### Get Recent Uploads
```python
from app.logic import get_recent_uploads

# Get last 10 uploaded files
recent_files = get_recent_uploads(limit=10)
```

### Save Uploaded File
```python
from app.logic import save_uploaded_file

# Save file and generate quiz
result = save_uploaded_file(
    file_content=file_bytes,
    original_filename="document.pdf",
    num_questions=5
)
```

### Get Document Quiz
```python
from app.logic import get_document_quiz

# Get quiz for specific document
quiz = get_document_quiz(document_id=1)
```

### Search Documents
```python
from app.logic import search_recent_uploads

# Search by filename or content
results = search_recent_uploads("search_term", limit=10)
```

### Delete Document
```python
from app.logic import delete_uploaded_file

# Delete document
success = delete_uploaded_file(document_id=1)
```

## Troubleshooting

### Connection Issues
1. Make sure MySQL server is running
2. Verify username and password in `.env` file
3. Check if the database exists
4. Ensure the user has proper permissions

### Import Errors
1. Install all dependencies: `pip install -r requirements.txt`
2. Make sure you're in the correct directory
3. Check Python path

### Permission Errors
1. Make sure the MySQL user has CREATE, INSERT, UPDATE, DELETE permissions
2. Check if the database exists and is accessible

## Example Frontend Integration

Here's how you might use this in your frontend API:

```python
from fastapi import FastAPI, UploadFile, File, HTTPException
from app.logic import save_uploaded_file, get_recent_uploads, get_document_quiz

app = FastAPI()

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        file_content = await file.read()
        result = save_uploaded_file(file_content, file.filename)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/recent-uploads")
async def get_recent_files(limit: int = 10):
    try:
        return get_recent_uploads(limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/quiz/{document_id}")
async def get_quiz(document_id: int):
    try:
        return get_document_quiz(document_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
``` 