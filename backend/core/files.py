import re
from io import BytesIO

from PIL import Image
from django.core.files.uploadedfile import InMemoryUploadedFile, UploadedFile
from pi_heif import register_heif_opener

register_heif_opener()

HEIF_CONTENT_TYPES = {"image/heif", "image/heic"}


def normalize_upload(uploaded_file: UploadedFile) -> UploadedFile:
    """
    Convert HEIF/HEIC uploads (e.g. iPhone photos) to JPEG, since browsers
    cannot render HEIF. Any other file is returned unchanged.
    """
    if uploaded_file.content_type not in HEIF_CONTENT_TYPES:
        return uploaded_file

    converted = BytesIO()
    with Image.open(uploaded_file) as image:
        image.convert("RGB").save(converted, format="jpeg")

    stem = re.sub(r"\.hei[cf]$", "", uploaded_file.name or "file", flags=re.IGNORECASE)
    return InMemoryUploadedFile(
        converted,
        None,
        f"{stem}.jpeg",
        "image/jpeg",
        converted.getbuffer().nbytes,
        None,
    )
