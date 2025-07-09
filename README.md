# Quiz Generator API

A FastAPI application that accepts any file, extracts its content, and generates quiz questions using Google's Gemini AI free model.

## Features

- **Multi-format Support**: Handles TXT, PDF, DOCX, XLSX, XLS, and CSV files
- **AI-Powered Quiz Generation**: Uses Gemini AI to create intelligent quiz questions
- **Multiple Choice Questions**: Generates 4 options with correct answers and explanations
- **RESTful API**: Easy-to-use HTTP endpoints
- **File Validation**: Size and format validation with helpful error messages

## Setup

### 1. Install Dependencies

```bash
pip install -r requirement.txt
```

### 2. Get Gemini AI API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the generated API key

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_actual_api_key_here
```

### 4. Run the Application

```bash
python app/main.py
```

Or using uvicorn directly:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

### GET /
Returns API information and supported file formats.

### POST /generate-quiz
Upload a file to generate quiz questions.

**Parameters:**
- `file`: The file to process (required)
- `num_questions`: Number of questions to generate (optional, default: 5, max: 10)

**Supported File Formats:**
- TXT (Text files)
- PDF (PDF documents)
- DOCX (Word documents)
- XLSX/XLS (Excel spreadsheets)
- CSV (Comma-separated values)

**Example Response:**
```json
{
  "success": true,
  "message": "Quiz generated successfully",
  "data": {
    "filename": "document.pdf",
    "content_preview": "This is a preview of the extracted content...",
    "total_questions": 5,
    "questions": [
      {
        "question": "What is the main topic discussed in the document?",
        "options": {
          "A": "Option A",
          "B": "Option B",
          "C": "Option C",
          "D": "Option D"
        },
        "correct_answer": "A",
        "explanation": "This is correct because..."
      }
    ]
  }
}
```

### GET /health
Health check endpoint.

## Usage Examples

### Using curl

```bash
# Generate 5 questions (default)
curl -X POST "http://localhost:8000/generate-quiz" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@your_document.pdf"

# Generate 10 questions
curl -X POST "http://localhost:8000/generate-quiz" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@your_document.pdf" \
  -F "num_questions=10"
```

### Using Python requests

```python
import requests

url = "http://localhost:8000/generate-quiz"
files = {"file": open("your_document.pdf", "rb")}
data = {"num_questions": 5}

response = requests.post(url, files=files, data=data)
quiz_data = response.json()
print(quiz_data)
```

## API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Error Handling

The API includes comprehensive error handling for:
- Invalid file types
- File size limits (10MB max)
- Missing API keys
- Network issues
- File processing errors

## Limitations

- Maximum file size: 10MB
- Maximum questions per request: 10
- Content is limited to first 3000 characters for AI processing
- Requires internet connection for Gemini AI API calls

## Troubleshooting

1. **API Key Error**: Make sure your `.env` file contains the correct Gemini API key
2. **File Processing Error**: Check that your file is in a supported format
3. **Network Error**: Ensure you have internet connection for AI API calls
4. **Memory Error**: Try with smaller files or fewer questions

## License

This project is open source and available under the MIT License. 