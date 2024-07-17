import os
import json
import re
import requests
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed

# Directory containing SBOM JSON files
SBOMS_DIR = "sboms"
# Hosted licenses JSON URLs
LICENSES_URL = "https://raw.githubusercontent.com/spdx/license-list-data/main/json/licenses.json"
EXCEPTIONS_URL = "https://raw.githubusercontent.com/spdx/license-list-data/main/json/exceptions.json"

LICENSE_NAME_TO_ID_MAP = {}

def fetch_data(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from {url}: {e}")
        return {}

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

def load_license_name_to_id_map(json_file):
    if not json_file:
        return {}
    try:
        with open(json_file, 'r') as file:
            return json.load(file)
    except Exception as e:
        print(f"Error loading mapping file: {e}")
        return {}

def extract_vcs_url(component):
    external_references = component.get("externalReferences", [])
    for reference in external_references:
        if reference.get("type") == "vcs":
            return reference.get("url", "")
    return "N/A"

def resolve_relative_url(base_url, relative_url):
    if not relative_url.startswith("http"):
        return base_url + relative_url.lstrip("./")
    return relative_url

def get_license_reference_url(license_id, licenses_lookup, exceptions_lookup):
    if license_id in licenses_lookup:
        return licenses_lookup.get(license_id, {}).get('reference', "")
    if license_id in exceptions_lookup:
        return exceptions_lookup.get(license_id, {}).get('reference', "")
    return ""

def get_full_license_text(details_url, is_exception=False):
    try:
        response = requests.get(details_url)
        response.raise_for_status()
        license_data = response.json()
        if is_exception:
            return license_data.get('licenseExceptionText', ''), license_data.get('exceptionTextHtml', '')
        return license_data.get('licenseText', ''), license_data.get('licenseTextHtml', '')
    except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
        print(f"Error fetching license details from {details_url}: {e}")
        return '', ''

def process_individual_license(license, licenses_lookup, license_texts, exceptions_lookup):
    license_ids = []
    license_names = []
    license_references = []
    exceptions = []

    license_id = license['license'].get('id', 'Unknown')
    license_name = license['license'].get('name', 'Unknown')
    license_url = license['license'].get('url', '')

    mapped_ids = LICENSE_NAME_TO_ID_MAP.get(license_name, [license_id])

    for id in mapped_ids:
        id_normalized = id.lower()

        if id_normalized in exceptions_lookup:
            exception_data = exceptions_lookup[id_normalized]
            exceptions.append(id_normalized)
            details_url = exception_data.get('detailsUrl', '')
            reference_url = exception_data.get('reference', '')

            if id_normalized not in license_texts and details_url:
                license_text, license_text_html = get_full_license_text(details_url, is_exception=True)
                if license_text and license_text_html:
                    license_texts[id_normalized] = {'text': license_text, 'html': license_text_html}

            license_ids.append(id)
            license_names.append(exception_data.get('name', 'Unknown'))
            license_references.append(reference_url if reference_url else 'No URL')
        else:
            if id != 'Unknown':
                reference_url = get_license_reference_url(id, licenses_lookup, exceptions_lookup)
                details_url = licenses_lookup.get(id, {}).get('detailsUrl', "")

                if id not in license_texts and details_url:
                    license_text, license_text_html = get_full_license_text(details_url)
                    if license_text and license_text_html:
                        license_texts[id] = {'text': license_text, 'html': license_text_html}

                license_ids.append(id)
                license_names.append(licenses_lookup.get(id, {}).get('name', license_name))
                license_references.append(reference_url if reference_url else 'No URL')
            else:
                license_ids.append(id)
                license_names.append(license_name)
                license_references.append(license_url if license_url else 'No URL')

    return license_ids, license_names, license_references, exceptions

def process_license_expression(license, licenses_lookup, license_texts, exceptions_lookup):
    license_ids = []
    license_names = []
    license_references = []
    exceptions = []

    expression = license['expression']
    license_ids_in_expression = re.findall(r'\b([A-Za-z0-9\.\-]+)\b', expression)
    for license_id in license_ids_in_expression:
        license_id_normalized = license_id.lower()
        if license_id_normalized in ['or', 'and', 'with', 'without', 'exception']:
            continue

        if license_id_normalized in exceptions_lookup:
            exception_data = exceptions_lookup[license_id_normalized]
            exceptions.append(license_id_normalized)
            details_url = exception_data.get('detailsUrl', '')
            reference_url = exception_data.get('reference', '')

            if license_id_normalized not in license_texts and details_url:
                license_text, license_text_html = get_full_license_text(details_url, is_exception=True)
                if license_text and license_text_html:
                    license_texts[license_id_normalized] = {'text': license_text, 'html': license_text_html}

            license_ids.append(license_id)
            license_names.append(exception_data.get('name', 'Unknown'))
            license_references.append(reference_url if reference_url else 'No URL')
        else:
            license_name = licenses_lookup.get(license_id, {}).get('name', 'Unknown')
            mapped_ids = LICENSE_NAME_TO_ID_MAP.get(license_name, [license_id])

            for id in mapped_ids:
                id_normalized = id.lower()
                if id_normalized in exceptions_lookup:
                    exception_data = exceptions_lookup[id_normalized]
                    exceptions.append(id_normalized)
                    details_url = exception_data.get('detailsUrl', '')
                    reference_url = exception_data.get('reference', '')

                    if id_normalized not in license_texts and details_url:
                        license_text, license_text_html = get_full_license_text(details_url, is_exception=True)
                        if license_text and license_text_html:
                            license_texts[id_normalized] = {'text': license_text, 'html': license_text_html}

                    license_ids.append(id)
                    license_names.append(exception_data.get('name', 'Unknown'))
                    license_references.append(reference_url if reference_url else 'No URL')
                else:
                    if id != 'Unknown':
                        reference_url = get_license_reference_url(id, licenses_lookup, exceptions_lookup)
                        details_url = licenses_lookup.get(id, {}).get('detailsUrl', "")

                        if id not in license_texts and details_url:
                            license_text, license_text_html = get_full_license_text(details_url)
                            if license_text and license_text_html:
                                license_texts[id] = {'text': license_text, 'html': license_text_html}

                        license_ids.append(id)
                        license_names.append(licenses_lookup.get(id, {}).get('name', license_name))
                        license_references.append(reference_url if reference_url else 'No URL')
                    else:
                        license_ids.append(id)
                        license_names.append(license_name)
                        license_references.append('No URL')

    return license_ids, license_names, license_references, exceptions

def process_license_name(license, licenses_lookup, license_texts, exceptions_lookup):
    license_ids = []
    license_names = []
    license_references = []
    exceptions = []

    license_name = license['name']
    mapped_data = LICENSE_NAME_TO_ID_MAP.get(license_name, ['Unknown'])

    if isinstance(mapped_data, list):
        for item in mapped_data:
            item_normalized = item.lower()
            if item_normalized in licenses_lookup:
                reference_url = get_license_reference_url(item, licenses_lookup, exceptions_lookup)
                details_url = licenses_lookup.get(item, {}).get('detailsUrl', "")

                if item not in license_texts and details_url:
                    license_text, license_text_html = get_full_license_text(details_url)
                    if license_text and license_text_html:
                        license_texts[item] = {'text': license_text, 'html': license_text_html}

                license_ids.append(item)
                license_names.append(licenses_lookup.get(item, {}).get('name', license_name))
                license_references.append(reference_url if reference_url else 'No URL')
            elif item_normalized in exceptions_lookup:
                exception_data = exceptions_lookup[item_normalized]
                exceptions.append(item_normalized)
                details_url = exception_data.get('detailsUrl', '')
                reference_url = exception_data.get('reference', '')

                if item_normalized not in license_texts and details_url:
                    license_text, license_text_html = get_full_license_text(details_url, is_exception=True)
                    if license_text and license_text_html:
                        license_texts[item_normalized] = {'text': license_text, 'html': license_text_html}

                license_ids.append(item)
                license_names.append(exception_data.get('name', 'Unknown'))
                license_references.append(reference_url if reference_url else 'No URL')
    else:
        reference_url = get_license_reference_url(mapped_data, licenses_lookup, exceptions_lookup)
        details_url = licenses_lookup.get(mapped_data, {}).get('detailsUrl', "")

        if mapped_data not in license_texts and details_url:
            license_text, license_text_html = get_full_license_text(details_url)
            if license_text and license_text_html:
                license_texts[mapped_data] = {'text': license_text, 'html': license_text_html}

        license_ids.append(mapped_data)
        license_names.append(license_name)
        license_references.append(reference_url if reference_url else 'No URL')

    return license_ids, license_names, license_references, exceptions

def process_license(license, licenses_lookup, license_texts, exceptions_lookup):
    if 'license' in license:
        return process_individual_license(license, licenses_lookup, license_texts, exceptions_lookup)
    elif 'expression' in license:
        return process_license_expression(license, licenses_lookup, license_texts, exceptions_lookup)
    elif 'name' in license:
        return process_license_name(license, licenses_lookup, license_texts, exceptions_lookup)
    return [], [], [], []

def format_license_info(license_ids, license_names, license_references, exceptions, exceptions_lookup):
    formatted_licenses = []
    formatted_licenses_html = []
    exception_ids = {ex.lower() for ex in exceptions}  # Use a set for efficient lookup

    for license_id, license_name, license_reference_url in zip(license_ids, license_names, license_references):
        if license_id.lower() not in exception_ids:
            if license_reference_url:
                formatted_licenses.append(f"License: {license_id if license_id != 'Unknown' else license_name}, {license_reference_url}")
                formatted_licenses_html.append(f'<li>License: {license_id if license_id != "Unknown" else license_name}, <a href="{license_reference_url}" target="_blank">{license_reference_url}</a></li>')
            else:
                formatted_licenses.append(f"License: {license_id if license_id != 'Unknown' else license_name}")
                formatted_licenses_html.append(f'<li>License: {license_id if license_id != "Unknown" else license_name}</li>')

    for exception in exceptions:
        exception_data = exceptions_lookup[exception.lower()]
        reference_url = exception_data.get('reference', 'No URL')
        formatted_licenses.append(f"Exception: {exception_data.get('name', 'Unknown')}, {reference_url}")
        formatted_licenses_html.append(f'<li>Exception: {exception_data.get("name", "Unknown")}, <a href="{reference_url}" target="_blank">{reference_url}</a></li>')

    formatted_licenses_text = "; ".join(formatted_licenses)
    formatted_licenses_html_list = "".join(formatted_licenses_html)  # Only join the list items, no additional <ul> here

    return formatted_licenses_text, formatted_licenses_html_list

def process_component(key, component, licenses_lookup, license_texts, exceptions_lookup):
    licenses_info = []
    licenses_info_html = []

    for license in component.get('licenses', []):
        license_ids, license_names, license_references, exceptions = process_license(license, licenses_lookup, license_texts, exceptions_lookup)
        license_info, license_info_html = format_license_info(license_ids, license_names, license_references, exceptions, exceptions_lookup)
        licenses_info.append(license_info)
        licenses_info_html.append(license_info_html)

    vcs_url = extract_vcs_url(component)

    licenses_info_text = "; ".join(licenses_info)
    licenses_info_html_list = "<ul>" + "".join(licenses_info_html) + "</ul>"

    component_info = f"Component: {component['group']}:{component['name']}, Version: {component['version']}, {licenses_info_text}, VCS: {vcs_url}"
    if vcs_url != "N/A":
        component_info_html = f"{component['group']}:{component['name']}, {component['version']}, {licenses_info_html_list}, <a href='{vcs_url}' target='_blank'>{vcs_url}</a>"
    else:
        component_info_html = f"{component['group']}:{component['name']}, {component['version']}, {licenses_info_html_list}, N/A"

    return component_info, component_info_html

def generate_reports(components, licenses_lookup, exceptions_lookup):
    license_report = []
    license_report_html = []
    license_texts = {}

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(process_component, key, component, licenses_lookup, license_texts, exceptions_lookup): key for key, component in components.items()}
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
                <th>VCS</th>
            </tr>
        </thead>
        <tbody>
