import datetime
from typing import Optional, Dict, Any
from zoneinfo import ZoneInfo
import requests


class Perception:
    def __init__(self, state: dict):
        # 引用外部字典以保持一致更新
        self.state = state

    def refresh(
        self,
        time_zone: str = "Asia/Shanghai",
        city: Optional[str] = None,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        更新时间与天气感知。
        - 优先使用 lat/lon；若仅给 city 则使用 Open-Meteo geocoding。
        - 使用 Open-Meteo 无需 API key 的当前天气接口。
        """
        # 时间
        now = datetime.datetime.now(ZoneInfo(time_zone))
        hour = now.hour + now.minute / 60.0
        weekday = now.weekday()  # 0=Mon
        time_str = now.strftime("%Y-%m-%d %H:%M:%S")

        info: Dict[str, Any] = {
            "local_time_str": time_str,
            "hour": hour,
            "weekday": weekday,
            "time_zone": time_zone,
        }

        # 地理反查（如需）
        if (lat is None or lon is None) and city:
            try:
                g_url = (
                    "https://geocoding-api.open-meteo.com/v1/search?" +
                    f"name={city}&count=1&language=zh&format=json"
                )
                g_res = requests.get(g_url, timeout=5)
                g_res.raise_for_status()
                data = g_res.json() or {}
                if data.get("results"):
                    r0 = data["results"][0]
                    lat = float(r0.get("latitude"))
                    lon = float(r0.get("longitude"))
                    info["geo_city"] = r0.get("name")
            except Exception:
                pass

        # 天气
        if lat is not None and lon is not None:
            try:
                w_url = (
                    "https://api.open-meteo.com/v1/forecast?" +
                    f"latitude={lat}&longitude={lon}&current_weather=true&hourly=precipitation"
                )
                w_res = requests.get(w_url, timeout=5)
                w_res.raise_for_status()
                w_data = w_res.json() or {}
                cw = w_data.get("current_weather", {})
                temp = cw.get("temperature")
                wind = cw.get("windspeed")
                weather_code = cw.get("weathercode")
                # 简单映射天气码
                desc = _code_desc(weather_code)
                info.update({
                    "weather_temp_c": temp,
                    "weather_wind": wind,
                    "weather_desc": desc,
                    "lat": lat,
                    "lon": lon,
                })
            except Exception:
                pass

        # 写入状态
        self.state.update(info)
        return info

    def update(self, values: dict):
        self.state.update(values or {})


def _code_desc(code: Optional[int]) -> str:
    mapping = {
        0: "晴", 1: "多云", 2: "局部多云", 3: "阴",
        45: "雾", 48: "霜雾",
        51: "毛毛雨", 53: "中毛毛雨", 55: "强毛毛雨",
        61: "小雨", 63: "中雨", 65: "大雨",
        71: "小雪", 73: "中雪", 75: "大雪",
        80: "阵雨", 81: "中阵雨", 82: "强阵雨",
        95: "雷雨", 96: "雷雨伴冰雹", 99: "强雷雨伴冰雹",
    }
    try:
        return mapping.get(int(code), "未知")
    except Exception:
        return "未知"

