# License Compliance Report Generator

This script generates license compliance reports from SBOM (Software Bill of Materials) JSON files. It retrieves and processes license information from SPDX license and exception lists.

## Prerequisites

- Python 3.6 or later
- `requests` library

You can install the required library using pip:

```bash
pip install requests
```

## Usage

1. **Place your SBOM JSON files in a directory**: By default, the script looks for SBOM JSON files in a directory named `sboms`. You can specify a different directory using the `--sbom-dir` argument.

2. **Mapping file (optional)**: If you have a custom JSON file to map complex license names to SPDX IDs, you can specify it using the `--mapping-file` argument.

3. **Run the script**: Execute the script with the appropriate arguments.

```bash
python generate.py --sbom-dir <path_to_sbom_directory> --mapping-file <path_to_mapping_file>
```

Example:

```bash
python generate.py --sbom-dir ../build/reports --mapping-file mapping.json
```

## Output

The script generates the following files in the current directory:

- `license_compliance.txt`: A text report of the license compliance.
- `license_compliance.html`: An HTML report of the license compliance.
- `licenses_text.txt`: A text file containing the full text of the licenses.
- `licenses_text.html`: An HTML file containing the full text of the licenses.

## Script Details

### Functions

- **fetch_data(url)**: Fetches JSON data from the provided URL.
- **load_sbom_files(directory)**: Loads SBOM JSON files from the specified directory.
- **load_license_name_to_id_map(json_file)**: Loads the license name to SPDX ID mapping from a JSON file.
- **extract_vcs_url(component)**: Extracts the VCS URL from the component's external references.
- **resolve_relative_url(base_url, relative_url)**: Resolves a relative URL against a base URL.
- **get_license_reference_url(license_id, licenses_lookup, exceptions_lookup)**: Gets the reference URL for a license or exception.
- **get_full_license_text(details_url, is_exception=False)**: Fetches the full text of a license or exception.
- **process_individual_license(license, licenses_lookup, license_texts, exceptions_lookup)**: Processes an individual license.
- **process_license_expression(license, licenses_lookup, license_texts, exceptions_lookup)**: Processes a license expression.
- **process_license_name(license, licenses_lookup, license_texts, exceptions_lookup)**: Processes a license by name.
- **process_license(license, licenses_lookup, license_texts, exceptions_lookup)**: Determines and processes the type of license (individual, expression, or name).
- **format_license_info(license_ids, license_names, license_references, exceptions, exceptions_lookup)**: Formats the license and exception information.
- **process_component(key, component, licenses_lookup, license_texts, exceptions_lookup)**: Processes a component and extracts license information.
- **generate_reports(components, licenses_lookup, exceptions_lookup)**: Generates the license compliance reports.
- **write_text_report(filename, data)**: Writes the license compliance text report.
- **write_html_report(filename, data)**: Writes the license compliance HTML report.
- **write_license_texts(text_filename, html_filename, license_texts)**: Writes the full text of the licenses and exceptions.
- **main()**: The main function that orchestrates the loading of SBOM files, fetching license data, processing components, and generating reports.

### Argument Parser

- `--sbom-dir`: Directory containing SBOM JSON files (default: `sboms`).
- `--mapping-file`: Optional JSON file to map complex license names to SPDX IDs.

## Example Mapping File

```json
{
  "The GNU General Public License, v2 with Universal FOSS Exception, v1.0": ["GPL-2.0", "Universal-FOSS-exception-1.0"]
}
```

This mapping file helps in resolving complex license names to their corresponding SPDX IDs.
