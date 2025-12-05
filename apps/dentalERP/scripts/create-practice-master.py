#!/usr/bin/env python3
import os
import snowflake.connector
from dotenv import load_dotenv

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

# Read and execute SQL
with open('database/snowflake/create-practice-master.sql') as f:
    sql = f.read()

for statement in sql.split(';'):
    if statement.strip():
        cursor.execute(statement)

conn.commit()

# Verify
cursor.execute("SELECT COUNT(*) FROM gold.practice_master")
count = cursor.fetchone()[0]
print(f"✅ Practice master created with {count} practices")

cursor.close()
conn.close()
