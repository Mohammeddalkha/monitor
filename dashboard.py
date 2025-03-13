from flask import Flask, jsonify, request
from flask_cors import CORS
import mysql.connector

app = Flask(__name__)
CORS(app)  # ✅ Enables CORS to allow frontend access

# ✅ Database Configuration (Replace with environment variables for security)
DB_CONFIG = {
    'host': 'ballast.proxy.rlwy.net',
    'user': 'root',
    'password': 'RnHgTWEWcuvjvlQHTKSEzYqLGGFtDUSS',
    'database': 'railway',
    'port': 32373
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

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
