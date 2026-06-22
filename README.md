## 🐍 Python Data Pipeline (TCAS Statistics)

ส่วนของสคริปต์ Python สำหรับประมวลผลข้อมูลสถิติคะแนนย้อนหลัง (2564 - 2568) เพื่อนำเข้าสู่ Database ของระบบ TCAS Assist

### 🌟 Key Features

- **Dynamic Column Mapping**: รองรับไฟล์ Excel จาก ทปอ. ที่มีชื่อคอลัมน์ต่างกันในแต่ละปี (เช่น 'รหัสหลักสูตร' vs 'รหัสคณะ')
- **Data Cleaning**: จัดการ Merge Cells, ตัดรหัสหลักสูตรเหลือ 14 หลักมาตรฐาน และแปลงข้อมูลค่าว่าง (NaN) ให้ถูกต้องตาม Data Type
- **Database Integration**: เชื่อมต่อโดยตรงกับ PostgreSQL ผ่าน SQLAlchemy โดยอ้างอิง Schema เดียวกับ NestJS Entity
- **Idempotent Process**: ระบบล้างข้อมูลเก่า (Truncate) อัตโนมัติก่อนเริ่มงานใหม่ เพื่อป้องกันข้อมูลซ้ำซ้อน

### 🛠️ Tech Stack

- **Python 3.12+**
- **Pandas & Openpyxl**: สำหรับการทำ Data Manipulation
- **SQLAlchemy & Psycopg2**: ตัวเชื่อมต่อ Database ประสิทธิภาพสูง

### 🚀 How to Run

1. ติดตั้ง Library ที่จำเป็น:

   ```bash
   pip install -r requirements.txt

   ## AI-Powered Automation & Extraction
   ```

### ⚙️ Automation Workflow

1. **Web Scraper (Playwright)**: บอท `js_striker` จะทำหน้าที่จำลองการคลิกหน้าเว็บ mytcas เพื่อกางข้อมูลเกณฑ์การรับรอบ 3 (Admission) และบันทึกข้อความดิบ (Raw Text) ลงในเครื่อง
2. **AI Intelligence (Gemini 2.0 Flash)**: ใช้ Gemini AI ในการอ่านข้อความดิบเพื่อแกะข้อมูลที่ซับซ้อน เช่น ค่าน้ำหนักคะแนน (Weights), คะแนนขั้นต่ำ (Min Requirements) และข้อมูลคณะ/สาขา
3. **Smart Sync Manager**: ระบบจะทำการ Mapping ข้อมูลที่ AI แกะได้เข้ากับฐานข้อมูล PostgreSQL โดยอัตโนมัติ หากพบมหาวิทยาลัยใหม่ ระบบจะสร้างข้อมูลให้อัตโนมัติ (On-the-fly Creation)
4. **Resilience & Rate Limiting**: มีระบบข้ามไฟล์ที่โหลดแล้ว (Resume) และระบบจัดการ Quota ของ AI (Auto-retry 429 Error) เพื่อให้รันงานต่อเนื่องได้หลายพันรายการ

### 🛠️ Tech Stack (Automation)

- **Playwright**: สำหรับควบคุม Browser แบบไร้หน้าจอ (Headless)
- **Google Generative AI (Gemini API)**: สมองกลในการวิเคราะห์และจัดกลุ่มข้อมูล
- **Psycopg2 (Extras)**: จัดการข้อมูล JSONB และการทำ Upsert (ON CONFLICT) ใน PostgreSQL

**AI Risk**: เปิดระบบคำนวณโอกาสความเสี่ยงจากคะแนน

```bash
uvicorn scripts.stats_analysis.analyze_risk_no_avg:app --reload --port 8000
```

### จัดการส่วนข้อสอบ

**cloud_upload.py** : scraping ข้อสอบจากหน้าเว็บทปอ ยิง ไฟล์ข้อสอบขึ้น Supabase + เซฟข้อมูลลง local dbs
**scraping_answer.py** : ดึงข้อมูลจากหน้าเว็บ ทปอ มาเป็น pdf ในเครื่อง
**scraping_pdf.py** : ตัด pdf แยกมาเป็นไฟล์รูปเก็บใน folder (กรณีมีไฟล์ pdf โหลดเข้ามาของ ทปอ)
**converter.py** : ตัด pdf แยกมาเป็นไฟล์รูปเก็บใน folder (ต่อกับหลังบ้านกรณีผู้ใช้ import file)
**auto_coords.py** : ใช้ Pixel-level Analysis ตัดภาพโจทย์ auto ใช้ OpenCV จัดการภาพ + ใช้ NumPy จัดการระบุพิกัด (ใช้ได้แค่รูปแบบข้อสอบของ ทปอ)
**extract_answer_table.py** : ดึงคำตอบเฉลยด้วย Pixel-level Analysis

### จัดการส่วนเกณฑ์คะแนนและสถิติ

**uni_scraper.py** : scraping หน้าเว็บทปอ ดึงรหัสสาขาจากทุกคณะของ 20 มหาวิทยาลัยลงไฟล์ mega_unis_links.txt
**save.py** : ดึงข้อมูลเกณฑ์และคะแนนย้อนหลังของรอบที่ 3 (Admission) จากหน้าเว็บ ทปอ อ้างอิงจากรหัสใน mega_unis_links.txt สร้างเป็นไฟล์ ตามรหัสสาขา ตัวอย่าง unlocked_score_10240125110101A.txt
**process_criteria.py** : จัดคิว อ่านไฟล์ แล้วยิงต่อหา main_sync
**main_sync.py** : Gemini AI clean data ส่งหา sync_manager.py
**sync_manager.py** : รับข้อมูลที่สะอาดแล้ว ยิงขึ้น database

**process_stats.py** : อ่าน xlsx สถิติเก่า clean แล้วยิงขึ้น database
**analyze_risk_no_avg.py** : คำนวณโอกาสติดด้วย Z-score

---
