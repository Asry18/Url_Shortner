from flask import Flask, request, redirect, jsonify, render_template
import mysql.connector
import hashlib
import base64
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME')
}

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

def generate_short_url(long_url):
    hash_object = hashlib.sha256(long_url.encode())
    short_hash = base64.urlsafe_b64encode(hash_object.digest())[:6].decode()
    return short_hash

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/shorten', methods=['POST'])
def shorten_url():
    long_url = request.form.get('long_url')
    if not long_url:
        return "Invalid URL", 400

    short_url = generate_short_url(long_url)

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Check if already exists
    cursor.execute("SELECT * FROM urls WHERE longurl = %s", (long_url,))
    existing = cursor.fetchone()
    if existing:
        conn.close()
        return f"Short URL already exists: <a href='/{existing['shorturl']}' target='_blank'>/{existing['shorturl']}</a>"

    # Insert into database
    cursor.execute("INSERT INTO urls (longurl, shorturl, count) VALUES (%s, %s, %s)",
                   (long_url, short_url, 0))
    conn.commit()
    conn.close()
    
    return f"Short URL is: <a href='/{short_url}' target='_blank'>/{short_url}</a>"

@app.route('/<short_url>')
def redirect_short_url(short_url):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM urls WHERE shorturl = %s", (short_url,))
    result = cursor.fetchone()

    if result:
        # Update count
        cursor.execute("UPDATE urls SET count = count + 1 WHERE shorturl = %s", (short_url,))
        conn.commit()
        conn.close()
        return redirect(result['longurl'])
    else:
        conn.close()
        return "URL not found", 404

if __name__ == '__main__':
    app.run(debug=True)
