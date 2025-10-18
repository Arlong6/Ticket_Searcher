import requests
import time
import json
from datetime import datetime
from parameters import *

# ========== Amadeus API 設定 ==========
AMADEUS_API_KEY = "xqTFrAYGLdGAgAdKGwcCAGQmn18G5ILL"
AMADEUS_API_SECRET = "oTkmuvpjX5QOiAj8"

# API URLs (測試環境)
TOKEN_URL = "https://test.api.amadeus.com/v1/security/oauth2/token"
FLIGHT_SEARCH_URL = "https://test.api.amadeus.com/v2/shopping/flight-offers"

# 檔案設定
LAST_PRICE_FILE = "last_price.txt"
HISTORY_LOG_FILE = "flight_history.txt"      # 完整歷史記錄
ERROR_LOG_FILE = "flight_error.txt"           # 錯誤日誌
EMAIL_CONTENT_FILE = "email_content.txt"      # 單次 Email 內容
EXECUTION_LOG_FILE = "execution.log"          # 執行記錄（監控用）

# 機場代碼對應中文名稱
AIRPORT_NAMES = {
    "TPE": "台北桃園",
    "NRT": "東京成田",
    "AKL": "奧克蘭",
    "HND": "東京羽田",
    "KIX": "大阪關西",
    "ICN": "首爾仁川",
    "SIN": "新加坡",
    "HKG": "香港",
    "BKK": "曼谷"
}

def get_airport_name(code):
    """取得機場中文名稱"""
    return AIRPORT_NAMES.get(code, code)

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
                if mode == 'a':  # append 模式才加分隔線
                    f.write('\n' + '='*80 + '\n\n')
        except Exception as e:
            print(f"⚠️ 寫入檔案失敗: {e}")

    def log_execution(self, status, message=""):
        """記錄執行狀態（用於監控）"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {status}"
        if message:
            log_entry += f" - {message}"
        log_entry += "\n"
        
        # 保持執行日誌在合理大小（最多保留最近 100 行）
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
        """記錄錯誤到 error log"""
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

    def create_simple_summary(self, price_data):
        """建立簡潔的查詢摘要（用於歷史記錄）"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return f"[{timestamp}] {self.origin}→{self.destination} | 最低價: NT$ {price_data['lowest_price']:,.0f}"

    def create_detailed_log(self, price_data):
        """建立詳細的查詢日誌（用於完整記錄）"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        dep_formatted = datetime.strptime(self.depart_date, "%Y-%m-%d").strftime("%Y年%m月%d日")
        ret_formatted = datetime.strptime(self.return_date, "%Y-%m-%d").strftime("%Y年%m月%d日")
        
        log_content = f"""
✅ 查詢成功時間: {timestamp}

【航班資訊】
出發地: {get_airport_name(self.origin)} ({self.origin})
目的地: {get_airport_name(self.destination)} ({self.destination})
出發日期: {dep_formatted}
回程日期: {ret_formatted}
乘客人數: {SEARCH_PARAMS['adults']} 位成人

