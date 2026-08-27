# Fee Receipt Generator

A simple Flask web application that accepts an Excel upload and generates fee receipts in PDF format.

## Features

- Excel template support with required columns
- Automatic receipt number generation
- PDF receipt creation using a formatted layout and logo
- Download a ZIP file when multiple receipts are generated

## Setup

1. Create a Python virtual environment:

```bash
python -m venv venv
```

2. Activate the environment:

```bash
venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Generate sample Excel files:

```bash
python generate_sample_excel.py
```

5. Run the app:

```bash
python app.py
```

6. Open the browser at `http://127.0.0.1:5000`

## Usage

- Upload `receipt_sample_data.xlsx` or your own Excel file matching the template columns.
- Use the admin page at `/admin` to prefill fee structures for specific Program and Semester combinations.
- The app generates one PDF per row, using Excel-provided student details and admin-prefilled fee data.
- If multiple receipts are created, they are downloaded as a ZIP file.
