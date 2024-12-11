import time
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from flask import Flask, jsonify, render_template
import threading
from flask_socketio import SocketIO, emit
from database import fetch_google_sheet_data  # 假設你有一個 fetch_google_sheet_data 函數來拉取 Google Sheets 資料

# 使用服務帳戶憑證
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_FILE = 'ledaprojct-6ce22ff6649c.json'

creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
app = Flask(__name__)
socketio = SocketIO(app)

# 指定表單 ID 和範圍
SPREADSHEET_ID = '1Zs_I8c9pPyUEmiMcH4rn29vtd35BN9mfAa1qBwsdkoY'
RANGE_NAME = '表單回應 1!B2:P'

# 初始化變數
service = build('sheets', 'v4', credentials=creds)
sheet = service.spreadsheets()

sheet_data = fetch_google_sheet_data(SPREADSHEET_ID, RANGE_NAME)

data_records = []  # 儲存目前的資料記錄
previous_row_count = 0  # 用於檢測新資料
pending_data_records = [] 
# 從 Google Sheets 獲取資料
def get_rows(sheet_data):
    # 確保 sheet_data 是一個列表
    if isinstance(sheet_data, list):
        return sheet_data  # 返回整個列表
    return []  # 如果不是列表，則返回空列表

# 循環檢查 Google Sheets 是否有新資料
def updateTable(data):
    # 從後端發送新資料後更新前端
    socketio.emit('new_data', {'data': data})

def monitor_new_records():
    global previous_row_count
    while True:
        sheet_data = fetch_google_sheet_data(SPREADSHEET_ID, RANGE_NAME)
        rows = get_rows(sheet_data)
        current_row_count = len(rows)
        
        if previous_row_count == 0:
            # 第一次執行，將所有行數不足 13 的資料加入待處理
            for current_row_count, row in enumerate(sheet_data, 1):
                if len(row) < 13:
                    new_data_with_index = {'row_index': current_row_count+1, 'data': row}
                    pending_data_records.append(new_data_with_index)

            # 推送到前端
            updateTable(pending_data_records)
            previous_row_count = current_row_count
        elif current_row_count > previous_row_count:
            print("有新資料")
            # 新增資料時，只將不重複的資料存入 templist，再推送到前端
            templist = []  # 存放本次新增的資料
            # 假設資料是存放在 sheet_data 並按行順序處理
            for i in range(previous_row_count, current_row_count+1):
                new_row = sheet_data[i]

                if len(new_row) < 13:  # 確保資料行有效
                    new_data = {'row_index': i + 1, 'data': new_row}
                    if new_data not in pending_data_records:
                        pending_data_records.append(new_data)
                        templist.append(new_data)

            # 打印檢查所有新增的資料
            # 如果 templist 不為空，進行更新
            if templist:
                updateTable(templist)
                # templist.clear()
            # 推送臨時列表到前端            
            # 更新 previous_row_count
            previous_row_count = current_row_count
        else:
            print(f"無新資料，目前行數: {current_row_count+1}")

        time.sleep(10)  # 每 10 秒檢查一次



def update_n_column(row_index, state):
    try:
        # 假設將 "已檢查" 寫入 O 列
        update_range = f"表單回應 1!N{row_index}"
        body = {
            'values': [[state]]
        }
        
        # 執行 API 更新
        sheet.values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=update_range,
            valueInputOption="RAW",
            body=body
        ).execute()
        
        print(f"成功更新第 {row_index+1} 行 N 列為：{state}")
    except Exception as e:
        print(f"更新第 {row_index+1} 行失敗: {e}")

# 使用 socket.on 來接收前端的事件
@socketio.on('accept_data')
def handle_accept_data(data):
    try:
        row_index = data['row_index']
        
        # 呼叫相同的處理邏輯
        update_n_column(row_index, '處理中')

        # 移除資料
        for i, data in enumerate(pending_data_records):
            if data['row_index'] == row_index:
                pending_data_records.pop(i)
                break
        print(pending_data_records)
        # 回傳通知前端資料已接受
        emit('data_accepted', {'row_index': row_index})
        print(f"Row {row_index} accepted.")
    except Exception as e:
        print(f"Error accepting row {row_index}: {str(e)}")

@socketio.on('reject_data')
def handle_reject_data(data):
    try:
        row_index = data['row_index']
        
        # 呼叫相同的處理邏輯
        update_n_column(row_index, '已拒絕')

        # 移除資料
        for i, data in enumerate(pending_data_records):
            if data['row_index'] == row_index:
                pending_data_records.pop(i)
                break
        print(pending_data_records)
        # 回傳通知前端資料已接受
        emit('data_rejected', {'row_index': row_index})
        print(f"Row {row_index} accepted.")
    except Exception as e:
        print(f"Error rejecting row {row_index}: {str(e)}")

# 啟動資料監控執行緒
threading.Thread(target=monitor_new_records, daemon=True).start()

# 前端連接後立即發送 pending_data_records
@socketio.on('connect')
def handle_connect():
    # 將所有待處理資料發送給前端
    emit('update_pending_list', {'data': pending_data_records})

# 網頁路由 - 顯示紀錄
@app.route('/')
def index():
    # threading.Thread(target=monitor_new_records, daemon=True).start()
    socketio.emit('new_data', {'data': 'Test data'})
    return render_template('index2.html', records=pending_data_records)

# 啟動 Flask 伺服器
if __name__ == '__main__':
    app.run(debug=True)
    socketio.run(app)

