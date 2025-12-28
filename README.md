# Epson Label Printer for Home Assistant

This custom component integrates Epson network-enabled label printers (and other ESC/POS compatible printers) into Home Assistant. It allows you to monitor printer status and print labels using simple text or advanced markup.

## Features

- **Connectivity Monitoring**: Binary sensor to track if the printer is online.
- **Paper Status**: Binary sensor to alert when there's a paper issue (e.g., out of paper).
- **Simple Printing**: Easy-to-use service for basic text labels.
- **Advanced Markup**: Support for barcodes, QR codes, and custom formatting via an extended markup language.
- **UI Configuration**: Easy setup via the Home Assistant integrations page.

## Installation

### HACS (Recommended)
1. Open HACS in your Home Assistant instance.
2. Click on "Integrations".
3. Click the three dots in the top right corner and select "Custom repositories".
4. Add the URL of this repository and select "Integration" as the category.
5. Search for "Epson Label Printer" and click "Download".
6. Restart Home Assistant.

### Manual
1. Download the `custom_components/epson_label` directory from this repository.
2. Copy it into your Home Assistant's `custom_components` directory.
3. Restart Home Assistant.

## Configuration

1. In Home Assistant, go to **Settings** > **Devices & Services**.
2. Click **Add Integration**.
3. Search for **Epson Label Printer**.
4. Enter the **Host** (IP address) and **Port** (default is 9100) of your printer.

## Services

### `epson_label.print_label`
Prints a simple text label.

**Fields:**
- `text` (Required): The text to print.
- `size` (Optional): Text size magnitude (1-8, default: 1).
- `cut` (Optional): Cut paper after printing (default: true).
- `feed_lines` (Optional): Number of empty lines to feed before cutting (default: 0).

### `epson_label.print_label_extended`
Prints a label using advanced markup for barcodes, formatting, etc.

**Fields:**
- `text` (Required): Text containing markup commands.

For details on the markup syntax, see [MARKUP.md](MARKUP.md).

#### Example Markup:
```
$ALIGN(center)
$SIZE(2,2)
MY PRODUCT
$SIZE(1,1)
$FEED(1)
$BARCODE(12345678, CODE39)
$CUT()
```

## Requirements
- `python-escpos==3.1` (automatically installed)

## License
This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.
