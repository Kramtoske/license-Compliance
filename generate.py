import os
import json
import base64
import requests

# Directory containing SBOM JSON files
sboms_dir = "sboms"

# Hosted licenses JSON URL
licenses_url = "https://raw.githubusercontent.com/spdx/license-list-data/main/json/licenses.json"

# Fetch the licenses data
response = requests.get(licenses_url)
licenses_data = response.json()['licenses']
licenses_lookup = {license['licenseId']: license for license in licenses_data}

# Function to get license details URL
def get_license_details_url(license_id):
    return licenses_lookup.get(license_id, {}).get('detailsUrl', "")

# Function to get full license text
def get_full_license_text(details_url):
    response = requests.get(details_url)
    license_data = response.json()
    return license_data.get('licenseText', ''), license_data.get('licenseTextHtml', '')

# Function to decode base64 license content
def decode_base64_license_content(content):
    return base64.b64decode(content).decode('utf-8')

# Consolidate and deduplicate components from all SBOMs
components = {}
for sbom_file in os.listdir(sboms_dir):
    if sbom_file.endswith(".json"):
        with open(os.path.join(sboms_dir, sbom_file), "r") as file:
            sbom_data = json.load(file)
            for component in sbom_data.get("components", []):
                component_key = f"{component['group']}:{component['name']}:{component['version']}"
                if component_key not in components:
                    components[component_key] = component

# Generate license compliance report
license_report = []
license_texts = {}

for key, component in components.items():
    licenses_info = []
    for license in component.get('licenses', []):
        license_id = license['license'].get('id', 'Unknown')
        license_name = license['license'].get('name', 'Unknown')

        # Check for license URL from SPDX data
        license_details_url = ""
        if license_id != 'Unknown':
            license_details_url = get_license_details_url(license_id)

        if license_details_url:
            license_text, license_text_html = get_full_license_text(license_details_url)
            if license_text and license_text_html:
                license_texts[license_id] = {'text': license_text, 'html': license_text_html}
        else:
            if 'text' in license['license']:
                license_text = decode_base64_license_content(license['license']['text']['content'])
                license_text_html = "<pre>" + license_text + "</pre>"
                license_texts[license_name] = {'text': license_text, 'html': license_text_html}
            else:
                license_text = ""
                license_text_html = ""

        license_url = license.get('url', 'Unknown')
        if 'spdx.org' not in license_url:
            license_url = license_details_url

        licenses_info.append(f"License: {license_id if license_id != 'Unknown' else license_name}, {license_url}")

    component_info = f"Component: {component['group']}:{component['name']}, Version: {component['version']}, {'; '.join(licenses_info)}"
    license_report.append(component_info)

# Write license compliance text report
with open("license_compliance.txt", "w") as txt_file:
    for item in license_report:
        txt_file.write(f"{item}\n")

# Write license compliance HTML report
html_report = """
<!DOCTYPE html>
<html>
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
                <th>URL</th>
            </tr>
        </thead>
        <tbody>
"""

for item in license_report:
    component, version, *licenses_info = item.split(', ')
    licenses_html = ", ".join(licenses_info).replace("License: ", "").replace("Unknown, ", "")
    html_report += f"""
        <tr>
            <td>{component}</td>
            <td>{version}</td>
            <td>{licenses_html}</td>
        </tr>
    """

html_report += """
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
"""

with open("license_compliance.html", "w") as html_file:
    html_file.write(html_report)

# Write license texts to separate files
with open("licenses_text.txt", "w") as txt_file:
    for license_id, texts in license_texts.items():
        txt_file.write(f"License ID: {license_id}\n")
        txt_file.write(f"{texts['text']}\n\n")

with open("licenses_text.html", "w") as html_file:
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>License Texts</title>
    </head>
    <body>
    """
    for license_id, texts in license_texts.items():
        html_content += f"<h2>License ID: {license_id}</h2>"
        html_content += texts['html']
        html_content += "<hr>"
    html_content += """
    </body>
    </html>
    """
    html_file.write(html_content)

print("license_compliance.txt, license_compliance.html, licenses_text.txt, and licenses_text.html created successfully.")
