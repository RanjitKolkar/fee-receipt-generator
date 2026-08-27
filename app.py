import base64
import io
import json
import os
import zipfile
from datetime import datetime

import pandas as pd
from flask import Flask, flash, redirect, render_template, request, send_file, url_for
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

app = Flask(__name__)
app.secret_key = "change-me-for-production"
CONFIG_PATH = os.path.join(app.root_path, "fee_config.json")

REQUIRED_COLUMNS = [
    "Receipt Date",
    "Received From",
]

FEE_ITEMS = [
    "Tuition Fees",
    "Library Fee",
    "Caution Money Including Library (Refundable)",
    "Registration Fee",
    "Enrollment Fee",
    "Computer Fees with internet facility (Per Semester)",
    "Semester Examination Fee",
    "Semester end Examination Transcript Fee",
    "Orientation Programme Fee",
    "Identity Card Fee",
    "Laboratory Fee",
    "Eligibility Certificate Fees",
    "Convocation Fee",
    "Student Activity Fee",
]

DEFAULT_FEE_CONFIG = {
    "default": {
        "School Name": "National Forensic Sciences University",
        "On Account Of": "Course Fees",
        **{item: 0 for item in FEE_ITEMS},
    },
    "B.Sc. Forensic Science": {
        "I": {
            "School Name": "NFSU",
            "On Account Of": "Course Fees",
            "Tuition Fees": 15000,
            "Library Fee": 1500,
            "Caution Money Including Library (Refundable)": 2000,
            "Registration Fee": 500,
            "Enrollment Fee": 500,
            "Computer Fees with internet facility (Per Semester)": 1500,
            "Semester Examination Fee": 800,
            "Semester end Examination Transcript Fee": 300,
            "Orientation Programme Fee": 250,
            "Identity Card Fee": 400,
            "Laboratory Fee": 350,
            "Eligibility Certificate Fees": 200,
            "Convocation Fee": 200,
            "Student Activity Fee": 150,
        }
    },
}


def ensure_fee_config():
    if not os.path.exists(CONFIG_PATH):
        save_fee_config(DEFAULT_FEE_CONFIG)


def load_fee_config():
    ensure_fee_config()
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_fee_config(config):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def get_fee_data(program, semester):
    config = load_fee_config()
    program_config = config.get(program, {})
    if semester and semester in program_config:
        return {**config.get("default", {}), **program_config[semester]}
    return config.get(program, {}).get("default", config.get("default", {}))


