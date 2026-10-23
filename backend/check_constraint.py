import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
database_url = os.getenv("DATABASE_URL")

if not database_url:
    print("❌ Error: DATABASE_URL not found.")
    exit(1)

try:
    connection = psycopg2.connect(database_url)
    cursor = connection.cursor()

    # Updated query to look for the module check constraint
    query = """
    SELECT conname, pg_get_constraintdef(oid) 
    FROM pg_constraint 
    WHERE conname = 'activity_log_module_check';
    """
    
    cursor.execute(query)
    result = cursor.fetchone()

    if result:
        print("\n✅ Constraint Found!")
        print(f"Definition: {result[1]}\n")
    else:
        print("\n❌ Could not find a constraint named 'activity_log_module_check'.\n")

    cursor.close()
    connection.close()

except Exception as e:
    print(f"❌ Connection error: {e}")
