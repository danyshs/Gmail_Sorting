import os
import re
import xml.etree.ElementTree as ET


def get_emails(filename, tagged_filename):
  """Extract emails from the given files."""
  try:
    with open(filename, "r", encoding="utf-8") as f:
      lines = f.readlines()
  except FileNotFoundError:
    print(f"File {filename} not found.")
    return []

  start_index = lines.index("BY FREQUENCY\n") + 1
  emails = [line.split(" || ")[0]
            for line in lines[start_index:] if " || " in line]

  try:
    with open(tagged_filename, "r", encoding="utf-8") as f:
      tagged_emails = [line.split(": ")[0] for line in f.readlines()]
  except FileNotFoundError:
    print(f"File {tagged_filename} not found.")
    return []

  return [email for email in emails if email not in tagged_emails]


def get_labels(filename, tagged_filename, labels_filename):
  """Extract labels from the given files."""
  try:
    tree = ET.parse(filename)
  except ET.ParseError:
    print(f"Error parsing XML file {filename}.")
    return []
  except FileNotFoundError:
    print(f"File {filename} not found.")
    return []

  root = tree.getroot()
  labels = []
  for prop in root.findall('.//apps:property[@name="label"]', namespaces={'apps': 'http://schemas.google.com/apps/2006'}):
    value = prop.get("value")
    if value is not None:
      labels.append(value)

  try:
    with open(tagged_filename, "r", encoding="utf-8") as f:
      for line in f.readlines():
        tags = line.split(": ")[1].strip().split(", ")
        labels.extend(tags)
  except FileNotFoundError:
    print(f"File {tagged_filename} not found.")
    return []

  if os.path.exists(labels_filename):
    try:
      with open(labels_filename, "r", encoding="utf-8") as f:
        labels.extend([re.sub(r"^\d+\. ", "", line).strip()
                      for line in f.readlines()])
    except FileNotFoundError:
      print(f"File {labels_filename} not found.")
      return []
  else:
    open(labels_filename, "w", encoding="utf-8").close()

  return list(set(labels))


def print_labels_in_columns(labels, num_columns=3):
  """Print labels in a grid format with specified number of columns."""
  # Calculate maximum length of each label
  max_label_len = max(len(f"{i + 1}. {label}")
                      for i, label in enumerate(labels))
  col_width = max_label_len + 2  # Add padding for spacing

  # Calculate number of rows required
  num_rows = (len(labels) + num_columns - 1) // num_columns

  for row in range(num_rows):
    line = ""
    for col in range(num_columns):
      index = row + col * num_rows
      if index < len(labels):
        line += f"{index + 1}. {labels[index]:{col_width}}"
    print(line.strip())


def tag_emails(emails, labels, tagged_filename, subjects):
  """Tag emails with the given labels."""
  tagged_emails = {}
  for i, email in enumerate(emails, start=1):
    email_subjects = subjects.get(email, [])
    subject_example = f"\nSubjects:\n - " + \
        "\n - ".join(email_subjects) if email_subjects else ""
    print(f"Tagging email: {email}{subject_example}\n({
          len(emails) - i} email addresses remaining)")

    labels.sort()
    print_labels_in_columns(labels, num_columns=3)
    print("0. Define a new label")
    response = input('Choose a number to tag this email or "n" to skip: ')

    if response.isdigit():
      if int(response) == 0:
        new_label = input("Enter the new label: ")
        labels.append(new_label)
        response = str(len(labels))
      if email in tagged_emails:
        tagged_emails[email].append(labels[int(response) - 1])
      else:
        tagged_emails[email] = [labels[int(response) - 1]]
      try:
        with open(tagged_filename, "a", encoding="utf-8") as f:
          f.write(f"{email}: {', '.join(tagged_emails[email])}\n")
      except FileNotFoundError:
        print(f"File {tagged_filename} not found.")


def extract_subjects(filename):
  """Extract email subjects from the given file."""
  try:
    with open(filename, "r", encoding="utf-8") as f:
      lines = f.readlines()
  except FileNotFoundError:
    print(f"File {filename} not found.")
    return {}

  start_index = lines.index("BY FREQUENCY\n") + 1
  subjects = {}
  current_email = None
  current_subjects = []

  for line in lines[start_index:]:
    if " || " in line:
      if current_email:
        subjects[current_email] = current_subjects
      parts = line.split(" || ")
      current_email = parts[0]
      if " || Subjects: " in line:
        subject_parts = line.split(" || Subjects: ")
        current_subjects = subject_parts[1].strip().split(" | ")
      else:
        current_subjects = []
    else:
      current_subjects.append(line.strip())

  if current_email:
    subjects[current_email] = current_subjects

  return subjects


def main():
  script_dir = os.path.dirname(os.path.realpath(__file__))
  os.chdir(script_dir)

  xmlupdate_file = os.path.join(script_dir, "xmlupdate.txt")
  labels_file = os.path.join(script_dir, "labels.txt")

  if not os.path.exists(xmlupdate_file):
    open(xmlupdate_file, "w", encoding="utf-8").close()

  if not os.path.exists(labels_file):
    open(labels_file, "w", encoding="utf-8").close()

  emails = get_emails(os.path.join(script_dir, "output.txt"), xmlupdate_file)
  labels = get_labels(os.path.join(
      script_dir, "mailFilters.xml"), xmlupdate_file, labels_file)
  subjects = extract_subjects(os.path.join(script_dir, "output.txt"))
  tag_emails(emails, labels, xmlupdate_file, subjects)


if __name__ == "__main__":
  try:
    main()
  except KeyboardInterrupt:
    print("\nEmail Tagger Script Terminated.")
