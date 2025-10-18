# 航班搜尋參數

# reference location: [TPE, NRT, ICN, HND, KIX, NGO, FUK, CTS, ITM, OSA]

# ========== Amadeus API 設定 ==========
AMADEUS_API_KEY = ""
AMADEUS_API_SECRET = ""

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
