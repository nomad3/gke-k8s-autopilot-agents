#!/usr/bin/env python3
import os
import snowflake.connector
from dotenv import load_dotenv
from pathlib import Path

load_dotenv('mcp-server/.env')

conn = snowflake.connector.connect(
    account=os.getenv('SNOWFLAKE_ACCOUNT'),
    user=os.getenv('SNOWFLAKE_USER'),
    password=os.getenv('SNOWFLAKE_PASSWORD'),
    role=os.getenv('SNOWFLAKE_ROLE'),
    warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
    database=os.getenv('SNOWFLAKE_DATABASE')
)

cursor = conn.cursor()

# Read and execute
sql_path = Path('database/snowflake/create-unified-analytics-view.sql')
with open(sql_path) as f:
    sql = f.read()

for statement in sql.split(';'):
    statement = statement.strip()
    if statement and not statement.startswith('--'):
        cursor.execute(statement)
        if 'SELECT' in statement and 'AS status' in statement:
            result = cursor.fetchone()
            if result:
                print(f"  {result[0]}")

conn.commit()

# Verify row count
cursor.execute("SELECT COUNT(*), COUNT(DISTINCT practice_id) FROM gold.practice_analytics_unified")
result = cursor.fetchone()
print(f"✅ Unified view created: {result[0]} records, {result[1]} practices")

cursor.close()
conn.close()
