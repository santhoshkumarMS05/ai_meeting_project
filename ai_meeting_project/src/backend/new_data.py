import sqlite3

conn = sqlite3.connect("meeting_history.db")
cursor = conn.cursor()

# Add the missing columns
cursor.execute("ALTER TABLE meeting_history ADD COLUMN key_decisions TEXT")
cursor.execute("ALTER TABLE meeting_history ADD COLUMN next_steps TEXT")

conn.commit()
conn.close()
print("✅ Columns added successfully!")