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
- `generate.py`: Main script to generate license compliance files.

## Usage

1. Place your SBOM JSON files in the `sboms` directory.
2. Run the script:

    ```bash
    python3 generate.py
    ```

3. The script will generate the following files in the project directory:
    - `license_compliance.txt`
    - `license_compliance.html`
    - `licenses_text.txt`
    - `licenses_text.html`

## Script Description

The script performs the following steps:

1. **Download SPDX Licenses**: Fetches the SPDX license data from the URL `https://raw.githubusercontent.com/spdx/license-list-data/main/json/licenses.json`.
2. **Scan SBOM Files**: Scans all JSON files in the `sboms` directory and extracts unique components.
3. **Extract License Information**: For each component, extracts license information and ensures URLs are taken from the SPDX data.
4. **Generate Outputs**: Writes the license compliance information to `license_compliance.txt` and `license_compliance.html`. Additionally, generates `licenses_text.txt` and `licenses_text.html` containing detailed license texts.
