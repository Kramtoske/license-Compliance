import os
import json
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# Directory containing SBOM JSON files
sboms_dir = "sboms"

# Hosted licenses JSON URL
licenses_url = "https://raw.githubusercontent.com/spdx/license-list-data/main/json/licenses.json"

# Fetch the licenses data
response = requests.get(licenses_url)
licenses_data = response.json()['licenses']
licenses_lookup = {license['licenseId']: license for license in licenses_data}

# Function to get license reference URL
def get_license_reference_url(license_id):
    return licenses_lookup.get(license_id, {}).get('reference', "")

# Function to get full license text
def get_full_license_text(details_url):
    try:
        response = requests.get(details_url)
        response.raise_for_status()  # Raise an error for bad status
        license_data = response.json()
        return license_data.get('licenseText', ''), license_data.get('licenseTextHtml', '')
    except (requests.exceptions.HTTPError, requests.exceptions.RequestException, json.JSONDecodeError) as e:
        print(f"Error fetching license details from {details_url}: {e}")
        return '', ''

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

# Function to process each component and gather license info
def process_component(key, component):
    licenses_info = []
    licenses_info_html = []
    for license in component.get('licenses', []):
        license_id = license['license'].get('id', 'Unknown')
        license_name = license['license'].get('name', 'Unknown')

        # Check for license URL from SPDX data
        license_reference_url = ""
        if license_id != 'Unknown':
            license_reference_url = get_license_reference_url(license_id)

        if license_reference_url:
            details_url = licenses_lookup[license_id].get('detailsUrl', "")
            license_text, license_text_html = get_full_license_text(details_url)
            if license_text and license_text_html:
                license_texts[license_id] = {'text': license_text, 'html': license_text_html}
        else:
            license_text = ""
            license_text_html = ""

        if license_reference_url:
            licenses_info.append(f"License: {license_id if license_id != 'Unknown' else license_name}, {license_reference_url}")
            licenses_info_html.append(f'License: {license_id if license_id != "Unknown" else license_name}, <a href="{license_reference_url}" target="_blank">{license_reference_url}</a>')
        else:
            licenses_info.append(f"License: {license_id if license_id != 'Unknown' else license_name}")
            licenses_info_html.append(f'License: {license_id if license_id != "Unknown" else license_name}')

    component_info = f"Component: {component['group']}:{component['name']}, Version: {component['version']}, {'; '.join(licenses_info)}"
    component_info_html = f"Component: {component['group']}:{component['name']}, Version: {component['version']}, {'; '.join(licenses_info_html)}"
    return component_info, component_info_html

# Generate license compliance report
license_report = []
license_report_html = []
license_texts = {}

# Use ThreadPoolExecutor for concurrent processing
with ThreadPoolExecutor(max_workers=10) as executor:
    futures = {executor.submit(process_component, key, component): key for key, component in components.items()}
    for future in as_completed(futures):
        try:
            component_info, component_info_html = future.result()
            license_report.append(component_info)
            license_report_html.append(component_info_html)
        except Exception as e:
            print(f"Error processing component: {e}")

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
            </tr>
        </thead>
        <tbody>
"""

for item in license_report_html:
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
