import base64
import io
import json
import os
import zipfile
from datetime import datetime

import pandas as pd
import streamlit as st
from flask_app import FEE_ITEMS, fill_receipt_rows, generate_receipt_pdf, load_fee_config, save_fee_config

LOGO_PATH = os.path.join(os.path.dirname(__file__), "static", "nfsu_logo.png")
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "fee_config.json")

SCHOOL_PROGRAMS = {
    "SCSDF": ["MSc CS", "MSC", "DFIS", "MTech AIDS (SP. Cyber Security)"],
    "FS": ["MSc FS", "BSc-MSc Forensic Sciences"],
}

MODES = ["Cash", "Cheque", "D.D.", "UPI", "Card"]


def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_config(config):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def format_preview_rows(rows):
    return [
        {
            "Receipt Date": row.get("Receipt Date", ""),
            "Received From": row.get("Received From", ""),
            "Program": row.get("Course", ""),
            "Mode": row.get("Payment Method", ""),
            "Semester": row.get("Semester", ""),
            "Amount": f"{row.get('Amount (INR)', 0):,.2f}",
        }
        for row in rows
    ]


def build_zip(receipts):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for receipt_number, row in receipts:
            pdf_buffer = generate_receipt_pdf(row, receipt_number, LOGO_PATH)
            zf.writestr(f"receipt_{receipt_number}.pdf", pdf_buffer.getvalue())
    buffer.seek(0)
    return buffer


def build_pdf(receipt):
    buffer = generate_receipt_pdf(receipt[1], receipt[0], LOGO_PATH)
    return buffer.getvalue()


def main():
    st.set_page_config(page_title="NFSU Fee Receipt Generator", layout="wide")
    st.title("NFSU Fee Receipt Generator")
    st.markdown("Upload an Excel file, preview receipts, and download PDF receipts.")

    with st.sidebar:
        st.header("Configure Upload")
        school = st.selectbox("School", ["", "SCSDF", "FS"])
        program = st.selectbox("Program", [""] + SCHOOL_PROGRAMS.get(school, []))
        semester = st.selectbox("Semester", [""] + [str(i) for i in range(1, 11)])
        mode = st.selectbox("Payment Mode", [""] + MODES)
        st.markdown("---")
        st.write("If your Excel already contains Program/Mode/Semester, these selections will override them.")

    uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx", "xls"])
    if uploaded_file is not None:
        try:
            df = pd.read_excel(uploaded_file)
        except Exception as exc:
            st.error(f"Could not read Excel file: {exc}")
            return

        required = ["Receipt Date", "Received From"]
        missing = [col for col in required if col not in df.columns]
        if missing:
            st.error(f"Missing required columns: {', '.join(missing)}")
            return

        receipt_rows = fill_receipt_rows(
            df,
            school_override=school,
            program_override=program,
            semester_override=semester,
            mode_override=mode,
        )

        if not receipt_rows:
            st.warning("No receipts could be generated from the file.")
            return

        preview = format_preview_rows(receipt_rows)
        st.subheader("Receipt Preview")
        st.dataframe(preview)

        first_preview_pdf = build_pdf(("PREVIEW", receipt_rows[0]))
        st.download_button(
            label="Download sample receipt PDF",
            data=first_preview_pdf,
            file_name="receipt_preview.pdf",
            mime="application/pdf",
        )

        if len(receipt_rows) == 1:
            pdf_bytes = build_pdf(("RCPT-1", receipt_rows[0]))
            st.download_button(
                label="Download receipt PDF",
                data=pdf_bytes,
                file_name="receipt_1.pdf",
                mime="application/pdf",
            )
        else:
            receipts = []
            now = datetime.now().strftime("%Y%m%d%H%M%S")
            for idx, row in enumerate(receipt_rows, start=1):
                receipts.append((f"RCPT-{now}-{idx:03d}", row))
            zip_buffer = build_zip(receipts)
            st.download_button(
                label="Download all receipts as ZIP",
                data=zip_buffer,
                file_name="fee_receipts.zip",
                mime="application/zip",
            )

    st.sidebar.markdown("---")
    st.sidebar.write("Need admin fee presets? Use the Flask admin route at /admin or edit fee_config.json directly.")


if __name__ == "__main__":
    main()
