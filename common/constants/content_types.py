


# The document must be an image in JPEG, PNG, PDF, or TIFF format.
TEXTRACT_ACCEPTED_CONTENT_TYPES = [
    # JPEG
    "image/jpeg",
    "image/pjpeg",
    "image/jpg",

    # PNG
    "image/png",
    "image/x-png",

    # PDF
    "application/pdf",
    "application/x-pdf",
    "application/acrobat",
    "application/vnd.adobe.pdf",

    # TIFF
    "image/tiff",
    "image/x-tiff"
]


IMAGE_CONTENT_TYPES = [
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/bmp",
    "image/tiff",
    "image/webp",
    "image/heic",
    "image/heif"
]

DOCUMENT_CONTENT_TYPES = [
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-powerpoint",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/rtf",
    "application/vnd.oasis.opendocument.text",
    "application/vnd.oasis.opendocument.spreadsheet",
    "application/vnd.oasis.opendocument.presentation",
    "text/plain",
    "text/csv",
    "text/markdown",
    "text/html",
    "application/pdf"
]

CONVERTABLE_CONTENT_TYPES = IMAGE_CONTENT_TYPES + DOCUMENT_CONTENT_TYPES
