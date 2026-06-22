from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
from scipy import stats

app = FastAPI()

# เพิ่ม CORS เพื่อให้หลังบ้านคุยกับส่วนอื่นๆ ได้ไม่ติดขัด
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/analyze-advanced-risk")
async def analyze_risk(payload: dict):
    try:
        # ดึงข้อมูลดิบและป้องกันค่า Error
        user_score = float(payload.get("userScore", 0))
        history_raw = payload.get("historyData", [])

        print(f"Received userScore: {user_score}")

        # กรองและปรับฐานคะแนน (Data Cleaning)
        min_scores = []
        for item in history_raw:
            val = item.get("minScore") or item.get("min_score")

            if val is not None:
                try:
                    score = float(val)
                    if score <= 0: continue

                    # ปรับฐานคะแนน
                    if score > 300:
                        score = (score / 30000) * 100
                    elif 100 < score <= 300:
                        score = (score / 300) * 100

                    min_scores.append(score)
                except (ValueError, TypeError):
                    continue

        # กรณีไม่มีข้อมูลเลย
        if not min_scores:
            print("No valid history scores found.")
            return {
                "status": "Error",
                "color": "Gray",
                "message": "ไม่พบข้อมูลสถิติที่ใช้งานได้",
                "chance_percent": 0
            }

        # คำนวณทางสถิติ
        latest_min = min_scores[-1]
        avg_min = np.mean(min_scores)
        std_dev = np.std(min_scores) if np.std(min_scores) > 0 else 1.0

        # คำนวณ % โอกาสติด (Z-Score)
        z_score = (user_score - avg_min) / std_dev
        chance_percent = round(stats.norm.cdf(z_score) * 100, 2)

        # Logic พิเศษ: ถ้าคะแนนดีกว่าค่าเฉลี่ย หรือชนะปีล่าสุด ห้ามเป็นสีแดง
        if (user_score >= latest_min or user_score >= avg_min) and chance_percent < 50:
            chance_percent = 55.0

        # ตัดสินผลและ "บังคับสี" (Decision Logic)
        if chance_percent >= 75:
            status = "Safe"
            color = "Green"
            message = "ปลอดภัยมาก โอกาสติดสูงตามสถิติ"
        elif chance_percent >= 45:
            status = "Passable"
            color = "Yellow"  # บังคับเป็นสีเหลือง
            message = "มีโอกาสลุ้น คะแนนอยู่ในเกณฑ์มาตรฐาน"
        else:
            status = "Risk"
            color = "Red"
            message = "มีความเสี่ยง คะแนนต่ำกว่าเกณฑ์เฉลี่ยปีก่อนๆ"

        # แสดงผลใน Terminal เพื่อตรวจสอบ
        print(f"Final Result: {status} | Color: {color} | Chance: {chance_percent}%")

        return {
            "status": status,
            "color": color,
            "chance_percent": chance_percent,
            "score_gap": round(user_score - latest_min, 4),
            "message": message,
            "analysis": {
                "z_score": round(z_score, 4),
                "avg_history": round(avg_min, 2),
                "data_points": len(min_scores)
            }
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            "status": "Error",
            "message": f"AI Error: {str(e)}",
            "color": "Gray"
        }