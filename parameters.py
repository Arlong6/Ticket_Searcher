# 航班搜尋參數

# reference location: [TPE, NRT, ICN, HND, KIX, NGO, FUK, CTS, ITM, OSA]

# ========== Amadeus API 設定 ==========
AMADEUS_API_KEY = ""
AMADEUS_API_SECRET = ""

# API URLs (測試環境)
TOKEN_URL = "https://test.api.amadeus.com/v1/security/oauth2/token"
FLIGHT_SEARCH_URL = "https://test.api.amadeus.com/v2/shopping/flight-offers"

# 檔案設定
LAST_PRICE_FILE = "last_price.txt"
HISTORY_LOG_FILE = "flight_history.txt"
ERROR_LOG_FILE = "flight_error.txt"
EMAIL_CONTENT_FILE = "email_content.txt"
EXECUTION_LOG_FILE = "execution.log"

# 機場代碼對應中文名稱
AIRPORT_NAMES = {
    "TPE": "台北桃園", "NRT": "東京成田", "HND": "東京羽田",
    "KIX": "大阪關西", "NGO": "名古屋中部", "FUK": "福岡",
    "CTS": "札幌新千歲", "ITM": "大阪伊丹", "OSA": "大阪",
    "ICN": "首爾仁川", "SIN": "新加坡", "HKG": "香港",
    "BKK": "曼谷", "AKL": "奧克蘭"
}

# 航空公司代碼對應
AIRLINE_NAMES = {
    "BR": "長榮航空", "CI": "中華航空", "JL": "日本航空",
    "NH": "全日空", "KE": "大韓航空", "OZ": "韓亞航空",
    "SQ": "新加坡航空", "CX": "國泰航空", "TG": "泰國航空",
    "MM": "樂桃航空", "7C": "濟州航空", "IT": "台灣虎航"
}



# ========== 基本搜尋參數 ==========
departure_place = "TPE"  # 台北
destination_place = "NRT"  # 東京

start_time = "2025-11-07"
end_time = "2025-11-20"
adults = 1

SEARCH_PARAMS = {
    "originLocationCode": departure_place,
    "destinationLocationCode": destination_place,
    "departureDate": start_time,
    "returnDate": end_time,
    "adults": adults,
    "currencyCode": "TWD",
    "max": "50"  # 增加結果數量以便有更多選擇
}

# ========== 通知條件設定 ==========
NOTIFICATION_RULES = {
    # 降價門檻（滿足任一條件就通知）
    "price_drop_threshold_percent": 3.0,   # 降幅超過 3% 才通知
    "price_drop_threshold_amount": 500,    # 或降幅超過 500 元才通知
    
    # 目標價格（低於此價格就通知，設為 None 表示不啟用）
    "target_price": None,  # 例如: 15000
    
    # 是否任何降價都通知（True=忽略上面的門檻，任何降價都通知）
    "notify_on_any_drop": False,
}

# ========== 航班篩選偏好 ==========
FLIGHT_PREFERENCES = {
    # 轉機限制
    "max_stops": 0,  # 最多接受幾次轉機（0=只要直飛, 1=最多1次轉機, None=不限）
    
    # 航空公司偏好
    "preferred_airlines": [],  # 偏好的航空公司代碼，例如: ["BR", "CI"]（長榮、華航）
    "excluded_airlines": [],   # 排除的航空公司代碼，例如: ["7C", "MM"]
    
    # 飛行時間限制（單位：小時）
    "max_duration_hours": None,  # 總飛行時間上限，例如: 24（包含轉機等待時間）
    
    # 出發時段偏好（可選: "morning"=06-12, "afternoon"=12-18, "evening"=18-24, "night"=00-06, "any"=不限）
    "departure_time_preference": "any",
    "arrival_time_preference": "any",  # 抵達時段偏好
}

# ========== 顯示設定 ==========
DISPLAY_SETTINGS = {
    "max_results_in_email": 5,  # Email 中最多顯示幾個航班選項
    "show_return_flight": True,  # 是否顯示回程航班資訊
}
