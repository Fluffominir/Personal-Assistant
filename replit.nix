{ pkgs }: {
  deps = [
    pkgs.python311Full   # Python runtime
    pkgs.tesseract       # OCR binary so pytesseract works
  ];
}
