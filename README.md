# License compliance and LICENSING file generator

This project generates license compliance information from multiple SBOM (Software Bill of Materials) JSON files. It extracts license information for each software component and outputs it in both text and HTML formats.

## Features

- **Multi-SBOM Support**: Scans multiple SBOM JSON files from a specified directory.
- **License Information Extraction**: Extracts and deduplicates license information for each component.
- **SPDX License Reference**: Always uses the SPDX license reference URL.
- **Output Formats**: Generates `license_compliance.txt`, `license_compliance.html`, `licenses_text.txt`, and `licenses_text.html` files.
- **Concurrency**: Utilizes concurrent processing for faster license data fetching.

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

For more details on usage, script description, and example outputs, see the additional README files in this repository.

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

# Script Description

The script performs the following steps:

1. **Download SPDX Licenses**: Fetches the SPDX license data from the URL `https://raw.githubusercontent.com/spdx/license-list-data/main/json/licenses.json`.
2. **Scan SBOM Files**: Scans all JSON files in the `sboms` directory and extracts unique components.
3. **Extract License Information**: For each component, extracts license information and ensures URLs are taken from the SPDX data.
4. **Generate Outputs**: Writes the license compliance information to `license_compliance.txt` and `license_compliance.html`.

# Example Output
## Text File (`license_compliance.txt`)
```text
Component: org.slf4j:jul-to-slf4j, Version: 2.0.12, License: MIT, https://spdx.org/licenses/MIT.html
Component: ch.qos.logback:logback-classic, Version: 1.4.14, License: EPL-1.0, https://spdx.org/licenses/EPL-1.0.html; License: LGPL-2.1, https://spdx.org/licenses/LGPL-2.1.html
```
## HTML File (`license_compliance.html`)
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <title>License Compliance Report</title>
    <style>
        table {
            width: 100%;
            border-collapse: collapse;
        }
        table, th, td {
            border: 1px solid black;
        }
        th, td {
            padding: 8px;
            text-align: left;
        }
        th {
            background-color: #f2f2f2;
        }
        input[type="text"] {
            margin-bottom: 10px;
            width: 100%;
            padding: 8px;
        }
    </style>
</head>
<body>
    <h1>License Compliance Report</h1>
    <input type="text" id="searchInput" onkeyup="searchTable()" placeholder="Search for components..">
    <table id="complianceTable">
        <thead>
            <tr>
                <th>Component</th>
                <th>Version</th>
                <th>License</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>org.slf4j:jul-to-slf4j</td>
                <td>2.0.12</td>
                <td>MIT, <a href="https://spdx.org/licenses/MIT.html">https://spdx.org/licenses/MIT.html</a></td>
            </tr>
            <tr>
                <td>ch.qos.logback:logback-classic</td>
                <td>1.4.14</td>
                <td>EPL-1.0, <a href="https://spdx.org/licenses/EPL-1.0.html">https://spdx.org/licenses/EPL-1.0.html</a>; LGPL-2.1, <a href="https://spdx.org/licenses/LGPL-2.1.html">https://spdx.org/licenses/LGPL-2.1.html</a></td>
            </tr>
        </tbody>
    </table>
    <script>
        function searchTable() {
            var input, filter, table, tr, td, i, j, txtValue;
            input = document.getElementById("searchInput");
            filter = input.value.toLowerCase();
            table = document.getElementById("complianceTable");
            tr = table.getElementsByTagName("tr");
            for (i = 1; i < tr.length; i++) {
                tr[i].style.display = "none";
                td = tr[i].getElementsByTagName("td");
                for (j = 0; j < td.length; j++) {
                    if (td[j]) {
                        txtValue = td[j].textContent || td[j].innerText;
                        if (txtValue.toLowerCase().indexOf(filter) > -1) {
                            tr[i].style.display = "";
                            break;
                        }
                    }
                }
            }
        }
    </script>
</body>
</html> 
```
## HTML File (`licenses_text.txt`)
```text
License ID: MIT
<license text for MIT>
License ID: EPL-1.0
<license text for EPL-1.0>
License ID: LGPL-2.1
<license text for LGPL-2.1>
```
## HTML File (`licenses_text.html`)
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <title>License Texts</title>
</head>
<body>
    <h2>License ID: MIT</h2>
    <pre><license text for MIT></pre>
    <hr>
    <h2>License ID: EPL-1.0</h2>
    <pre><license text for EPL-1.0></pre>
    <hr>
    <h2>License ID: LGPL-2.1</h2>
    <pre><license text for LGPL-2.1></pre>
    <hr>
</body>
</html>
```
