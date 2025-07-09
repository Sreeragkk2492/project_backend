#!/usr/bin/env python3
"""
Database Setup Script for Quiz Generator
This script helps set up the MySQL database for the quiz generator application.
"""

import os
import sys
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_database():
    """Create the database if it doesn't exist"""
    try:
        # Get database connection details
        db_host = os.getenv('DB_HOST', 'localhost')
        db_port = int(os.getenv('DB_PORT', 3306))
        db_user = os.getenv('DB_USER', 'root')
        db_password = os.getenv('DB_PASSWORD', '')
        db_name = os.getenv('DB_NAME', 'quiz_generator')
        
        # Connect to MySQL server
        connection = mysql.connector.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # Create database if it doesn't exist
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
            print(f"✅ Database '{db_name}' created successfully or already exists")
            
            cursor.close()
            connection.close()
            
            return True
            
    except Error as e:
        print(f"❌ Error creating database: {e}")
        return False

def test_connection():
    """Test the database connection"""
    try:
        from app.model.db import engine
        
        # Test connection with newer SQLAlchemy syntax
        with engine.connect() as connection:
            # Use text() for raw SQL in newer SQLAlchemy versions
            from sqlalchemy import text
            result = connection.execute(text("SELECT 1"))
            print("✅ Database connection successful!")
            return True
            
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("\nPlease check your database configuration:")
        print("1. Make sure MySQL server is running")
        print("2. Check your .env file has correct DATABASE_URL")
        print("3. Verify username and password are correct")
        return False

def main():
    """Main setup function"""
    print("🚀 Setting up Quiz Generator Database...")
    print("=" * 50)
    
    # Step 1: Create database
    print("\n📦 Step 1: Creating database...")
    if not create_database():
        print("❌ Failed to create database. Exiting.")
        sys.exit(1)
    
    # Step 2: Test connection
    print("\n🔗 Step 2: Testing database connection...")
    if not test_connection():
        print("❌ Database connection failed. Exiting.")
        sys.exit(1)
    
    # Step 3: Initialize tables
    print("\n📋 Step 3: Initializing database tables...")
    try:
        from app.model.db import init_db
        init_db()
        print("✅ Database tables created successfully!")
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        sys.exit(1)
    
    print("\n🎉 Database setup completed successfully!")
    print("\nNext steps:")
    print("1. Make sure your .env file has the correct DATABASE_URL")
    print("2. Install dependencies: pip install -r requirement.txt")
    print("3. Run your application: python main.py")

if __name__ == "__main__":
    main() 