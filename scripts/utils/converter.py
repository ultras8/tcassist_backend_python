from flask import Flask, request, jsonify
from pdf2image import convert_from_path
import os

app = Flask(__name__)

POPPLER_PATH = r'C:\poppler\bin\Library\bin'

@app.route('/convert-local', methods=['POST'])
def convert_pdf_to_png():
    data = request.json
    raw_file_path = data.get('filePath')
    raw_output_dir = data.get('outputDir')

    file_path = os.path.normpath(raw_file_path) if raw_file_path else None
    output_dir = os.path.normpath(raw_output_dir) if raw_output_dir else None

    # print(f"Python ได้รับคำสั่งให้หาไฟล์ที่: {file_path}")
    # print(f"และจะส่งรูปไปที่: {output_dir}")

    if not file_path:
        return jsonify({"error": "filePath is missing"}), 400

    if not os.path.exists(file_path):
        print(f"หาไฟล์ไม่เจอที่พาธ: {os.path.abspath(file_path)}")
        return jsonify({"error": f"File not found at {file_path}"}), 404

    try:
        # แปลงไฟล์
        images = convert_from_path(
            file_path,
            dpi=200,
            poppler_path=POPPLER_PATH
        )

        # สร้างโฟลเดอร์ปลายทางถ้ายังไม่มี
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        for i, image in enumerate(images):
            page_num = i + 1
            image_name = f"page_{page_num}.png"
            image.save(os.path.join(output_dir, image_name), "PNG")

        print(f"แปลงไฟล์สำเร็จ ทั้งหมด {len(images)} หน้า")
        return jsonify({
            "status": "success",
            "pages": len(images),
            "message": "Images generated in the folder"
        })

    except Exception as e:
        print(f"เกิดข้อผิดพลาดฝั่ง Python: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000, debug=True) # เปิด debug=True เพื่อดู Error ละเอียดๆ ใน Terminal