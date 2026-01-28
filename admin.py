import mysql.connector
import bcrypt

# Database connection
def get_connection():
    return mysql.connector.connect(
        host='localhost',         # or your DB host
        user='root',
        password='',
        database='autism'
    )

# Insert user with hashed password
def insert_user(user_id, plain_password):
    hashed = bcrypt.hashpw(plain_password.encode('utf-8'), bcrypt.gensalt())
    
    conn = get_connection()
    cursor = conn.cursor()
    query = "INSERT INTO admin (email, password) VALUES (%s, %s)"
    cursor.execute(query, (user_id, hashed.decode('utf-8')))
    
    conn.commit()
    cursor.close()
    conn.close()
    print("User inserted successfully.")




# Example usage
if __name__ == "__main__":
    # Insert a user
    insert_user("admin1@gmail.com", "adminpass123")

    