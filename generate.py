import json
import os
import base64
import re
import requests
from collections import defaultdict

# Define the URL to the hosted licenses file
licenses_url = "https://raw.githubusercontent.com/spdx/license-list-data/main/json/licenses.json"

# Define the paths to the SBOM files directory and HTML template file
sbom_directory_path = os.path.join(os.path.dirname(__file__), 'sboms')
template_file_path = os.path.join(os.path.dirname(__file__), 'template.html')

# Load HTML template from the file
with open(template_file_path, 'r') as template_file:
    html_template = template_file.read()

# Download and load licenses information from the URL
response = requests.get(licenses_url)
if response.status_code != 200:
    raise Exception(f"Failed to download licenses data: {response.status_code}")

licenses_data = response.json()

# Extract the licenses list from the licenses_data
licenses_list = licenses_data.get("licenses", [])

# Create a dictionary for quick lookup of licenses by licenseId
licenses_lookup = {license['licenseId']: license for license in licenses_list}

# Function to decode base64 content and extract license URL
def decode_base64_and_extract_url(encoded_text):
    decoded_text = base64.b64decode(encoded_text).decode('utf-8')
    # Match URLs starting with either http or https
    url_pattern = re.compile(r'https?://[^\s]+|http://[^\s]+')
    urls = url_pattern.findall(decoded_text)
    return urls[0] if urls else 'N/A'

# Dictionary to store unique components
unique_components = defaultdict(dict)

# Scan all JSON files in the specified directory
for sbom_filename in os.listdir(sbom_directory_path):
    if sbom_filename.endswith('.json'):
        sbom_file_path = os.path.join(sbom_directory_path, sbom_filename)
        with open(sbom_file_path, 'r') as sbom_file:
            try:
                sbom = json.load(sbom_file)
                for component in sbom.get('components', []):
                    component_group = component.get('group', 'Unknown')
                    component_name = component.get('name', 'Unknown')
                    component_version = component.get('version', 'Unknown')
                    component_key = (component_group, component_name, component_version)
                    if component_key not in unique_components:
                        unique_components[component_key] = component
            except json.JSONDecodeError:
                print(f"Error reading {sbom_file_path}, not a valid JSON file.")

# Initialize the license compliance text and HTML
compliance_text = []
compliance_html = []

# Extract and format license information from unique components
for component_key, component in sorted(unique_components.items()):
    component_group, component_name, component_version = component_key
    full_component_name = f"{component_group}:{component_name}"
    licenses = component.get('licenses', [])
    license_info_list = []
    license_info_text_list = []

    if licenses:
        for license_entry in licenses:
            license_info = license_entry.get('license', {})
            license_id = license_info.get('id', None)
            license_name = license_info.get('name', 'Unknown')

            # Determine license URL
            if license_id in licenses_lookup:
                license_data = licenses_lookup[license_id]
                license_url = license_data.get('reference', 'N/A')
                license_name = license_data.get('name', license_id)
            else:
                license_url = license_info.get('url', 'N/A')
                if not license_id:
                    license_id = license_name  # Use license name if ID is not available

            license_info_list.append(f"License: {license_id}, <a href='{license_url}'>{license_url}</a>")
            license_info_text_list.append(f"License: {license_id}, {license_url}")

        license_info_str = "; ".join(license_info_list)
        license_info_text_str = "; ".join(license_info_text_list)
        component_info = (
            f"Component: {full_component_name}, Version: {component_version}, {license_info_text_str}"
        )
        component_html = (
            f"<tr><td>{full_component_name}</td><td>{component_version}</td><td>{license_info_str}</td></tr>"
        )
    else:
        component_info = (
            f"Component: {full_component_name}, Version: {component_version}, "
            "License: None, URL: N/A"
        )
        component_html = (
            f"<tr><td>{full_component_name}</td><td>{component_version}</td><td>License: None, URL: N/A</td></tr>"
        )

    compliance_text.append(component_info)
    compliance_html.append(component_html)

# Join the license information into a single string
compliance_txt_content = "\n".join(compliance_text)
compliance_html_content = "\n".join(compliance_html)

# Define the output file paths
output_txt_file_path = os.path.join(os.path.dirname(__file__), 'license_compliance.txt')
output_html_file_path = os.path.join(os.path.dirname(__file__), 'license_compliance.html')

# Write to license_compliance.txt
with open(output_txt_file_path, 'w') as compliance_file:
    compliance_file.write(compliance_txt_content)

# Insert the compliance data into the HTML template
html_output = html_template.replace("{{compliance_html_content}}", compliance_html_content)

# Write the final HTML to the output file
with open(output_html_file_path, 'w') as compliance_file:
    compliance_file.write(html_output)

print("license_compliance.txt and license_compliance.html created successfully.")
