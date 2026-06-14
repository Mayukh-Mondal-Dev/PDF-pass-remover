"""PDF Password Remover — Streamlit application.

Upload one or more password-protected PDFs, supply the password, and
download unlocked copies.
"""

from __future__ import annotations

import logging
from io import BytesIO
from pathlib import PurePosixPath

import streamlit as st
from pypdf import PdfReader, PdfWriter
from pypdf.errors import DependencyError, PdfReadError

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MAX_FILE_SIZE_MB = 100
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------


class PDFDecryptionError(Exception):
    """Raised when a PDF cannot be decrypted."""


def remove_pdf_password(file_bytes: bytes, password: str) -> bytes:
    """Return *file_bytes* as an unencrypted PDF.

    Parameters
    ----------
    file_bytes:
        Raw bytes of the source PDF.
    password:
        Password used to decrypt the file. May be empty if the file is
        not actually encrypted.

    Raises
    ------
    PDFDecryptionError
        If the file is encrypted and the password is wrong or missing.
    PdfReadError
        If the file is not a valid PDF.
    """
    input_stream = BytesIO(file_bytes)

    try:
        reader = PdfReader(input_stream)
    except PdfReadError:
        raise PdfReadError("The file does not appear to be a valid PDF.")

    if reader.is_encrypted:
        if not password:
            raise PDFDecryptionError(
                "This file is encrypted — please provide a password."
            )
        try:
            result = reader.decrypt(password)
        except Exception as exc:
            logger.debug("Decryption failed: %s", exc)
            raise PDFDecryptionError(
                "Could not decrypt the file. The password may be incorrect "
                "or the encryption method may be unsupported."
            ) from exc

        # pypdf returns 0 when the password is wrong (owner vs user may
        # return 1 or 2 on success).
        if result == 0:
            raise PDFDecryptionError("Incorrect password.")

    writer = PdfWriter()
    try:
        for page in reader.pages:
            writer.add_page(page)
    except DependencyError as exc:
        logger.debug("Missing crypto backend: %s", exc)
        raise PDFDecryptionError(
            "This PDF requires AES decryption support. Install "
            "cryptography>=3.1 and restart the app."
        ) from exc

    out_stream = BytesIO()
    writer.write(out_stream)
    return out_stream.getvalue()


def _safe_stem(filename: str) -> str:
    """Return the filename without the last extension, handling edge cases."""
    return PurePosixPath(filename).stem or filename


# ---------------------------------------------------------------------------
# Streamlit UI
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="PDF Password Remover",
    page_icon="🔓",
    layout="centered",
)

st.title("PDF Password Remover")
st.caption(
    "Upload one or more password-protected PDFs, enter the password, "
    "and download unlocked copies."
)

st.divider()

# --- Inputs ----------------------------------------------------------------
uploaded_files = st.file_uploader(
    "Choose PDF files",
    type=["pdf"],
    accept_multiple_files=True,
    help=f"Maximum {MAX_FILE_SIZE_MB} MB per file.",
)

password = st.text_input(
    "Password",
    type="password",
    placeholder="Enter the PDF password",
    help="The same password will be used for every uploaded file.",
)

# --- Processing ------------------------------------------------------------
if not uploaded_files:
    st.info("Upload at least one PDF to get started.", icon="📄")
    st.stop()

st.divider()

success_count = 0
fail_count = 0

for uploaded_file in uploaded_files:
    with st.container(border=True):
        st.markdown(f"**📄 {uploaded_file.name}**")

        # Guard: file-size limit
        file_bytes = uploaded_file.read()
        if len(file_bytes) > MAX_FILE_SIZE_BYTES:
            st.error(
                f"File exceeds the {MAX_FILE_SIZE_MB} MB size limit — skipped.",
                icon="⚠️",
            )
            fail_count += 1
            continue

        # Guard: empty file
        if len(file_bytes) == 0:
            st.error("File is empty — skipped.", icon="⚠️")
            fail_count += 1
            continue

        try:
            unlocked_bytes = remove_pdf_password(file_bytes, password)
        except PDFDecryptionError as exc:
            st.error(str(exc), icon="🔒")
            fail_count += 1
            continue
        except PdfReadError as exc:
            st.error(str(exc), icon="❌")
            fail_count += 1
            continue
        except Exception:
            logger.exception("Unexpected error processing %s", uploaded_file.name)
            st.error(
                "An unexpected error occurred while processing this file.",
                icon="❌",
            )
            fail_count += 1
            continue

        out_name = f"{_safe_stem(uploaded_file.name)}_unlocked.pdf"
        st.success("Unlocked successfully!", icon="✅")
        st.download_button(
            label="⬇️ Download unlocked PDF",
            data=unlocked_bytes,
            file_name=out_name,
            mime="application/pdf",
            key=f"dl_{uploaded_file.name}_{uploaded_file.file_id}",
        )
        success_count += 1

# --- Summary ---------------------------------------------------------------
st.divider()
cols = st.columns(2)
cols[0].metric("Unlocked", success_count)
cols[1].metric("Failed", fail_count)
