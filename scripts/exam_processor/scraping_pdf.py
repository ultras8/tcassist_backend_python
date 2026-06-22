# ตัด pdf แยกมาเป็นไฟล์รูปเก็บใน folder
import fitz  # PyMuPDF
import os

def process_all_pdfs(input_folder="tcas_library", output_base_folder="extracted_exams"):
    if not os.path.exists(input_folder):
        print(f"ไม่พบโฟลเดอร์: {input_folder}")
        return

    # ดึงรายชื่อไฟล์ทั้งหมดในโฟลเดอร์ที่เป็น .pdf
    pdf_files = [f for f in os.listdir(input_folder) if f.endswith('.pdf')]

    if not pdf_files:
        print(f"ไม่มีไฟล์ PDF ในโฟลเดอร์ {input_folder}")
        return

    for pdf_filename in pdf_files:
        pdf_path = os.path.join(input_folder, pdf_filename)

        # สร้างโฟลเดอร์ย่อยตามชื่อวิชา (ตัด .pdf ออก)
        raw_name = os.path.splitext(pdf_filename)[0].strip()
        exam_name = raw_name.replace(" ", "_")
        output_folder = os.path.join(output_base_folder, exam_name)

        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        try:
            doc = fitz.open(pdf_path)

            for page_index in range(len(doc)):
                page = doc.load_page(page_index)
                # ความชัด 3.0
                pix = page.get_pixmap(matrix=fitz.Matrix(3.0, 3.0))

                image_name = f"page_{page_index + 1}.png"
                image_path = os.path.join(output_folder, image_name)
                pix.save(image_path)

            doc.close()
            print(f"บันทึกรูปภาพเรียบร้อยที่: {output_folder}")

        except Exception as e:
            print(f"เกิดข้อผิดพลาดกับไฟล์ {pdf_filename}: {str(e)}")
process_all_pdfs()