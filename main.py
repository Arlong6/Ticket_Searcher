import requests
import time
import json
from datetime import datetime, timedelta
from parameters import *
from email_formatter import EmailFormatter

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

class FlightInfo:
    """航班資訊類別"""
    def __init__(self, offer_data):
        self.raw_data = offer_data
        self.price = float(offer_data["price"]["total"])
        self.currency = offer_data["price"]["currency"]
        
        # 去程資訊
        outbound = offer_data["itineraries"][0]
        self.outbound_segments = outbound["segments"]
        self.outbound_stops = len(self.outbound_segments) - 1
        self.outbound_duration = parse_duration(outbound["duration"])
        
        # 回程資訊
        if len(offer_data["itineraries"]) > 1:
            inbound = offer_data["itineraries"][1]
            self.inbound_segments = inbound["segments"]
            self.inbound_stops = len(self.inbound_segments) - 1
            self.inbound_duration = parse_duration(inbound["duration"])
        else:
            self.inbound_segments = []
            self.inbound_stops = 0
            self.inbound_duration = 0
        
        # 主要航空公司（去程第一段）
        first_segment = self.outbound_segments[0]
        self.airline_code = first_segment["carrierCode"]
        self.airline_name = get_airline_name(self.airline_code)
        self.flight_number = first_segment["number"]
        
        # 出發/抵達資訊
        self.departure_time = first_segment["departure"]["at"]
        self.departure_airport = first_segment["departure"]["iataCode"]
        
        last_segment = self.outbound_segments[-1]
        self.arrival_time = last_segment["arrival"]["at"]
        self.arrival_airport = last_segment["arrival"]["iataCode"]
        
        # 時段
        self.departure_period = get_time_period(self.departure_time)
        self.arrival_period = get_time_period(self.arrival_time)
    
    def matches_preferences(self, preferences):
        """檢查是否符合使用者偏好"""
        # 檢查轉機次數
        max_stops = preferences.get("max_stops")
        if max_stops is not None and self.outbound_stops > max_stops:
            return False
        
        # 檢查航空公司偏好
        preferred = preferences.get("preferred_airlines", [])
        if preferred and self.airline_code not in preferred:
            return False
        
        excluded = preferences.get("excluded_airlines", [])
        if excluded and self.airline_code in excluded:
            return False
        
        # 檢查飛行時間
        max_duration = preferences.get("max_duration_hours")
        if max_duration is not None and self.outbound_duration > max_duration:
            return False
        
        # 檢查出發時段
        dep_pref = preferences.get("departure_time_preference", "any")
        if dep_pref != "any" and self.departure_period != dep_pref:
            return False
        
        # 檢查抵達時段
        arr_pref = preferences.get("arrival_time_preference", "any")
        if arr_pref != "any" and self.arrival_period != arr_pref:
            return False
        
        return True
    
    def get_summary(self):
        """取得航班摘要"""
        stops_text = "直飛" if self.outbound_stops == 0 else f"{self.outbound_stops}次轉機"
        dep_time = self.departure_time.split('T')[1][:5]
        arr_time = self.arrival_time.split('T')[1][:5]
        
        return f"{self.airline_name} {self.flight_number} | {stops_text} | {dep_time}→{arr_time} | {format_duration(self.outbound_duration)}"
    
    def get_detailed_info(self, show_return=True):
        """取得詳細航班資訊"""
        info = []
        
        # 去程資訊
        info.append(f"【去程】{self.airline_name} {self.flight_number}")
        info.append(f"  出發: {self.departure_time.replace('T', ' ')[:16]} {get_airport_name(self.departure_airport)}")
        info.append(f"  抵達: {self.arrival_time.replace('T', ' ')[:16]} {get_airport_name(self.arrival_airport)}")
        info.append(f"  轉機: {'直飛' if self.outbound_stops == 0 else f'{self.outbound_stops}次'}")
        info.append(f"  飛行時間: {format_duration(self.outbound_duration)}")
        
        if self.outbound_stops > 0:
            info.append(f"  轉機機場: {', '.join([get_airport_name(seg['arrival']['iataCode']) for seg in self.outbound_segments[:-1]])}")
        
        # 回程資訊
        if show_return and self.inbound_segments:
            first_return = self.inbound_segments[0]
            last_return = self.inbound_segments[-1]
            info.append(f"\n【回程】{get_airline_name(first_return['carrierCode'])} {first_return['number']}")
            info.append(f"  出發: {first_return['departure']['at'].replace('T', ' ')[:16]} {get_airport_name(first_return['departure']['iataCode'])}")
            info.append(f"  抵達: {last_return['arrival']['at'].replace('T', ' ')[:16]} {get_airport_name(last_return['arrival']['iataCode'])}")
            info.append(f"  轉機: {'直飛' if self.inbound_stops == 0 else f'{self.inbound_stops}次'}")
            info.append(f"  飛行時間: {format_duration(self.inbound_duration)}")
            
            if self.inbound_stops > 0:
                info.append(f"  轉機機場: {', '.join([get_airport_name(seg['arrival']['iataCode']) for seg in self.inbound_segments[:-1]])}")
        
        return "\n".join(info)

