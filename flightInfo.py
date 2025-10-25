from utils import parse_duration, format_duration, get_airline_name, get_airport_name, get_time_period
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