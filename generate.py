import os
import json
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# Directory containing SBOM JSON files
SBOMS_DIR = "sboms"
# Hosted licenses JSON URL
LICENSES_URL = "https://raw.githubusercontent.com/spdx/license-list-data/main/json/licenses.json"

def fetch_licenses_data(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()['licenses']
    except requests.exceptions.RequestException as e:
        print(f"Error fetching licenses data from {url}: {e}")
        return []

def load_sbom_files(directory):
    components = {}
    for sbom_file in os.listdir(directory):
        if sbom_file.endswith(".json"):
            with open(os.path.join(directory, sbom_file), "r") as file:
                sbom_data = json.load(file)
                for component in sbom_data.get("components", []):
                    component_key = f"{component['group']}:{component['name']}:{component['version']}"
                    if component_key not in components:
                        components[component_key] = component
    return components

def get_license_reference_url(license_id, licenses_lookup):
    return licenses_lookup.get(license_id, {}).get('reference', "")

def get_full_license_text(details_url):
    try:
        response = requests.get(details_url)
        response.raise_for_status()
        license_data = response.json()
        return license_data.get('licenseText', ''), license_data.get('licenseTextHtml', '')
    except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
        print(f"Error fetching license details from {details_url}: {e}")
        return '', ''

def process_license(license, licenses_lookup, license_texts):
    license_id = license.get('license', {}).get('id', 'Unknown')
    license_name = license.get('license', {}).get('name', 'Unknown')
    license_reference_url = get_license_reference_url(license_id, licenses_lookup) if license_id != 'Unknown' else ""

    if not license_reference_url and 'url' in license.get('license', {}):
        license_reference_url = license['license']['url']

    if license_reference_url:
        details_url = licenses_lookup.get(license_id, {}).get('detailsUrl', "")
        if license_id not in license_texts and details_url:
            license_text, license_text_html = get_full_license_text(details_url)
            if license_text and license_text_html:
                license_texts[license_id] = {'text': license_text, 'html': license_text_html}
    return license_id, license_name, license_reference_url

def format_license_info(license_id, license_name, license_reference_url):
    if license_reference_url:
        return (
            f"License: {license_id if license_id != 'Unknown' else license_name}, {license_reference_url}",
            f'License: {license_id if license_id != "Unknown" else license_name}, <a href="{license_reference_url}" target="_blank">{license_reference_url}</a>'
        )
    return (
        f"License: {license_id if license_id != 'Unknown' else license_name}",
        f'License: {license_id if license_id != "Unknown" else license_name}'
    )

def process_component(key, component, licenses_lookup, license_texts):
    licenses_info = []
    licenses_info_html = []

    for license in component.get('licenses', []):
        license_id, license_name, license_reference_url = process_license(license, licenses_lookup, license_texts)
        license_info, license_info_html = format_license_info(license_id, license_name, license_reference_url)
        licenses_info.append(license_info)
        licenses_info_html.append(license_info_html)

    component_info = f"Component: {component['group']}:{component['name']}, Version: {component['version']}, {'; '.join(licenses_info)}"
    component_info_html = f"Component: {component['group']}:{component['name']}, Version: {component['version']}, {'; '.join(licenses_info_html)}"

    return component_info, component_info_html

def generate_reports(components, licenses_lookup):
    license_report = []
    license_report_html = []
    license_texts = {}

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(process_component, key, component, licenses_lookup, license_texts): key for key, component in components.items()}
        for future in as_completed(futures):
            try:
                component_info, component_info_html = future.result()
                license_report.append(component_info)
                license_report_html.append(component_info_html)
            except Exception as e:
                print(f"Error processing component: {e}")

    return license_report, license_report_html, license_texts

def write_text_report(filename, data):
    with open(filename, "w") as file:
        for item in data:
            file.write(f"{item}\n")

def write_html_report(filename, data):
    html_report = """
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
"""
    for item in data:
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

    with open(filename, "w") as file:
        file.write(html_report)

def write_license_texts(text_filename, html_filename, license_texts):
    with open(text_filename, "w") as txt_file:
        for license_id, texts in license_texts.items():
            txt_file.write(f"License ID: {license_id}\n")
            txt_file.write(f"{texts['text']}\n\n")

    html_content = """
    <!DOCTYPE html>
    <html lang="en">
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

    with open(html_filename, "w") as html_file:
        html_file.write(html_content)

def main():
    licenses_data = fetch_licenses_data(LICENSES_URL)
    licenses_lookup = {license['licenseId']: license for license in licenses_data}
    components = load_sbom_files(SBOMS_DIR)
    license_report, license_report_html, license_texts = generate_reports(components, licenses_lookup)
    write_text_report("license_compliance.txt", license_report)
    write_html_report("license_compliance.html", license_report_html)
    write_license_texts("licenses_text.txt", "licenses_text.html", license_texts)
    print("license_compliance.txt, license_compliance.html, licenses_text.txt, and licenses_text.html created successfully.")

if __name__ == "__main__":
    main()
