import cv2
import requests
import os
import re
import numpy as np

IMAGE_ROOT = r"D:\Project_Tcassist\back_py\scripts\extracted_exams"
API_URL = "http://localhost:3000/exams/questions"

def send_to_nestjs(payload):
    try:
        # ใช้ POST เพื่อไปทำการ Upsert ใน NestJS
        res = requests.post(API_URL, json=payload, timeout=5)
        return res.status_code == 201 or res.status_code == 200
    except: return False

def process_smart_layout_scan(img, page_num, year, subject_folder, start_q):
    h_img, w_img = img.shape[:2]

    # พิกัดมาตรฐานที่จูนไว้
    top_limit = 265
    bottom_limit = h_img - 150
    left_limit = 100
    right_limit = w_img - 100

    content_zone = img[top_limit:bottom_limit, left_limit:right_limit]
    gray = cv2.cvtColor(content_zone, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 220, 255, cv2.THRESH_BINARY_INV)

    col_sums = np.sum(thresh, axis=0)
    try:
        anchor_x_relative = np.where(col_sums > 300)[0][0]
        scan_x_relative = anchor_x_relative + 12
    except:
        return start_q # ถ้าหาไม่เจอ ให้ส่งเลขข้อเดิมกลับไป

    vertical_line = thresh[:, scan_x_relative]
    question_starts = []
    is_ink = False

    for y, pixel in enumerate(vertical_line):
        if pixel > 0:
            if not is_ink:
                question_starts.append(y + top_limit)
                is_ink = True
        else:
            if is_ink:
                is_ink = False

    final_y = []
    if question_starts:
        last_y = -1000
        for y in question_starts:
            if y - last_y > 150:
                final_y.append(y)
                last_y = y

    real_x = anchor_x_relative + left_limit
    top_buffer = 70
    bottom_padding = 30

    current_q = start_q
    for i, y_start in enumerate(final_y):
        y_box_start = y_start - top_buffer
        if i + 1 < len(final_y):
            y_box_end = final_y[i+1] - top_buffer - 5
        else:
            y_box_end = bottom_limit + bottom_padding

        payload = {
            "year": str(year),
            "subjectName": subject_folder,
            "pageNumber": int(page_num),
            "questionNumber": str(current_q), # ใช้เลขข้อที่รันต่อเนื่อง
            "x": float(real_x - 15),
            "y": float(y_box_start),
            "width": float(w_img - real_x - 20),
            "height": float(y_box_end - y_box_start)
            # ไม่ส่ง correctAnswer เพื่อป้องกันการทับข้อมูลเดิม
        }

        if send_to_nestjs(payload):
            print(f"บันทึกพิกัด: {subject_folder} ข้อ {current_q} (หน้า {page_num})")

        current_q += 1

    return current_q # ส่งเลขข้อถัดไปกลับคืนไป

if not os.path.exists(IMAGE_ROOT):
    print(f"ไม่พบโฟลเดอร์: {IMAGE_ROOT}")
else:
    for subject_folder in os.listdir(IMAGE_ROOT):
        subject_path = os.path.join(IMAGE_ROOT, subject_folder)

        if os.path.isdir(subject_path):
            year_match = re.search(r'\d{4}', subject_folder)
            year = year_match.group() if year_match else "Unknown"

            all_images = [f for f in os.listdir(subject_path) if f.lower().endswith(".png")]
            img_files = sorted(all_images, key=lambda x: int(re.search(r'\d+', x).group() if re.search(r'\d+', x) else 0))

            total_count = len(img_files)

            # เริ่มนับข้อที่ 1 ใหม่ทุกครั้งที่ขึ้นวิชาใหม่
            current_q_count = 1

            for idx, img_file in enumerate(img_files):
                page_match = re.search(r'\d+', img_file)
                page_num = int(page_match.group()) if page_match else (idx + 1)

                # ข้ามหน้าปกและหน้าท้าย
                if page_num <= 2 or idx == total_count - 1:
                    continue

                img_path = os.path.join(subject_path, img_file)
                img_array = np.fromfile(img_path, np.uint8)
                img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

                if img is not None:
                    # อัปเดตเลขข้อสะสมจากการสแกนแต่ละหน้า
                    current_q_count = process_smart_layout_scan(img, page_num, year, subject_folder, current_q_count)