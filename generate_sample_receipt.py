from app import generate_receipt_pdf

sample_row = {
    "Receipt Date": "2026-08-27",
    "Received From": "Aarav Kumar",
    "Amount (INR)": 22500,
    "Amount in Words": "Twenty two thousand five hundred only",
    "Payment Method": "Cash",
    "On Account Of": "Course Fees",
    "Semester": "II",
    "Course": "B.Sc. Forensic Science",
    "School Name": "NFSU",
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

buffer = generate_receipt_pdf(sample_row, "243", "static/nfsu_logo.png")
with open("sample_receipt_output.pdf", "wb") as f:
    f.write(buffer.getvalue())

print("Created sample_receipt_output.pdf")