def number_to_words(num):
    num = int(round(num))
    if num == 0:
        return "Zero"

    units = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"]
    teens = ["Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
    tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]

    def one(n):
        return units[n]

    def two(n):
        if n < 10:
            return one(n)
        if n < 20:
            return teens[n - 10]
        ten = n // 10
        rest = n % 10
        return tens[ten] + (" " + units[rest] if rest else "")

    def three(n):
        hundred = n // 100
        rest = n % 100
        if hundred and rest:
            return units[hundred] + " Hundred " + two(rest)
        if hundred:
            return units[hundred] + " Hundred"
        return two(rest)

    billions = num // 1_000_000_000
    millions = (num // 1_000_000) % 1000
    thousands = (num // 1000) % 1000
    remainder = num % 1000

    parts = []
    if billions:
        parts.append(three(billions) + " Billion")
    if millions:
        parts.append(three(millions) + " Million")
    if thousands:
        parts.append(three(thousands) + " Thousand")
    if remainder:
        parts.append(three(remainder))

    return " ".join(parts)


def fill_receipt_rows(df, school_override="", program_override="", semester_override="", mode_override=""):
    rows = []
    for _, raw in df.iterrows():
        program = program_override or str(raw.get("Program", "")).strip()
        semester = semester_override or str(raw.get("Semester", "")).strip()
        mode = mode_override or str(raw.get("Mode", "")).strip()
        school_name = school_override or str(raw.get("School Name", "")).strip()

        if not program or not semester:
            # if the row or form does not provide program/semester, use defaults from row if present
            program = str(raw.get("Program", "")).strip()
            semester = str(raw.get("Semester", "")).strip()

        if not school_name:
            school_name = "NFSU"

        fee_data = get_fee_data(program, semester)
        row_data = {
            "Receipt Date": str(raw.get("Receipt Date", "")),
            "Received From": str(raw.get("Received From", "")),
            "Course": program,
            "Program": program,
            "Semester": semester,
            "School Name": school_name or fee_data.get("School Name", "NFSU"),
            "Payment Method": mode,
            "On Account Of": fee_data.get("On Account Of", "Course Fees"),
        }
        total = 0.0
        for item in FEE_ITEMS:
            value = fee_data.get(item, 0)
            try:
                amount = float(value)
            except (TypeError, ValueError):
                amount = 0.0
            row_data[item] = amount
            total += amount

        row_data["Amount (INR)"] = total
        row_data["Amount in Words"] = number_to_words(total) + " only"
        rows.append(row_data)
    return rows


def generate_receipt_pdf(row, receipt_number, logo_path):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    margin = 18 * mm

    if os.path.exists(logo_path):
        try:
            logo_width = 70 * mm
            logo_height = 28 * mm
            logo_x = (width - logo_width) / 2
            logo_y = height - margin - logo_height
            c.drawImage(logo_path, logo_x, logo_y, width=logo_width, height=logo_height, preserveAspectRatio=True, mask='auto')
            header_top = logo_y - 8 * mm
        except Exception:
            header_top = height - margin - 10 * mm
    else:
        header_top = height - margin - 10 * mm

    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(width / 2, header_top, "National Forensic Sciences University")
    c.drawCentredString(width / 2, header_top - 5 * mm, "Goa Campus")
    c.setFont("Helvetica", 10)
    c.drawCentredString(width / 2, header_top - 10 * mm, "Near Goa Dairy, Ponda – 403 401, Goa – India.")

    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2, header_top - 20 * mm, "COURSE FEES RECEIPT")

    c.setFont("Helvetica", 10)
    c.drawRightString(width - margin, header_top - 14 * mm, f"Receipt No.: {receipt_number}")
    c.drawRightString(width - margin, header_top - 20 * mm, f"Date: {row.get('Receipt Date', '')}")

    c.setStrokeColor(colors.black)
    c.setLineWidth(0.4)
    c.line(margin, header_top - 22 * mm, width - margin, header_top - 22 * mm)

    y = header_top - 30 * mm
    c.setFont("Helvetica", 10)

    c.drawString(margin, y, "Received From:")
    line_start = margin + 35 * mm
    c.line(line_start, y - 1 * mm, width - margin, y - 1 * mm)
    c.drawString(line_start + 2 * mm, y, row.get("Received From", ""))

    y -= 9 * mm
    c.drawString(margin, y, "Rs.")
    c.line(margin + 12 * mm, y - 1 * mm, margin + 78 * mm, y - 1 * mm)
    c.drawString(margin + 14 * mm, y, f"{row.get('Amount (INR)', 0):,.2f}")

    y -= 9 * mm
    c.drawString(margin, y, "(in words)")
    c.line(margin + 20 * mm, y - 1 * mm, width - margin, y - 1 * mm)
    c.drawString(margin + 22 * mm, y, row.get("Amount in Words", ""))

    y -= 9 * mm
    c.drawString(margin, y, "By:")
    c.line(margin + 10 * mm, y - 1 * mm, margin + 50 * mm, y - 1 * mm)
    c.drawString(margin + 12 * mm, y, row.get("Payment Method", ""))

    y -= 9 * mm
    c.drawString(margin, y, "on account of fees as under for")
    sem_start = margin + 55 * mm
    c.line(sem_start, y - 1 * mm, sem_start + 10 * mm, y - 1 * mm)
    c.drawString(sem_start + 2 * mm, y, row.get("Semester", ""))
    c.drawString(sem_start + 15 * mm, y, "semester for the course of")
    course_start = sem_start + 72 * mm
    c.line(course_start, y - 1 * mm, width - margin, y - 1 * mm)
    c.drawString(course_start + 2 * mm, y, row.get("Course", ""))

    y -= 9 * mm
    c.drawString(margin, y, "Name of the School:")
    c.line(margin + 35 * mm, y - 1 * mm, width - margin, y - 1 * mm)
    c.drawString(margin + 37 * mm, y, row.get("School Name", ""))

    y -= 14 * mm
    row_height = 8 * mm
    table_left = margin
    table_right = width - margin
    col1_width = 16 * mm
    col3_width = 36 * mm
    col1_right = table_left + col1_width
    col2_left = col1_right + 4 * mm
    col3_left = table_right - col3_width
    table_top = y

    row_count = len(FEE_ITEMS) + 2
    table_bottom = table_top - row_count * row_height

    c.setFillColor(colors.HexColor("#f3f4f6"))
    c.rect(table_left, table_top - row_height, table_right - table_left, row_height, fill=1, stroke=0)
    c.setFillColor(colors.black)
    c.setLineWidth(0.4)
    c.rect(table_left, table_bottom, table_right - table_left, table_top - table_bottom, stroke=1, fill=0)

    for i in range(1, row_count):
        y_line = table_top - i * row_height
        c.line(table_left, y_line, table_right, y_line)
    c.line(col1_right, table_top, col1_right, table_bottom)
    c.line(col3_left, table_top, col3_left, table_bottom)

    header_text_y = table_top - row_height / 2 + 1 * mm
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString((table_left + col1_right) / 2, header_text_y, "Sr. No.")
    c.drawString(col2_left, header_text_y, "Particulars")
    c.drawRightString(table_right - 2 * mm, header_text_y, "Amount Rs.")

    y = table_top - row_height - row_height / 2 + 1 * mm
    total_amount = 0.0
    c.setFont("Helvetica", 10)
    for index, item in enumerate(FEE_ITEMS, start=1):
        amount_value_num = float(row.get(item, 0) or 0)
        total_amount += amount_value_num

        c.drawCentredString((table_left + col1_right) / 2, y, str(index))
        c.drawString(col2_left, y, item)
        c.drawRightString(table_right - 2 * mm, y, f"{amount_value_num:,.2f}" if amount_value_num else "")
        y -= row_height

    total_y = table_bottom + row_height / 2 + 1 * mm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(col2_left, total_y, "TOTAL")
    c.drawRightString(table_right - 2 * mm, total_y, f"{total_amount:,.2f}")

    y -= 14 * mm
    c.setFont("Helvetica", 9)
    c.drawString(margin, y, "Subject to realisation of cheque")
    y -= 6 * mm
    c.drawString(margin, y, "Out station cheques will not be accepted.")

    y -= 14 * mm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin, y, "Executive Registrar")
    c.drawString(width - margin - 40 * mm, y, "Cashier")

    c.save()
    buffer.seek(0)
    return buffer


