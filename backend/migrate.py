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

def run_migration():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Drop food_experience_availability table if it exists
        cursor.execute("""
            DROP TABLE IF EXISTS food_experience_availability;
        """)
        
        print("Dropped food_experience_availability table")

        # Remove availability-related columns from food_experiences if they exist
        cursor.execute("""
            SELECT COUNT(*)
            FROM information_schema.columns 
            WHERE table_schema = DATABASE()
            AND table_name = 'food_experiences' 
            AND column_name = 'availability'
        """)
        
        if cursor.fetchone()[0] > 0:
            cursor.execute("""
                ALTER TABLE food_experiences
                DROP COLUMN availability
            """)
            print("Removed availability column from food_experiences")

        conn.commit()
        print("Migration completed successfully!")

    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    run_migration() 