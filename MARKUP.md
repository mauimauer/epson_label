# Epson Label Printer Extended Markup

The `print_label_extended` service supports a simple markup language to control the printer dynamically within the text payload.

## Syntax
Commands start with `$` followed by the command name in UPPERCASE and arguments in parentheses.
Arguments are separated by commas. String arguments usually don't need quotes unless they contain commas, but the parser is simple: it splits by comma.

Example:
```
Title
$SIZE(2, 2)
Big Text
$SIZE(1, 1)
Normal Text
$BARCODE(123456, CODE39)
$CUT()
```

## Available Commands

### Text Formatting
*   **$SIZE(width, height)**
    *   `width`: 1-8
    *   `height`: 1-8
    *   Example: `$SIZE(2, 2)`

*   **$ALIGN(alignment)**
    *   `alignment`: `left`, `center`, `right`
    *   Example: `$ALIGN(center)`

*   **$BOLD(enable)**
    *   `enable`: `true` or `false`
    *   Example: `$BOLD(true)`

*   **$INVERT(enable)**
    *   `enable`: `true` or `false`
    *   Example: `$INVERT(true)` (White on black)

### Barcodes & QR
*   **$BARCODE(data, format, width, height)**
    *   `data`: The content of the barcode.
    *   `format`: `UPC-A`, `UPC-E`, `EAN13`, `EAN8`, `CODE39`, `ITF`, `NW-7`, `CODE128`, `CODE93`.
    *   `width`: (Optional, default 3) Bar width.
    *   `height`: (Optional, default 100) Bar height.
    *   Example: `$BARCODE(12345678, CODE39)`

*   **$QR(data, size)**
    *   `data`: The content of the QR code.
    *   `size`: (Optional) Size of QR code.
    *   Example: `$QR(https://home-assistant.io)`

### Actions
*   **$CUT()**
    *   Cuts the paper immediately.
    *   Example: `$CUT()`

*   **$FEED(lines)**
    *   Feeds `lines` empty lines.
    *   Example: `$FEED(3)`