def build_preview_data(rows):
    preview_list = []
    for row in rows:
        preview_list.append({
            "Receipt Date": row.get("Receipt Date", ""),
            "Received From": row.get("Received From", ""),
            "Program": row.get("Course", ""),
            "Mode": row.get("Payment Method", ""),
            "Semester": row.get("Semester", ""),
            "Amount": f"{row.get('Amount (INR)', 0):,.2f}",
        })
    return preview_list


@app.route("/", methods=["GET", "POST"])
def upload():
    ensure_fee_config()
    if request.method == "POST":
        file = request.files.get("excel_file")
        if not file or file.filename == "":
            flash("Please upload an Excel file.", "danger")
            return redirect(url_for("upload"))

        try:
            df = pd.read_excel(file)
        except Exception as exc:
            flash(f"Could not read Excel file: {exc}", "danger")
            return redirect(url_for("upload"))

        school = request.form.get("school", "").strip()
        program = request.form.get("program", "").strip()
        semester = request.form.get("semester", "").strip()
        mode = request.form.get("mode", "").strip()

        missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        if missing:
            flash(f"Missing required columns: {', '.join(missing)}", "danger")
            return redirect(url_for("upload"))

        receipt_rows = fill_receipt_rows(df, school_override=school, program_override=program, semester_override=semester, mode_override=mode)
        if not receipt_rows:
            flash("No data available in the uploaded file.", "danger")
            return redirect(url_for("upload"))

        rows_json = base64.b64encode(json.dumps(receipt_rows).encode("utf-8")).decode("ascii")
        preview_pdf = None
        if receipt_rows:
            preview_buffer = generate_receipt_pdf(receipt_rows[0], "PREVIEW", os.path.join(app.root_path, "static", "nfsu_logo.png"))
            preview_pdf = base64.b64encode(preview_buffer.getvalue()).decode("ascii")

        return render_template(
            "index.html",
            required_columns=REQUIRED_COLUMNS,
            preview_rows=build_preview_data(receipt_rows),
            preview_pdf=preview_pdf,
            rows_json=rows_json,
            receipt_count=len(receipt_rows),
        )

    return render_template("index.html", required_columns=REQUIRED_COLUMNS)


