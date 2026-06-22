import cv2
import numpy as np
import easyocr
import os
import re
import torch
import sys
import io
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from scripts.database import get_engine

engine = get_engine()
Session = sessionmaker(bind=engine)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def smart_clean_answer(txt):
    """ทำความสะอาดคำตอบ กรองขยะ และแปลงรูปแบบตัวเลข"""
    # จัดการเฉลยฟรี
    if any(k in txt for k in ["ฟรี", "ทุก", "ข้อ", "ถึก"]):
        return "FREE"

    # จัดการกรณี "หรือ" (เช่นข้อ 28 ฟิสิกส์)
    if "หรือ" in txt:
        parts = re.findall(r'\d+\.?\d*', txt)
        cleaned_parts = [str(float(p)) if '.' in p else str(int(p)) for p in parts]
        return " หรือ ".join(cleaned_parts)

    # ลบตัวอักษรไทย/อังกฤษ/สัญลักษณ์ที่ไม่ใช่เลขหรือจุด
    cleaned = re.sub(r'[^0-9.]', '', txt)

    # --- ถ้าไม่มีตัวเลขเลย (เป็นขยะ) ให้คืนค่า None ---
    if not any(char.isdigit() for char in cleaned):
        return None

    # จัดการเลขช้อยส์ติดกัน (เช่น เคมี 35 -> 3, 5)
    if len(cleaned) == 2 and '.' not in cleaned:
        if all(d in '12345' for d in cleaned):
            return f"{cleaned[0]}, {cleaned[1]}"

    try:
        # จัดการเลขทศนิยม (เช่น 0004.00 -> 4.0)
        if '.' in cleaned:
            return str(float(cleaned))
        # จัดการเลขจำนวนเต็ม (เช่น 01 -> 1)
        return str(int(cleaned))
    except:
        return cleaned if cleaned else None

def scan_and_save_to_db(folder_path, year, subject_name):

    reader = easyocr.Reader(['th', 'en'], gpu=torch.cuda.is_available())

    files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    if not files:
        print("Error: No images found in folder!")
        return

    files.sort(key=lambda x: int(re.search(r'\d+', x).group() if re.search(r'\d+', x) else 0))

    target_file = files[-1]
    target_path = os.path.join(folder_path, target_file)

    print(f"AI Scanning file: {target_file}")

    img_array = np.fromfile(target_path, np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

    results = reader.readtext(img, detail=1)
    data = []
    for (bbox, txt, prob) in results:
        x_min, y_min = bbox[0]
        x_max, y_max = bbox[2]
        data.append({
            'x': float(x_min), 'y': float(y_min),
            'w': float(x_max - x_min), 'h': float(y_max - y_min),
            'cx': (x_min + x_max) / 2, 'cy': (y_min + y_max) / 2,
            'text': txt.strip()
        })

    session = Session()
    try:
        used = set()
        match_count = 0

        for i in range(len(data)):
            if i in used: continue

            q_raw = data[i]['text'].replace('O', '0').replace('o', '0')
            q_num_only = re.sub(r'\D', '', q_raw)

            if q_num_only != "" and 1 <= int(q_num_only) <= 100:
                q_str = str(int(q_num_only))

                best_match = -1
                min_dx = 9999
                for j in range(len(data)):
                    if i == j or j in used: continue
                    dy = abs(data[i]['cy'] - data[j]['cy'])
                    dx = abs(data[j]['cx'] - data[i]['cx'])

                    if dy < 45 and 20 < dx < 500:
                        if dx < min_dx:
                            min_dx = dx
                            best_match = j

                if best_match != -1:
                    ans = smart_clean_answer(data[best_match]['text'])
                    if ans:
                        used.add(i)
                        used.add(best_match)

                        sql = text("""
                            UPDATE exam_questions
                            SET "correctAnswer" = :ans
                            WHERE year = :year
                            AND "subjectName" = :subj
                            AND "questionNumber" = :qnum
                        """)

                        result = session.execute(sql, {
                            'year': str(year),
                            'subj': subject_name,
                            'qnum': q_str,
                            'ans': ans
                        })

                        if result.rowcount > 0:
                            match_count += 1
                            # print(f"Success Update: Q{q_str} = {ans}")
                        else:
                            print(f"Mismatch: Q{q_str} not found in DB")

        session.commit()
        print(f"Finished! Updated {match_count} questions in Database.")

    except Exception as e:
        print(f"Database Error: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    base_path = r"D:\Project_Tcassist\back_py\scripts\extracted_exams"

    final_path = ""

    if len(sys.argv) > 1:
        folder_name = sys.argv[1]
        final_path = os.path.join(base_path, folder_name)
    else:
        final_path = r"D:\Project_Tcassist\back_py\scripts\extracted_exams\2568 ข้อสอบวิชา A-Level คณิตศาสตร์ประยุกต์ 1"

    if os.path.isdir(final_path):
        # ดึงชื่อโฟลเดอร์ออกมาจาก path เต็ม
        actual_folder_name = os.path.basename(final_path)

        # ดึงปีจากชื่อโฟลเดอร์
        year_match = re.search(r'\d{4}', actual_folder_name)
        year_val = year_match.group(0) if year_match else "2568"

        print(f"AI Scanning: {actual_folder_name} (Year: {year_val})")
        scan_and_save_to_db(final_path, year_val, actual_folder_name)
    else:
        print(f"Error: Folder not found at {final_path}")