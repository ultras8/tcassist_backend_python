import asyncio
import re
import os
from playwright.async_api import async_playwright

async def mega_university_scanner_v3_fixed():
    target_unis = [
        "001", "002", "003", "004", "005", "006", "007", "008", "009", "010",
        "011", "012", "013", "014", "015", "016", "017", "018", "019", "020"
    ]

    filename = "mega_unis_links.txt"

    # อ่านข้อมูลเก่าที่มีในไฟล์ขึ้นมาจำไว้ก่อน
    existing_links = set()
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            existing_links = set(line.strip() for line in f if line.strip())

    print(f"ตรวจพบข้อมูลเดิมในไฟล์: {len(existing_links)} ลิ้งก์")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        for uni_id in target_unis:
            all_program_urls = set() # เก็บเฉพาะของรอบนี้
            try:
                print(f"มหาลัย: {uni_id}")
                await page.goto(f"https://course.mytcas.com/universities/{uni_id}", wait_until="domcontentloaded")
                await asyncio.sleep(2)

                # ล่าลิ้งก์คณะ
                faculty_links = [f"https://course.mytcas.com{await a.get_attribute('href')}" 
                                 for a in await page.query_selector_all('a[href*="/faculties/"]')]

                for f_url in faculty_links:
                    print(f"สแกนคณะ: {f_url.split('/')[-1]}")
                    await page.goto(f_url, wait_until="domcontentloaded")

                    field_links = [f"https://course.mytcas.com{await a.get_attribute('href')}" 
                                   for a in await page.query_selector_all('a[href*="/fields/"]')]

                    targets_to_scan = field_links if field_links else [f_url]

                    for target_url in targets_to_scan:
                        try:
                            if target_url != f_url:
                                await page.goto(target_url, wait_until="domcontentloaded")

                            await asyncio.sleep(1)
                            content = await page.content()
                            found_codes = re.findall(r'/programs/([0-9A-Z]{15})', content)

                            if not found_codes:
                                found_codes = re.findall(r'\b\d{14}[0-9A-Z]\b', content)

                            for code in found_codes:
                                full_url = f"https://course.mytcas.com/programs/{code}"
                                # เช็คว่าลิ้งก์นี้ไม่อยู่ในของเก่า และ ของใหม่ที่เพิ่งเจอ
                                if full_url not in existing_links and full_url not in all_program_urls:
                                    all_program_urls.add(full_url)
                        except:
                            continue

                # บันทึกผลเฉพาะของใหม่ ต่อท้ายไฟล์ (Append)
                if all_program_urls:
                    new_links_list = sorted(list(all_program_urls))
                    with open(filename, "a", encoding="utf-8") as f:
                        for link in new_links_list:
                            f.write(f"{link}\n")

                    # อัปเดต existing_links เพื่อกันซ้ำในมหาลัยถัดไปด้วย
                    existing_links.update(all_program_urls)
                    print(f"จบมหาลัย {uni_id} เซฟเพิ่มใหม่: {len(all_program_urls)} ลิ้งก์")
                else:
                    print(f"จบมหาลัย {uni_id} (ไม่พบลิ้งก์ใหม่ที่ยังไม่มีในไฟล์)")

            except Exception as e:
                print(f"มหาลัย {uni_id} ขัดข้อง: {e}")

        await browser.close()
        print(f"ยอดรวมในไฟล์ตอนนี้คือ: {len(existing_links)} ลิ้งก์")

if __name__ == "__main__":
    asyncio.run(mega_university_scanner_v3_fixed())
