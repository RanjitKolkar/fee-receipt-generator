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

5. Run the Streamlit app:

```bash
streamlit run streamlit_app.py
```

6. Open the browser at the link shown by Streamlit, usually `http://localhost:8501`

## Usage

- Upload `receipt_sample_data.xlsx` or your own Excel file with columns `Receipt Date` and `Received From`.
- Choose School, Program, Semester, and Payment Mode before upload.
- Preview generated receipts in the app.
- Download a single PDF or ZIP of all receipts.
- For advanced fee presets, use the Flask admin route at `/admin` or edit `fee_config.json`.
