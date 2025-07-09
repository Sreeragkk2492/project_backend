#!/usr/bin/env python3
"""
Database Migration Script
This script updates the database table structure to handle larger files.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def migrate_database():
    """Migrate database to support larger files"""
    try:
        from app.model.db import engine, Base, UploadedDocument, QuizSession
        
        print("🔄 Starting database migration...")
        
        # Drop existing tables
        print("📋 Dropping existing tables...")
        UploadedDocument.__table__.drop(engine, checkfirst=True)
        QuizSession.__table__.drop(engine, checkfirst=True)
        
        # Recreate tables with new structure
        print("📋 Creating tables with updated structure...")
        Base.metadata.create_all(bind=engine)
        
        print("✅ Database migration completed successfully!")
        print("\nThe database now supports files up to 4GB in size.")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    migrate_database() 