class TicketSearcher:
    def __init__(self, origin, destination, depart_date, return_date):
        self.origin = origin
        self.destination = destination
        self.depart_date = depart_date
        self.return_date = return_date
        self.execution_start = datetime.now()

    def log_to_file(self, filename, content, mode='a'):
        """寫入日誌檔案"""
        try:
            with open(filename, mode, encoding='utf-8') as f:
                f.write(content)
                if mode == 'a':
                    f.write('\n' + '='*80 + '\n\n')
        except Exception as e:
            print(f"⚠️ 寫入檔案失敗: {e}")

    def log_execution(self, status, message=""):
        """記錄執行狀態"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {status}"
        if message:
            log_entry += f" - {message}"
        log_entry += "\n"
        
        try:
            with open(EXECUTION_LOG_FILE, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            lines = lines[-99:] if len(lines) >= 100 else lines
            lines.append(log_entry)
            with open(EXECUTION_LOG_FILE, 'w', encoding='utf-8') as f:
                f.writelines(lines)
        except FileNotFoundError:
            with open(EXECUTION_LOG_FILE, 'w', encoding='utf-8') as f:
                f.write(log_entry)

    def log_error(self, error_msg, error_detail=""):
        """記錄錯誤"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_content = f"""
❌ 錯誤發生時間: {timestamp}
錯誤訊息: {error_msg}
"""
        if error_detail:
            log_content += f"詳細資訊: {error_detail}\n"
        
        print(log_content)
        self.log_to_file(ERROR_LOG_FILE, log_content)
        self.log_execution("ERROR", error_msg)

    def should_notify(self, last_price, new_price):
        """判斷是否應該發送通知"""
        rules = NOTIFICATION_RULES
        
        # 如果價格上升或不變，不通知
        if new_price >= last_price:
            return False, "價格未下降"
        
        # 計算降幅
        price_drop = last_price - new_price
        drop_percent = (price_drop / last_price) * 100
        
        # 檢查是否任何降價都通知
        if rules.get("notify_on_any_drop", False):
            return True, f"任何降價都通知模式 (降幅: {price_drop:.0f}, {drop_percent:.1f}%)"
        
        # 檢查目標價格
        target_price = rules.get("target_price")
        if target_price is not None and new_price <= target_price:
            return True, f"達到目標價格 NT$ {target_price:,.0f}"
        
        # 檢查降幅門檻（百分比或金額，滿足其一即可）
        threshold_percent = rules.get("price_drop_threshold_percent", 0)
        threshold_amount = rules.get("price_drop_threshold_amount", 0)
        
        if drop_percent >= threshold_percent:
            return True, f"降幅 {drop_percent:.1f}% 超過門檻 {threshold_percent}%"
        
        if price_drop >= threshold_amount:
            return True, f"降幅 NT$ {price_drop:.0f} 超過門檻 NT$ {threshold_amount}"
        
        return False, f"降幅不足 (降幅: {price_drop:.0f}, {drop_percent:.1f}%)"

    def create_email_content(self, last_price, new_price, filtered_flights):
        """建立 Email 內容（使用 EmailFormatter）"""
        formatter = EmailFormatter(
            self.origin,
            self.destination,
            self.depart_date,
            self.return_date,
            SEARCH_PARAMS['adults']
        )
        
        return formatter.create_price_drop_email(
            last_price,
            new_price,
            filtered_flights,
            max_results=DISPLAY_SETTINGS['max_results_in_email'],
            show_return=DISPLAY_SETTINGS['show_return_flight']
        )

    def get_access_token(self):
        """取得 Amadeus API 的 access token"""
        print("🔑 正在取得 Access Token...")
        try:
            response = requests.post(
                TOKEN_URL,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data={
                    "grant_type": "client_credentials",
                    "client_id": AMADEUS_API_KEY,
                    "client_secret": AMADEUS_API_SECRET
                },
                timeout=10
            )
            
            if response.status_code != 200:
                error_msg = f"Token 取得失敗 (狀態碼: {response.status_code})"
                self.log_error(error_msg, response.text)
                return None
                
            token_data = response.json()
            token = token_data["access_token"]
            print("✅ 成功取得 Access Token")
            return token
            
        except Exception as e:
            self.log_error("取得 Access Token 失敗", str(e))
            return None

    def get_flights(self):
        """查詢航班並回傳所有符合條件的航班"""
        token = self.get_access_token()
        if not token:
            return None
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }
        
        try:
            print(f"🔍 正在查詢航班: {self.origin} → {self.destination}")
            print(f"📅 出發日期: {self.depart_date}")
            print(f"📅 回程日期: {self.return_date}")
            
            response = requests.get(
                FLIGHT_SEARCH_URL,
                headers=headers,
                params=SEARCH_PARAMS,
                timeout=15
            )
            
            if response.status_code != 200:
                error_msg = f"航班查詢失敗 (狀態碼: {response.status_code})"
                self.log_error(error_msg, response.text)
                return None
            
            data = response.json()
            
            # 儲存完整 API 回應
            with open("api_response.json", "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            if "data" not in data or len(data["data"]) == 0:
                self.log_error("沒有找到任何航班", str(data.get('errors', '')))
                return None
            
            # 解析所有航班
            all_flights = []
            for offer in data["data"]:
                try:
                    flight = FlightInfo(offer)
                    all_flights.append(flight)
                except Exception as e:
                    print(f"⚠️ 解析航班失敗: {e}")
                    continue
            
            if not all_flights:
                self.log_error("無法解析任何航班資料")
                return None
            
            # 篩選符合偏好的航班
            filtered_flights = [f for f in all_flights if f.matches_preferences(FLIGHT_PREFERENCES)]
            
            if not filtered_flights:
                print("⚠️ 沒有找到符合偏好條件的航班，顯示所有航班")
                filtered_flights = all_flights
            
            # 按價格排序
            filtered_flights.sort(key=lambda x: x.price)
            
            print(f"\n找到 {len(filtered_flights)} 個符合條件的航班:")
            print("-" * 80)
            
            for i, flight in enumerate(filtered_flights[:10], 1):
                print(f"{i}. NT$ {flight.price:,.0f} - {flight.get_summary()}")
            
            print("-" * 80)
            print(f"💰 最低票價: NT$ {filtered_flights[0].price:,.0f}\n")
            
            return filtered_flights
            
        except Exception as e:
            self.log_error("查詢航班時發生錯誤", str(e))
            return None

    def check_price(self):
        """檢查價格是否有變化"""
        print(f"\n{'='*60}")
        print(f"⏰ 執行時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print('='*60)
        
        self.log_execution("START", "開始查詢航班價格")
        
        # 查詢航班
        filtered_flights = self.get_flights()
        if not filtered_flights:
            print("⚠️ 無法取得航班資訊")
            self.log_execution("FAILED", "無法取得航班資訊")
            return False
        
        new_price = filtered_flights[0].price  # 最低價
        
        # 記錄簡易日誌（使用 EmailFormatter）
        formatter = EmailFormatter(
            self.origin,
            self.destination,
            self.depart_date,
            self.return_date,
            SEARCH_PARAMS['adults']
        )
        summary = formatter.create_simple_summary(new_price, len(filtered_flights))
        self.log_to_file(HISTORY_LOG_FILE, summary)
        
        # 讀取上次記錄的價格
        try:
            with open(LAST_PRICE_FILE, "r") as f:
                last_price = float(f.read().strip())
        except FileNotFoundError:
            print("📝 首次執行，記錄當前價格")
            with open(LAST_PRICE_FILE, "w") as f:
                f.write(str(new_price))
            self.log_execution("SUCCESS", f"首次執行，記錄價格: {new_price}")
            return True
        except Exception as e:
            self.log_error("讀取歷史價格失敗", str(e))
            return False
        
        # 判斷是否需要通知
        should_send, reason = self.should_notify(last_price, new_price)
        
        price_diff = last_price - new_price
        
        if new_price < last_price:
            print(f"📉 價格下降：NT$ {last_price:,.0f} → NT$ {new_price:,.0f} (-{price_diff:.0f}, -{(price_diff/last_price)*100:.1f}%)")
        elif new_price > last_price:
            print(f"📈 價格上升：NT$ {last_price:,.0f} → NT$ {new_price:,.0f} (+{abs(price_diff):.0f}, +{(abs(price_diff)/last_price)*100:.1f}%)")
        else:
            print(f"💤 價格沒變化：NT$ {new_price:,.0f}")
        
        print(f"📋 通知判斷: {reason}")
        
        # 發送通知
        if should_send:
            email_content = self.create_email_content(last_price, new_price, filtered_flights)
            self.log_to_file(EMAIL_CONTENT_FILE, email_content, mode='w')
            
            print("\n📧 符合通知條件！正在發送 Email...")
            
            try:
                from mailer import send_email
                send_email(email_content)
                print("✅ Email 通知已成功發送！")
                self.log_execution("EMAIL_SENT", f"{reason}")
            except ImportError:
                print("⚠️ 找不到 mailer.py，Email 內容已儲存至 email_content.txt")
                self.log_execution("EMAIL_SKIPPED", "找不到 mailer.py")
            except Exception as e:
                print(f"❌ Email 發送失敗: {e}")
                self.log_error("Email 發送失敗", str(e))
            
            # 更新價格記錄
            with open(LAST_PRICE_FILE, "w") as f:
                f.write(str(new_price))
        else:
            print("💤 不符合通知條件，本次不發送通知")
            self.log_execution("SUCCESS", f"價格變化但不通知: {reason}")
        
        return True

    def run(self):
        """執行一次完整的檢查流程"""
        print("\n" + "="*60)
        print("✈️  航班價格監控系統（強化版）")
        print("="*60)
        print(f"📍 路線: {get_airport_name(self.origin)} → {get_airport_name(self.destination)}")
        print(f"📅 日期: {self.depart_date} ~ {self.return_date}")
        print(f"👤 人數: {SEARCH_PARAMS['adults']} 位成人")
        print(f"💱 幣別: {SEARCH_PARAMS['currencyCode']}")
        print("\n【篩選條件】")
        
        # 顯示轉機限制
        max_stops = FLIGHT_PREFERENCES.get('max_stops')
        if max_stops is not None:
            if max_stops == 0:
                print("  ✓ 只接受直飛")
            else:
                print(f"  ✓ 最多 {max_stops} 次轉機")
        
        # 顯示航空公司偏好
        preferred = FLIGHT_PREFERENCES.get('preferred_airlines', [])
        if preferred:
            print(f"  ✓ 偏好航空: {', '.join([get_airline_name(code) for code in preferred])}")
        
        excluded = FLIGHT_PREFERENCES.get('excluded_airlines', [])
        if excluded:
            print(f"  ✗ 排除航空: {', '.join([get_airline_name(code) for code in excluded])}")
        
        # 顯示時段偏好
        dep_pref = FLIGHT_PREFERENCES.get('departure_time_preference', 'any')
        if dep_pref != 'any':
            print(f"  ✓ 出發時段: {dep_pref}")
        
        arr_pref = FLIGHT_PREFERENCES.get('arrival_time_preference', 'any')
        if arr_pref != 'any':
            print(f"  ✓ 抵達時段: {arr_pref}")
        
        print("\n【通知條件】")
        rules = NOTIFICATION_RULES
        
        if rules.get('notify_on_any_drop', False):
            print("  🔔 任何降價都通知")
        else:
            threshold_percent = rules.get('price_drop_threshold_percent', 0)
            threshold_amount = rules.get('price_drop_threshold_amount', 0)
            
            if threshold_percent > 0:
                print(f"  🔔 降幅超過 {threshold_percent}% 才通知")
            if threshold_amount > 0:
                print(f"  🔔 降幅超過 NT$ {threshold_amount} 才通知")
        
        target_price = rules.get('target_price')
        if target_price:
            print(f"  🎯 目標價格: NT$ {target_price:,.0f}")
        
        print("="*60 + "\n")
        
        success = self.check_price()
        
        # 計算執行時間
        execution_time = (datetime.now() - self.execution_start).total_seconds()
        print(f"\n⏱️  執行時間: {execution_time:.2f} 秒")
        
        if success:
            print("✅ 執行完成")
        else:
            print("❌ 執行過程中發生錯誤，請查看錯誤日誌")
        
        return success

if __name__ == "__main__":
    searcher = TicketSearcher(
        SEARCH_PARAMS['originLocationCode'],
        SEARCH_PARAMS['destinationLocationCode'],
        SEARCH_PARAMS['departureDate'],
        SEARCH_PARAMS['returnDate']
    )
    
    if AMADEUS_API_KEY == "YOUR_CLIENT_ID" or AMADEUS_API_SECRET == "YOUR_CLIENT_SECRET":
        print("❌ 請先在 parameters.py 填入你的 Amadeus API Key 和 Secret！")
        exit(1)
    else:
        success = searcher.run()
        exit(0 if success else 1)
