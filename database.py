import sqlite3
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from datetime import datetime
# # Google Sheets 設定
# SPREADSHEET_ID = "1Zs_I8c9pPyUEmiMcH4rn29vtd35BN9mfAa1qBwsdkoY"
# RANGE_NAME = "表單回應 1!B2:O"  # 從第二行開始抓取資料 (B到N)

# 連線到 Google Sheets
def fetch_google_sheet_data(SPREADSHEET_ID, RANGE_NAME):
    creds = Credentials.from_service_account_file("ledaprojct-6ce22ff6649c.json")
    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
    return result.get('values', [])

def insert_or_update_database(data):
    # print(data)
    conn = sqlite3.connect("tasks.db")  # 建立 SQLite 資料庫檔案
    cursor = conn.cursor()

    # 建立資料表 (若尚未建立)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            applicant TEXT,
            project_name TEXT,
            task_type TEXT,
            task_detail TEXT,            
            intern_NAS TEXT,
            urgency_leval TEXT,
            urgency_reson TEXT,
            start_date TEXT,
            deadline TEXT,
            diffculty_level TEXT,
            additional_info TEXT,
            email TEXT,
            status TEXT
        )
    """)

    # 插入或更新資料
    for row in data:
        # 確保資料行長度為13，若不足，填充缺失欄位為 None
        if len(row) < 13:
            print(f"Skipping incomplete row: {row}")
            row.extend([None] * (13 - len(row)))  # 將缺少的欄位補充為 None

        # 將日期轉換為標準格式 (若需要)
        start_date = None
        deadline = None
        try:
            start_date = datetime.strptime(row[7], "%Y/%m/%d").date() if row[6] else None  # start_date是第6列
            deadline = datetime.strptime(row[8], "%Y/%m/%d").date() if row[7] else None  # deadline是第7列
        except ValueError:
            pass  # 忽略格式錯誤的日期

        # 檢查專案名稱是否存在
        cursor.execute("""
            SELECT id FROM tasks WHERE project_name = ?
        """, (row[1],))
        existing_row = cursor.fetchone()

        if existing_row:
            # 如果專案名稱存在，更新整個資料行
            try:
                start_date = datetime.strptime(row[7], "%Y/%m/%d").date() if row[7] else None
                deadline = datetime.strptime(row[8], "%Y/%m/%d").date() if row[8] else None

                cursor.execute("""
                    UPDATE tasks
                    SET applicant=?, project_name=?, task_type=?, task_detail=?, intern_NAS=?, urgency_leval=?, urgency_reson=?,
                        start_date=?, deadline=?, diffculty_level=?, additional_info=?, email=?, status=?
                    WHERE project_name=?
                """, (row[0], row[1], row[2], row[3], row[4], row[5], row[6], start_date, deadline, row[9], row[10], row[11], row[12],row[1]))
                conn.commit()
                print(f"Record updated for project: {row[1]}")
            except sqlite3.Error as e:
                print(f"Error updating record: {e}")
        else:
            # 如果專案名稱不存在，插入新資料
            cursor.execute("""
                INSERT INTO tasks (applicant, project_name, task_type, task_detail, intern_NAS, urgency_leval, urgency_reson,
                                   start_date, deadline, diffculty_level, additional_info, email, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (row[0], row[1], row[2], row[3], row[4], row[5], row[6], start_date, deadline, row[9], row[10], row[11], row[12]))

            print(f"Inserted new row for project: {row[1]}")

    conn.commit()
    cursor.close()
    conn.close()

def clear_database():
    conn = sqlite3.connect("tasks.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks")  # 清除所有資料
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='tasks'")  # 重設自增計數器
    conn.commit()
    cursor.close()
    conn.close()


