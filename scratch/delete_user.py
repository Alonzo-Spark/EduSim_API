import sqlite3

try:
    conn = sqlite3.connect('edusim.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE email='test@edusim.com'")
    conn.commit()
    print("Deleted test@edusim.com from database.")
except Exception as e:
    print("Error:", e)
finally:
    conn.close()
