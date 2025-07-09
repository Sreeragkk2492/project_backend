# Environment Configuration Guide

Create a `.env` file in your project root directory with the following content:

## Required Configuration

```env
# Database Configuration
DATABASE_URL=mysql://username:password@localhost:3306/quiz_generator

# Gemini AI Configuration
GEMINI_API_KEY=your_gemini_api_key_here
```

## Complete Example

```env
# Database Configuration
# Format: mysql://username:password@host:port/database_name
DATABASE_URL=mysql://root:your_password@localhost:3306/quiz_generator

# Alternative: Individual database settings (if not using DATABASE_URL)
DB_HOST=localhost
DB_PORT=3306
DB_NAME=quiz_generator
DB_USER=root
DB_PASSWORD=your_password

# Gemini AI Configuration
# Get your API key from: https://makersuite.google.com/app/apikey
GEMINI_API_KEY=your_gemini_api_key_here
GOOGLE_API_KEY=your_google_api_key_here

# Optional: Server Configuration
HOST=0.0.0.0
PORT=8000
```

## How to Get Your Values

### 1. Database Configuration

**For MySQL:**
- `username`: Your MySQL username (usually `root`)
- `password`: Your MySQL password
- `host`: Database host (usually `localhost`)
- `port`: Database port (usually `3306`)
- `database_name`: Database name (use `quiz_generator`)

**Example:**
```env
DATABASE_URL=mysql://root:mypassword123@localhost:3306/quiz_generator
```

### 2. Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the generated API key
5. Add it to your `.env` file:

```env
GEMINI_API_KEY=AIzaSyC...your_actual_api_key_here
```

## Common Database Configurations

### Local MySQL (Default)
```env
DATABASE_URL=mysql://root:password@localhost:3306/quiz_generator
```

### MySQL with Custom User
```env
DATABASE_URL=mysql://quiz_user:userpassword@localhost:3306/quiz_generator
```

### Remote MySQL Server
```env
DATABASE_URL=mysql://username:password@your-server.com:3306/quiz_generator
```

### XAMPP/WAMP (Common)
```env
DATABASE_URL=mysql://root:@localhost:3306/quiz_generator
```

## Testing Your Configuration

After creating your `.env` file, run the database setup script:

```bash
python setup_database.py
```

This will:
- Test your database connection
- Create the database if it doesn't exist
- Create all necessary tables

## Troubleshooting

### Database Connection Issues
1. Make sure MySQL server is running
2. Verify username and password are correct
3. Check if the database exists
4. Ensure the user has proper permissions

### API Key Issues
1. Make sure you copied the full API key
2. Check if the API key is active
3. Verify you have access to Gemini API

### File Location
Make sure your `.env` file is in the project root directory (same level as `main.py`)

## Security Notes

- Never commit your `.env` file to version control
- Keep your API keys secure
- Use strong passwords for your database
- Consider using environment variables in production 