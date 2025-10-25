import yaml
from datetime import datetime

# 读取 YAML 配置文件
with open("config.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

AIRPORT_NAMES = config['mappings']['airport_names']
AIRLINE_NAMES = config['mappings']['airline_names']


def get_airport_name(code):
    """取得機場中文名稱"""
    return AIRPORT_NAMES.get(code, code)


def get_airline_name(code):
    """取得航空公司中文名稱"""
    return AIRLINE_NAMES.get(code, code)


def parse_duration(duration_str):
    """
    解析 ISO 8601 duration 格式（例如: "PT3H30M"）
    回傳小時數（浮點數）
    """
    if not duration_str:
        return 0
    
    # 移除 "PT" 前綴
    duration_str = duration_str.replace("PT", "")
    
    hours = 0
    minutes = 0
    
    # 解析小時
    if "H" in duration_str:
        h_index = duration_str.index("H")
        hours = int(duration_str[:h_index])
        duration_str = duration_str[h_index+1:]
    
    # 解析分鐘
    if "M" in duration_str:
        m_index = duration_str.index("M")
        minutes = int(duration_str[:m_index])
    
    return hours + minutes / 60.0


def format_duration(hours):
    """
    將小時數格式化為易讀格式
    例如: 3.5 -> "3小時30分鐘"
    """
    h = int(hours)
    m = int((hours - h) * 60)
    
    if m == 0:
        return f"{h}小時"
    else:
        return f"{h}小時{m}分鐘"


def get_time_period(datetime_str):
    """
    取得時段（morning, afternoon, evening, night）
    datetime_str 格式: "2024-01-01T08:30:00"
    """
    try:
        dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        hour = dt.hour
        
        if 6 <= hour < 12:
            return "morning"
        elif 12 <= hour < 18:
            return "afternoon"
        elif 18 <= hour < 24:
            return "evening"
        else:
            return "night"
    except:
        return "any"


def format_price(price, currency="TWD"):
    """格式化價格顯示"""
    if currency == "TWD":
        return f"NT$ {price:,.0f}"
    else:
        return f"{currency} {price:,.2f}"


def calculate_price_change(old_price, new_price):
    """
    計算價格變化
    回傳: (價差, 百分比變化)
    """
    diff = new_price - old_price
    percent = (diff / old_price) * 100 if old_price > 0 else 0
    return diff, percent