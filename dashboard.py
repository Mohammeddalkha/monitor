from flask import Flask, jsonify, request
from flask_cors import CORS
import mysql.connector
import os

app = Flask(__name__)

# ✅ Allow only GitHub Pages domain
CORS(app, resources={r"/*": {"origins": "*"}})  # Allow all domains temporarily

DB_CONFIG = {
    'host': 'ballast.proxy.rlwy.net',
    'user': 'root',
    'password': 'RnHgTWEWcuvjvlQHTKSEzYqLGGFtDUSS',
    'database': 'railway',
    'port': 32373
}

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

@app.route('/get_status', methods=['GET'])
def get_status():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    date_filter = request.args.get('date')
    today = request.args.get('today')
    history = request.args.get('history')

    query = "SELECT timestamp, url, call_initiated, recipient FROM monitor_log"

    if today:
        query += " WHERE DATE(timestamp) = CURDATE()"
    elif date_filter:
        query += f" WHERE DATE(timestamp) = '{date_filter}'"

    query += " ORDER BY timestamp DESC"

    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    conn.close()

    return jsonify(data)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

