import os
import re
import uuid
import requests
from dotenv import load_dotenv
from supabase import create_client, Client
from playwright.sync_api import sync_playwright

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

NESTJS_API_URL = "http://localhost:3000/exams/library"

def save_to_nestjs(subject_name, cloud_url, year_from_file):
    payload = {
        "subjectName": subject_name.replace(".pdf", ""),
        "pdfUrl": cloud_url,
        "year": year_from_file,
        "source": "ทปอ."
    }
    try:
        response = requests.post(NESTJS_API_URL, json=payload)
        if response.status_code == 201 or response.status_code == 200:
            print(f"บันทึก {subject_name} ลง DB เรียบร้อย")
        else:
            print(f"NestJS ตอบกลับด้วย Error: {response.status_code}")
    except Exception as e:
        print(f"เชื่อมต่อ NestJS ไม่ได้: {e}")

# ตรวจสอบการเชื่อมต่อ Supabase
if not SUPABASE_URL or not SUPABASE_KEY:
    print("ไม่พบค่า SUPABASE_URL หรือ SUPABASE_KEY ใน .env")
    exit()

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def upload_to_supabase(local_filepath, original_filename):
    try:
        safe_filename = f"exam_{uuid.uuid4().hex[:8]}.pdf"

        with open(local_filepath, 'rb') as f:
            supabase.storage.from_('tcas-exam-library').upload(
                path=safe_filename,
                file=f,
                file_options={"content-type": "application/pdf", "x-upsert": "true"}
            )

        file_url = supabase.storage.from_('tcas-exam-library').get_public_url(safe_filename)
        return file_url
    except Exception as e:
        return None

def download_and_sync_tcas():
    base_dir = "tcas_library"
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        url = "https://www.mytcas.com/answers/"
        page.goto(url, wait_until="networkidle")

        links = page.query_selector_all('a[href$=".pdf"]')

        for link in links:
            href = link.get_attribute('href')
            text = link.inner_text().strip()

            year_match = re.search(r'\d{4}', text)
            found_year = year_match.group(0) if year_match else "ไม่ระบุปี"

            clean_name = re.sub(r'[\\/*?:"<>|]', '', text)
            if not clean_name: clean_name = href.split('/')[-1]
            if not clean_name.endswith('.pdf'): clean_name += ".pdf"

            filepath = os.path.join(base_dir, clean_name)
            full_url = href if href.startswith('http') else f"https://www.mytcas.com{href}"

            # ดาวน์โหลดลงเครื่องก่อน (ถ้ายังไม่มี)
            if not os.path.exists(filepath):
                try:
                    res = requests.get(full_url, timeout=30)
                    with open(filepath, 'wb') as f:
                        f.write(res.content)
                except Exception as e:
                    print(f"โหลดไม่สำเร็จ: {e}")
                    continue

            cloud_url = upload_to_supabase(filepath, clean_name)

            if cloud_url:
                save_to_nestjs(clean_name, cloud_url, found_year)
            else:
                print(f"อัปโหลดไม่สำเร็จสำหรับไฟล์นี้")

        browser.close()
if __name__ == "__main__":
    download_and_sync_tcas()