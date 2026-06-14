# PDF Password Remover

A simple [Streamlit](https://streamlit.io/) app that removes passwords from PDF files so you can freely open, print, and edit them.

## Features

- Upload **multiple PDFs** at once.
- Provides clear per-file error messages (wrong password, invalid PDF, file too large).
- Shows a summary of successful / failed unlocks.

## Quick-start

1. **Install dependencies** (preferably inside a virtual environment):

   ```bash
   pip install -r requirements.txt
   ```

2. **Run the app:**

   ```bash
   streamlit run streamlit_app.py
   ```

3. Upload one or more password-protected PDFs, enter the password, and click the download button to save unlocked copies.

## Requirements

| Package    | Minimum version |
| ---------- | --------------- |
| streamlit  | 1.0             |
| pypdf      | 3.0             |
| cryptography | 3.1           |
