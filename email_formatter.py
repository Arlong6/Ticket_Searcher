"""
Email 內容格式化模組
負責生成航班價格通知的 Email 內容
"""

from datetime import datetime

# 機場代碼對應中文名稱
AIRPORT_NAMES = {
    "TPE": "台北桃園", "NRT": "東京成田", "HND": "東京羽田",
    "KIX": "大阪關西", "NGO": "名古屋中部", "FUK": "福岡",
    "CTS": "札幌新千歲", "ITM": "大阪伊丹", "OSA": "大阪",
    "ICN": "首爾仁川", "SIN": "新加坡", "HKG": "香港",
    "BKK": "曼谷", "AKL": "奧克蘭"
}

def get_airport_name(code):
    """取得機場中文名稱"""
    return AIRPORT_NAMES.get(code, code)

def format_duration(hours):
    """將小時數格式化為易讀格式"""
    h = int(hours)
    m = int((hours - h) * 60)
    return f"{h}小時{m}分鐘"

class EmailFormatter:
    """Email 內容格式化器"""
    
    def __init__(self, origin, destination, depart_date, return_date, adults):
        self.origin = origin
        self.destination = destination
        self.depart_date = depart_date
        self.return_date = return_date
        self.adults = adults
    
    def _format_date(self, date_str):
        """格式化日期為中文格式"""
        return datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y年%m月%d日")
    
    def _generate_comparison_links(self):
        """生成比價網站連結"""
        dep_date_compact = self.depart_date.replace('-', '')
        ret_date_compact = self.return_date.replace('-', '')
        
        skyscanner_url = f"https://www.skyscanner.com.tw/transport/flights/{self.origin}/{self.destination}/{dep_date_compact}/{ret_date_compact}/"
        google_flights_url = f"https://www.google.com/flights?hl=zh-TW#flt={self.origin}.{self.destination}.{self.depart_date}*{self.destination}.{self.origin}.{self.return_date}"
        
        return skyscanner_url, google_flights_url
    
    def _format_flight_details(self, flight, show_return=True):
        """格式化單個航班的詳細資訊"""
        details = []
        
        # 去程資訊
        details.append(f"【去程】{flight.airline_name} {flight.flight_number}")
        details.append(f"  出發: {flight.departure_time.replace('T', ' ')[:16]} {get_airport_name(flight.departure_airport)}")
        details.append(f"  抵達: {flight.arrival_time.replace('T', ' ')[:16]} {get_airport_name(flight.arrival_airport)}")
        details.append(f"  轉機: {'直飛' if flight.outbound_stops == 0 else f'{flight.outbound_stops}次'}")
        details.append(f"  飛行時間: {format_duration(flight.outbound_duration)}")
        
        if flight.outbound_stops > 0:
            transit_airports = ', '.join([get_airport_name(seg['arrival']['iataCode']) 
                                        for seg in flight.outbound_segments[:-1]])
            details.append(f"  轉機機場: {transit_airports}")
        
        # 回程資訊
        if show_return and flight.inbound_segments:
            first_return = flight.inbound_segments[0]
            last_return = flight.inbound_segments[-1]
            airline_name = flight.airline_name  # 可以從 flight 物件取得
            
            details.append(f"\n【回程】{airline_name}")
            details.append(f"  出發: {first_return['departure']['at'].replace('T', ' ')[:16]} {get_airport_name(first_return['departure']['iataCode'])}")
            details.append(f"  抵達: {last_return['arrival']['at'].replace('T', ' ')[:16]} {get_airport_name(last_return['arrival']['iataCode'])}")
            details.append(f"  轉機: {'直飛' if flight.inbound_stops == 0 else f'{flight.inbound_stops}次'}")
            details.append(f"  飛行時間: {format_duration(flight.inbound_duration)}")

            if flight.inbound_stops > 0:
                transit_airports = ', '.join([get_airport_name(seg['arrival']['iataCode']) 
                                            for seg in flight.inbound_segments[:-1]])
                details.append(f"  轉機機場: {transit_airports}")
        
        return "\n".join(details)
    
    def create_price_drop_email(self, last_price, new_price, filtered_flights, 
                                max_results=5, show_return=True):
        """
        建立價格下降通知 Email
        
        Args:
            last_price: 上次記錄的價格
            new_price: 目前最低價
            filtered_flights: 符合條件的航班列表 (FlightInfo 物件)
            max_results: Email 中最多顯示幾個航班選項
            show_return: 是否顯示回程資訊
        
        Returns:
            str: 格式化的 Email 內容
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        price_diff = last_price - new_price
        percentage = (price_diff / last_price) * 100
        
        dep_formatted = self._format_date(self.depart_date)
        ret_formatted = self._format_date(self.return_date)
        
        skyscanner_url, google_flights_url = self._generate_comparison_links()
        
        # Email 主體
        email_body = f"""
🎉 機票價格下降通知！

═══════════════════════════════════════
📍 航班資訊
═══════════════════════════════════════
出發地：{get_airport_name(self.origin)} ({self.origin})
目的地：{get_airport_name(self.destination)} ({self.destination})
出發日期：{dep_formatted}
回程日期：{ret_formatted}
乘客人數：{self.adults} 位成人

═══════════════════════════════════════
💰 價格變化
═══════════════════════════════════════
上次價格：NT$ {last_price:,.0f}
目前價格：NT$ {new_price:,.0f}
省下金額：NT$ {price_diff:,.0f} ({percentage:.1f}%)

═══════════════════════════════════════
✈️ 推薦航班（前 {min(len(filtered_flights), max_results)} 個符合條件的選項）
═══════════════════════════════════════
"""
        
        # 加入航班詳細資訊
        for i, flight in enumerate(filtered_flights[:max_results], 1):
            email_body += f"\n【選項 {i}】NT$ {flight.price:,.0f}\n"
            email_body += self._format_flight_details(flight, show_return)
            email_body += "\n" + "-"*50 + "\n"
        
        # 加入比價連結和提醒
        email_body += f"""
═══════════════════════════════════════
🔗 立即比價
═══════════════════════════════════════
Skyscanner: {skyscanner_url}

Google Flights: {google_flights_url}

═══════════════════════════════════════
⏰ 通知時間：{timestamp}

💡 提醒：
- 建議在多個平台比價後再下單
- 注意行李、餐食等附加費用
- 建議盡快下單，價格可能隨時變動
- 確認航班時間是否適合您的行程
"""
        return email_body
    
    def create_simple_summary(self, price, num_flights):
        """
        建立簡短的查詢摘要（用於日誌）
        
        Args:
            price: 最低價格
            num_flights: 符合條件的航班數量
        
        Returns:
            str: 一行摘要文字
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return f"[{timestamp}] {self.origin}→{self.destination} | 最低價: NT$ {price:,.0f} | 符合條件航班: {num_flights} 個"


# 便捷函數：快速建立 Email 內容
def create_flight_email(origin, destination, depart_date, return_date, adults,
                       last_price, new_price, flights, max_results=5, show_return=True):
    """
    快速建立航班價格變化通知 Email
    
    這是一個便捷函數，讓你不需要先建立 EmailFormatter 物件
    """
    formatter = EmailFormatter(origin, destination, depart_date, return_date, adults)
    return formatter.create_price_drop_email(last_price, new_price, flights, 
                                            max_results, show_return)
