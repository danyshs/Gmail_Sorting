import os
import shutil
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime
import logging


def handle_file_operation(file_path, operation, mode="r", content=None):
  try:
    with open(file_path, mode) as file:
      if operation == "read":
        return file.readlines()
      elif operation == "write":
        file.write(content)
      else:
        raise ValueError("Unsupported file operation.")
  except FileNotFoundError:
    raise FileNotFoundError(f"The file {file_path} does not exist.")
  except IOError as e:
    raise IOError(f"Error during file operation on {file_path}: {str(e)}")


def parse_xml_file(file_path):
  try:
    tree = ET.parse(file_path)
    return tree.getroot()
  except ET.ParseError as e:
    raise ValueError(f"XML parsing error in {file_path}: {str(e)}")
  except Exception as e:
    raise Exception(
        f"An unexpected error occurred while parsing {file_path}: {str(e)}")


def get_label_email_pairs(root):
  ns = {"ns": "http://www.w3.org/2005/Atom",
        "apps": "http://schemas.google.com/apps/2006"}
  pairs = {}
  for entry in root.findall("ns:entry", ns):
    label = entry.find('apps:property[@name="label"]', ns)
    email = entry.find('apps:property[@name="from"]', ns)
    if label is not None and email is not None:
      pairs[label.get('value')] = email.get('value')
  return pairs


def update_xml_with_emails(xml_root, emails):
  labels = {}
  print("\n")
  ET.register_namespace('', 'http://www.w3.org/2005/Atom')
  ET.register_namespace('apps', 'http://schemas.google.com/apps/2006')
  for email, tags in emails.items():
    for tag in tags:
      if tag in labels:
        labels[tag] += ' OR ' + email
        print(
            f'Label "{tag}" exists. Appending email "{email}" to it.')
      else:
        labels[tag] = email
        print(
            f'Label "{tag}" does not exist. Creating it with email "{email}".')

      entry = ET.SubElement(xml_root, 'entry', {})
      category = ET.SubElement(
          entry, 'category', attrib={'term': 'filter'})
      category.text = ''
      ET.SubElement(entry, 'title').text = 'Mail Filter'
      ET.SubElement(
          entry, 'id').text = 'tag:mail.google.com,2008:filter:PLACEHOLDER_TEXT'
      ET.SubElement(
          entry, 'updated').text = datetime.now().isoformat() + 'Z'
      content = ET.SubElement(entry, 'content')
      content.text = ''
      ET.SubElement(entry, 'apps:property', {
                    'name': 'from', 'value': email})
      ET.SubElement(entry, 'apps:property', {
                    'name': 'label', 'value': tag})
      ET.SubElement(entry, 'apps:property', {
                    'name': 'shouldArchive', 'value': 'true'})
      ET.SubElement(entry, 'apps:property', {
                    'name': 'shouldNeverSpam', 'value': 'true'})
      ET.SubElement(entry, 'apps:property', {
                    'name': 'sizeOperator', 'value': 's_sl'})
      ET.SubElement(entry, 'apps:property', {
                    'name': 'sizeUnit', 'value': 's_smb'})


def pretty_print_xml(xml_root):
  rough_string = ET.tostring(xml_root, 'utf-8')
  reparsed = minidom.parseString(rough_string)
  return '\n'.join([line for line in reparsed.toprettyxml(indent="   ").split('\n') if line.strip()])


def process_email_updates(input_file: str, old_file: str, output_file: str) -> None:
  try:
    files = [input_file, old_file]
    for file in files:
      if not os.path.exists(file):
        raise FileNotFoundError(f"File {file} does not exist.")

    old_parsed = parse_xml_file(old_file)

    logfile = 'logging_file.log'
    if os.path.exists(logfile):
      os.remove(logfile)
    logging.basicConfig(filename=logfile, level=logging.INFO)

    emails = get_emails_from_update_file(input_file)
    update_xml_with_emails(old_parsed, emails)
    pretty_xml_str = pretty_print_xml(old_parsed)

    temp_file = None
    if os.path.exists(output_file):
      temp_file = 'temp.xml'
      shutil.copy(output_file, temp_file)

    handle_file_operation(output_file, 'write', 'w', pretty_xml_str)

    logging.info(f"Input file: {input_file}, Key-value pairs: {emails}")
    logging.info(
        f"Old file: {old_file}, Key-value pairs: {get_label_email_pairs(old_parsed)}")
    logging.info(f"Output file: {
                 output_file}, Key-value pairs: {get_label_email_pairs(parse_xml_file(output_file))}")
    print("\nLog file " + logfile + " created successfully.")

    if temp_file:
      temp_parsed = parse_xml_file(temp_file)

      print(f"\nComparing original XML files before any changes: {
            old_file} and {temp_file}")
      differences = compare_xml_files(old_file, temp_file)
      print(differences)

      print(f"\nComparing XML files after updates: {
            temp_file} and {output_file}")
      differences = compare_xml_files(temp_file, output_file)
      print(differences)

      logging.info(f"Temp file: {
                   temp_file}, Key-value pairs: {get_label_email_pairs(temp_parsed)}")

      os.remove(temp_file)

    print("XML file updated successfully.")
  except Exception as e:
    print(f"An error occurred: {e}")


def get_emails_from_update_file(update_file):
  emails = {}
  lines = handle_file_operation(update_file, 'read')
  for line in lines:
    try:
      email, tag = line.strip().split(': ')
      emails.setdefault(email, []).append(tag)
    except ValueError:
      print(f"Skipping malformed line: {line.strip()}")
  return emails


def compare_xml_files(file1, file2):
  root1 = parse_xml_file(file1)
  root2 = parse_xml_file(file2)

  pairs1 = get_label_email_pairs(root1)
  pairs2 = get_label_email_pairs(root2)

  additions = {k: v for k, v in pairs2.items() if k not in pairs1}
  deletions = {k: v for k, v in pairs1.items() if k not in pairs2}
  modifications = {k: (pairs1[k], pairs2[k])
                   for k in pairs1 if k in pairs2 and pairs1[k] != pairs2[k]}

  return {'additions': additions, 'deletions': deletions, 'modifications': modifications}


if __name__ == "__main__":
  os.chdir(os.path.dirname(os.path.abspath(__file__)))
  process_email_updates(
      'xmlupdate.txt', 'mailFilters.xml', 'newMailFilters.xml')