@app.route("/generate", methods=["POST"])
def generate():
    rows_json = request.form.get("rows_json")
    if not rows_json:
        flash("Unable to generate receipts. Please upload the Excel file again.", "danger")
        return redirect(url_for("upload"))

    try:
        receipt_rows = json.loads(base64.b64decode(rows_json.encode("ascii")).decode("utf-8"))
    except Exception as exc:
        flash(f"Invalid receipt data: {exc}", "danger")
        return redirect(url_for("upload"))

    now = datetime.now().strftime("%Y%m%d%H%M%S")
    logo_path = os.path.join(app.root_path, "static", "nfsu_logo.png")
    receipts = []

    for index, row_data in enumerate(receipt_rows, start=1):
        receipt_number = f"RCPT-{now}-{index:03d}"
        receipts.append((receipt_number, row_data))

    if len(receipts) == 1:
        receipt_number, row_data = receipts[0]
        pdf_buffer = generate_receipt_pdf(row_data, receipt_number, logo_path)
        return send_file(
            pdf_buffer,
            download_name=f"receipt_{receipt_number}.pdf",
            as_attachment=True,
            mimetype="application/pdf",
        )

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for receipt_number, row_data in receipts:
            pdf_buffer = generate_receipt_pdf(row_data, receipt_number, logo_path)
            zf.writestr(f"receipt_{receipt_number}.pdf", pdf_buffer.getvalue())

    zip_buffer.seek(0)
    return send_file(
        zip_buffer,
        download_name=f"fee_receipts_{now}.zip",
        as_attachment=True,
        mimetype="application/zip",
    )


@app.route("/admin", methods=["GET", "POST"])
def admin():
    ensure_fee_config()
    fee_config = load_fee_config()
    programs = [key for key in fee_config.keys() if key != "default"]
    selected_program = None
    selected_semester = None
    selected_values = {}

    if request.method == "POST":
        selected_program = request.form.get("program", "").strip()
        selected_semester = request.form.get("semester", "").strip()
        school_name = request.form.get("school_name", "NFSU").strip()
        on_account = request.form.get("on_account_of", "Course Fees").strip()
        if not selected_program or not selected_semester:
            flash("Program and semester are required.", "danger")
            return redirect(url_for("admin"))

        program_section = fee_config.setdefault(selected_program, {})
        section = {"School Name": school_name, "On Account Of": on_account}
        for item in FEE_ITEMS:
            raw_value = request.form.get(item, "0")
            try:
                section[item] = float(raw_value or 0)
            except ValueError:
                section[item] = 0.0
        program_section[selected_semester] = section
        save_fee_config(fee_config)
        flash(f"Saved fees for {selected_program} / {selected_semester}.", "success")
        return redirect(url_for("admin"))

    return render_template(
        "admin.html",
        fee_config=fee_config,
        programs=programs,
        fee_items=FEE_ITEMS,
    )


if __name__ == "__main__":
    app.run(debug=True)
