import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'user': os.getenv('MYSQL_USER'),
    'password': os.getenv('MYSQL_PASSWORD'),
    'database': os.getenv('MYSQL_DATABASE')
}

def migrate_bathrooms():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Check if bathrooms column exists
        cursor.execute("""
            SELECT COUNT(*)
            FROM information_schema.columns 
            WHERE table_schema = 'platform2025'
            AND table_name = 'stays' 
            AND column_name = 'bathrooms'
        """)
        
        if cursor.fetchone()[0] == 0:
            print("Adding bathrooms column to stays table...")
            cursor.execute("""
                ALTER TABLE stays
                ADD COLUMN bathrooms INT DEFAULT 1
            """)
            
            # Update existing stays to have bathrooms equal to bedrooms
            cursor.execute("""
                UPDATE stays 
                SET bathrooms = bedrooms 
                WHERE bathrooms IS NULL
            """)
            
            conn.commit()
            print("Migration successful!")
        else:
            print("Bathrooms column already exists.")

    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    migrate_bathrooms() 