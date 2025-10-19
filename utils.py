def get_airport_name(code):
    """取得機場中文名稱"""
    return AIRPORT_NAMES.get(code, code)

def get_airline_name(code):
    """取得航空公司名稱"""
    return AIRLINE_NAMES.get(code, code)

def parse_duration(duration_str):
    """解析 ISO 8601 duration (例如: PT15H30M) 轉換為小時"""
    try:
        # 移除 PT 前綴
        duration_str = duration_str.replace('PT', '')
        hours = 0
        minutes = 0
        
        if 'H' in duration_str:
            h_parts = duration_str.split('H')
            hours = int(h_parts[0])
            duration_str = h_parts[1] if len(h_parts) > 1 else ''
        
        if 'M' in duration_str:
            minutes = int(duration_str.replace('M', ''))
        
        return hours + minutes / 60.0
    except:
        return 0

def format_duration(hours):
    """將小時數格式化為易讀格式"""
    h = int(hours)
    m = int((hours - h) * 60)
    return f"{h}小時{m}分鐘"

def get_time_period(time_str):
    """判斷時間所屬時段"""
    try:
        hour = int(time_str.split('T')[1].split(':')[0])
        if 6 <= hour < 12:
            return "morning"
        elif 12 <= hour < 18:
            return "afternoon"
        elif 18 <= hour < 24:
            return "evening"
        else:
            return "night"
    except:
        return "unknown"