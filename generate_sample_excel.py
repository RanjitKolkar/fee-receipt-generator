from openpyxl import Workbook

columns = [
    "Receipt Date",
    "Received From",
    "Program",
    "Mode",
    "Semester",
]

sample_rows = [
    ["2026-08-27", "Aarav Kumar", "B.Sc. Forensic Science", "Cash", "I"],
    ["2026-08-27", "Mira Sharma", "B.Sc. Forensic Science", "Cheque", "I"],
    ["2026-08-27", "Rohan Patel", "B.Sc. Forensic Science", "Cash", "II"],
]

wb = Workbook()
ws = wb.active
ws.title = "Template"
ws.append(columns)
wb.save("receipt_template.xlsx")

wb2 = Workbook()
ws2 = wb2.active
ws2.title = "Sample Data"
ws2.append(columns)
for row in sample_rows:
    ws2.append(row)
wb2.save("receipt_sample_data.xlsx")

print("Created receipt_template.xlsx and receipt_sample_data.xlsx")
