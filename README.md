# License Compliance Generator

This project generates license compliance information from multiple SBOM (Software Bill of Materials) JSON files. It extracts license information for each software component and outputs it in both text and HTML formats.

## Features

- **Multi-SBOM Support**: Scans multiple SBOM JSON files from a specified directory.
- **License Information Extraction**: Extracts and deduplicates license information for each component.
- **SPDX License Reference**: Always uses the SPDX license reference URL.
- **Output Formats**: Generates `license_compliance.txt`, `license_compliance.html`, `licenses_text.txt`, and `licenses_text.html` files.

## Prerequisites

- Python 3.x
- `requests` library

## Installation

1. Clone the repository or download the script files.
2. Install the required Python library:

    ```bash
    pip install requests
    ```

## Directory Structure

- `sboms/`: Directory containing the SBOM JSON files.
- `template.html`: HTML template used to generate the HTML output.
- `generate.py`: Main script to generate license compliance files.

## Usage

1. Place your SBOM JSON files in the `sboms` directory.
2. Ensure the `template.html` file is in the same directory as `generate.py`.
3. Run the script:

    ```bash
    python3 generate.py
    ```

4. The script will generate the following files in the project directory:
    - `license_compliance.txt`
    - `license_compliance.html`
    - `licenses_text.txt`
    - `licenses_text.html`

## Script Description

The script performs the following steps:

1. **Load HTML Template**: Reads the HTML template from `template.html`.
2. **Download SPDX Licenses**: Fetches the SPDX license data from the URL `https://raw.githubusercontent.com/spdx/license-list-data/main/json/licenses.json`.
3. **Scan SBOM Files**: Scans all JSON files in the `sboms` directory and extracts unique components.
4. **Extract License Information**: For each component, extracts license information and ensures URLs are taken from the SPDX data.
5. **Generate Outputs**: Writes the license compliance information to `license_compliance.txt` and `license_compliance.html`. Additionally, generates `licenses_text.txt` and `licenses_text.html` containing detailed license texts.

## HTML Template

Ensure your `template.html` includes a placeholder for the compliance content:

```html
<!DOCTYPE html>
<html>
<head>
    <title>License Compliance</title>
</head>
<body>
    <h1>License Compliance Report</h1>
    <table border="1">
        <thead>
            <tr>
                <th>Component</th>
                <th>Version</th>
                <th>License Information</th>
            </tr>
        </thead>
        <tbody>
            {{compliance_html_content}}
        </tbody>
    </table>
</body>
</html>
