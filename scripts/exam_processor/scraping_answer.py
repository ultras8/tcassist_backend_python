# ดึงข้อมูลจากหน้าเว็บ ทปอ มาเป็น pdf ในเครื่อง
from playwright.sync_api import sync_playwright
import os
import requests
import re

def download_all_tcas_pdfs():
    base_dir = "tcas_library"
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        url = "https://www.mytcas.com/answers/"
        print(f"กำลังเข้าสู่คลังข้อสอบ: {url}...")

        try:
            page.goto(url, wait_until="networkidle")

            # ค้นหาลิงก์ PDF ทั้งหมด
            links = page.query_selector_all('a[href$=".pdf"]')
            print(f"พบไฟล์ PDF ทั้งหมด {len(links)} ไฟล์")

            for link in links:
                href = link.get_attribute('href')
                text = link.inner_text().strip()

                # ทำความสะอาดชื่อไฟล์: เอาตัวอักษรพิเศษออกเพื่อให้เซฟเป็นชื่อไฟล์ได้
                clean_name = re.sub(r'[\\/*?:"<>|]', '', text)
                if not clean_name: clean_name = href.split('/')[-1]

                full_url = href if href.startswith('http') else f"https://www.mytcas.com{href}"
                filepath = os.path.join(base_dir, f"{clean_name}.pdf")

                # ตรวจสอบว่าถ้ามีไฟล์เดิมอยู่แล้ว ไม่ต้องโหลดซ้ำ
                if os.path.exists(filepath):
                    print(f"ข้าม: {clean_name} (มีไฟล์อยู่แล้ว)")
                    continue

                print(f"กำลังดาวน์โหลด: {clean_name}...")
                try:
                    res = requests.get(full_url, timeout=30)
                    with open(filepath, 'wb') as f:
                        f.write(res.content)
                    print(f"สำเร็จ")
                except Exception as e:
                    print(f"โหลดไม่สำเร็จ: {clean_name} ({e})")

        finally:
            browser.close()
            print(f"\nดาวน์โหลดเสร็จสิ้น ไฟล์ทั้งหมดถูกเก็บไว้ที่โฟลเดอร์: {base_dir}")

# รันเพื่อดึงทุกวิชามาลงเครื่อง
download_all_tcas_pdfs()