"""
    for item in data:
        component, version, *licenses_info = item.split(', ')
        vcs_info = licenses_info.pop().replace("VCS: ", "")
        licenses_html = ", ".join(licenses_info).replace("License: ", "").replace("Unknown, ", "")
        html_report += f"""
            <tr>
                <td>{component}</td>
                <td>{version}</td>
                <td>{licenses_html}</td>
                <td>{vcs_info}</td>
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

    with open(filename, "w") as html_file:
        html_file.write(html_report)

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
    parser = argparse.ArgumentParser(description='Generate license compliance reports from SBOM JSON files.')
    parser.add_argument('--sbom-dir', type=str, default='sboms', help='Directory containing SBOM JSON files (default: sboms)')
    parser.add_argument('--mapping-file', type=str, help='Optional JSON file to map complex license names to SPDX IDs')
    args = parser.parse_args()

    sbom_dir = args.sbom_dir
    mapping_file = args.mapping_file

    global LICENSE_NAME_TO_ID_MAP
    LICENSE_NAME_TO_ID_MAP = load_license_name_to_id_map(mapping_file)

    licenses_data = fetch_data(LICENSES_URL).get('licenses', [])
    licenses_lookup = {license['licenseId']: license for license in licenses_data}

    exceptions_data = fetch_data(EXCEPTIONS_URL).get('exceptions', [])
    exceptions_lookup = {
        exception['licenseExceptionId'].lower(): {
            'name': exception.get('name', ''),
            'reference': resolve_relative_url('https://spdx.org/licenses/', exception.get('detailsUrl', '')),
            'detailsUrl': resolve_relative_url('https://spdx.org/licenses/', exception.get('reference', ''))
        } for exception in exceptions_data
    }

    components = load_sbom_files(sbom_dir)
    license_report, license_report_html, license_texts = generate_reports(components, licenses_lookup, exceptions_lookup)
    write_text_report("license_compliance.txt", license_report)
    write_html_report("license_compliance.html", license_report_html)
    write_license_texts("licenses_text.txt", "licenses_text.html", license_texts)
    print("license_compliance.txt, license_compliance.html, licenses_text.txt, and licenses_text.html created successfully.")

if __name__ == "__main__":
    main()
