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

def migrate_reviews():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Check if type column exists
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.columns 
            WHERE table_schema = DATABASE()
            AND table_name = 'reviews' 
            AND column_name = 'type'
        """)
        
        if cursor.fetchone()[0] == 0:
            print("Adding type column to reviews table...")
            cursor.execute("""
                ALTER TABLE reviews 
                ADD COLUMN type ENUM('food', 'stay') NOT NULL DEFAULT 'food'
            """)
            
            conn.commit()
            print("Migration successful!")
        else:
            print("Type column already exists.")

    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    migrate_reviews() 