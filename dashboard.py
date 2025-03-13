from flask import Flask, jsonify, request
from flask_cors import CORS
import mysql.connector
import os

app = Flask(__name__)
CORS(app)  # ✅ Enables CORS to allow frontend access

# ✅ Database Configuration (Use environment variables)
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'ballast.proxy.rlwy.net'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', 'RnHgTWEWcuvjvlQHTKSEzYqLGGFtDUSS'),
    'database': os.getenv('DB_NAME', 'railway'),
    'port': int(os.getenv('DB_PORT', 32373))
}

def get_db_connection():
    """ ✅ Establish and return a database connection """
    return mysql.connector.connect(**DB_CONFIG)

@app.route('/get_status', methods=['GET'])
def get_status():
    """ ✅ Fetch server downtime logs based on date or history """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # ✅ Handle query parameters
    date_filter = request.args.get('date')
    today = request.args.get('today')
    history = request.args.get('history')

    query = "SELECT timestamp, url, call_initiated, recipient FROM monitor_log"

    # ✅ Apply date filters dynamically
    if today:
        query += " WHERE DATE(timestamp) = CURDATE()"
    elif date_filter:
        query += f" WHERE DATE(timestamp) = '{date_filter}'"

    query += " ORDER BY timestamp DESC"

    # ✅ Execute query and fetch data
    cursor.execute(query)
    data = cursor.fetchall()

    # ✅ Close DB connection
    cursor.close()
    conn.close()

    return jsonify(data)

# ✅ Fix Indentation Issue - Ensure Flask App Runs Properly
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Get Railway's assigned port
    app.run(host='0.0.0.0', port=port)  # ✅ Run Flask server