【價格資訊】
最低票價: NT$ {price_data['lowest_price']:,.0f}
"""
        
        if 'flights' in price_data and price_data['flights']:
            log_content += "\n【前5個航班選項】\n"
            for i, flight in enumerate(price_data['flights'][:5], 1):
                log_content += f"{i}. {flight['airline']}{flight['flight_num']} - NT$ {flight['price']:,.0f} - {flight['departure']}\n"
        
        return log_content

    def create_email_content(self, last_price, new_price):
        """建立 Email 內容（只包含本次價格變化）"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        price_diff = abs(new_price - last_price)
        percentage = (price_diff / last_price) * 100 if last_price > 0 else 0
        
        dep_formatted = datetime.strptime(self.depart_date, "%Y-%m-%d").strftime("%Y年%m月%d日")
        ret_formatted = datetime.strptime(self.return_date, "%Y-%m-%d").strftime("%Y年%m月%d日")
        
        # 生成 Skyscanner 連結
        dep_date_compact = self.depart_date.replace('-', '')
        ret_date_compact = self.return_date.replace('-', '')
        skyscanner_url = f"https://www.skyscanner.com.tw/transport/flights/{self.origin}/{self.destination}/{dep_date_compact}/{ret_date_compact}/"
        
        email_body = f"""
🎉 機票價格下降通知！

═══════════════════════════════════════
📍 航班資訊
═══════════════════════════════════════
出發地：{get_airport_name(self.origin)} ({self.origin})
目的地：{get_airport_name(self.destination)} ({self.destination})
出發日期：{dep_formatted}
回程日期：{ret_formatted}
乘客人數：{SEARCH_PARAMS['adults']} 位成人

═══════════════════════════════════════
💰 價格變化
═══════════════════════════════════════
上次價格：NT$ {last_price:,.0f}
目前價格：NT$ {new_price:,.0f}
省下金額：NT$ {price_diff:,.0f} ({percentage:.1f}%)

═══════════════════════════════════════
🔗 立即比價
═══════════════════════════════════════
Skyscanner: {skyscanner_url}

Google Flights: https://www.google.com/flights

═══════════════════════════════════════
⏰ 通知時間：{timestamp}

💡 提醒：
- 建議在多個平台比價後再下單
- 注意行李、餐食等附加費用
- 建議盡快下單，價格可能隨時變動
"""
        return email_body

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

    def get_lowest_price(self):
        """查詢航班並回傳最低票價"""
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
            
            # 解析航班資料
            prices = []
            flights_info = []
            
            print(f"\n找到 {len(data['data'])} 個航班選項:")
            print("-" * 60)
            
            for i, offer in enumerate(data["data"][:5], 1):
                try:
                    price = float(offer["price"]["total"])
                    prices.append(price)
                    
                    segments = offer["itineraries"][0]["segments"]
                    first_segment = segments[0]
                    airline = first_segment["carrierCode"]
                    flight_num = first_segment["number"]
                    departure = first_segment["departure"]["at"]
                    
                    flights_info.append({
                        'airline': airline,
                        'flight_num': flight_num,
                        'price': price,
                        'departure': departure
                    })
                    
                    print(f"{i}. {airline}{flight_num} - {price:.0f} TWD - {departure}")
                    
                except (KeyError, ValueError, IndexError):
                    continue
            
            if not prices:
                self.log_error("無法解析任何價格資料")
                return None
            
            lowest_price = min(prices)
            print("-" * 60)
            print(f"💰 最低票價: {lowest_price:.0f} TWD\n")
            
            # 記錄到歷史日誌
            price_data = {
                'lowest_price': lowest_price,
                'flights': flights_info
            }
            
            # 簡潔摘要（一行）
            summary = self.create_simple_summary(price_data)
            self.log_to_file(HISTORY_LOG_FILE, summary)
            
            # 詳細記錄（可選，如果需要完整資訊）
            # detailed_log = self.create_detailed_log(price_data)
            # self.log_to_file(HISTORY_LOG_FILE + ".detailed", detailed_log)
            
            return lowest_price
            
        except Exception as e:
            self.log_error("查詢航班時發生錯誤", str(e))
            return None

    def check_price(self):
        """檢查價格是否有變化"""
        print(f"\n{'='*60}")
        print(f"⏰ 執行時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print('='*60)
        
        self.log_execution("START", "開始查詢航班價格")
        
        new_price = self.get_lowest_price()
        if new_price is None:
            print("⚠️ 無法取得價格資訊")
            self.log_execution("FAILED", "無法取得價格資訊")
            return False
        
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
        
        # 判斷價格變化
        price_diff = new_price - last_price
        
        if new_price < last_price:
            # 價格下降 - 發送 Email
            print(f"🎉 價格下降！{last_price:.0f} → {new_price:.0f}")
            
            # 建立 Email 內容（只包含本次變化）
            email_content = self.create_email_content(last_price, new_price)
            
            # 寫入 Email 內容檔案（覆蓋模式）
            self.log_to_file(EMAIL_CONTENT_FILE, email_content, mode='w')
            
            print("\n📧 價格下降！正在發送 Email 通知...")
            
            # 發送 Email
            try:
                from mailer import send_email
                send_email(email_content)
                print("✅ Email 通知已成功發送！")
                self.log_execution("EMAIL_SENT", f"價格下降 {price_diff:.0f}，已發送通知")
            except ImportError:
                print("⚠️ 找不到 mailer.py，Email 內容已儲存至 email_content.txt")
                self.log_execution("EMAIL_SKIPPED", "找不到 mailer.py")
            except Exception as e:
                print(f"❌ Email 發送失敗: {e}")
                self.log_error("Email 發送失敗", str(e))
            
            # 更新價格記錄
            with open(LAST_PRICE_FILE, "w") as f:
                f.write(str(new_price))
            
        elif new_price > last_price:
            print(f"📈 價格上升：{last_price:.0f} → {new_price:.0f} (+{price_diff:.0f})")
            self.log_execution("SUCCESS", f"價格上升 {price_diff:.0f}")
            
        else:
            print(f"💤 價格沒變化：{new_price:.0f} TWD")
            self.log_execution("SUCCESS", f"價格不變 {new_price:.0f}")
        
        return True

    def run(self):
        """執行一次完整的檢查流程"""
        print("\n" + "="*60)
        print("✈️  航班價格監控系統")
        print("="*60)
        print(f"📍 路線: {get_airport_name(self.origin)} → {get_airport_name(self.destination)}")
        print(f"📅 日期: {self.depart_date} ~ {self.return_date}")
        print(f"👤 人數: {SEARCH_PARAMS['adults']} 位成人")
        print(f"💱 幣別: {SEARCH_PARAMS['currencyCode']}")
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
        print("❌ 請先填入你的 Amadeus API Key 和 Secret！")
        exit(1)
    else:
        success = searcher.run()
        exit(0 if success else 1)
