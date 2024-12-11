from flask import Flask, jsonify
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from database import fetch_google_sheet_data, insert_or_update_database, clear_database

# 設定 Flask 應用
app = Flask(__name__)

SPREADSHEET_ID = "1Zs_I8c9pPyUEmiMcH4rn29vtd35BN9mfAa1qBwsdkoY"
RANGE_NAME = "表單回應 1!B2:O"  # 從第二行開始抓取資料 (B到N)

# API 路由：載入 Google Sheets 資料並插入資料庫
@app.route('/import', methods=['GET'])
def import_data():
    
    try:
        sheet_data = fetch_google_sheet_data(SPREADSHEET_ID, RANGE_NAME)
        insert_or_update_database(sheet_data)
        return jsonify({"message": "資料已成功存入 SQLite 資料庫！"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# API 路由：清除資料庫資料
@app.route('/clear', methods=['POST'])
def clear_data():
    try:
        clear_database()
        return jsonify({"message": "資料庫資料已成功清除！"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 啟動 Flask 伺服器
if __name__ == "__main__":
    app.run(debug=True)