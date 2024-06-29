import os
import re
import xml.etree.ElementTree as ET


def get_emails(filename, tagged_filename):
  """Extract emails from the given files."""
  emails = []
  if os.path.getsize(filename) != 0:
    try:
      with open(filename, "r", encoding="utf-8") as f:
        lines = f.readlines()
    except FileNotFoundError:
      print(f"File {filename} not found.")
      return []
    start_index = lines.index("BY FREQUENCY\n") + 1
    emails = [line.split(" || ")[0].split("||")[0].strip()
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
  labels = []
  try:
    tree = ET.parse(filename)
    root = tree.getroot()
    labels.extend(
        prop.get("value") for prop in root.findall('.//apps:property[@name="label"]', namespaces={'apps': 'http://schemas.google.com/apps/2006'})
        if prop.get("value")
    )
  except (ET.ParseError, FileNotFoundError):
    print(f"Error reading XML file {filename}.")

  try:
    with open(tagged_filename, "r", encoding="utf-8") as f:
      for line in f.readlines():
        tags = line.split(": ")[1].strip().split(", ")
        labels.extend(tags)
  except FileNotFoundError:
    print(f"File {tagged_filename} not found.")

  if os.path.exists(labels_filename):
    try:
      with open(labels_filename, "r", encoding="utf-8") as f:
        labels.extend(re.sub(r"^\d+\. ", "", line).strip()
                      for line in f.readlines())
    except FileNotFoundError:
      print(f"File {labels_filename} not found.")
  else:
    open(labels_filename, "w", encoding="utf-8").close()

  return list(set(labels))


def print_labels_in_columns(labels, num_columns=3):
  """Print labels in a grid format with specified number of columns."""
  max_label_len = max(len(f"{i + 1}. {label}")
                      for i, label in enumerate(labels))
  col_width = max_label_len + 2  # Add padding for spacing

  num_rows = (len(labels) + num_columns - 1) // num_columns

  for row in range(num_rows):
    line = ""
    for col in range(num_columns):
      index = row + col * num_rows
      if index < len(labels):
        line += f"{index + 1}. {labels[index]:{col_width}}"
    print(line.strip())


def extract_subjects(filename):
  subjects = {}
  frequencies = {}

  try:
    with open(filename, "r", encoding="utf-8") as f:
      lines = f.readlines()
  except FileNotFoundError:
    print(f"File {filename} not found.")
    return subjects, frequencies

  try:
    start_index = lines.index("BY FREQUENCY\n") + 1
  except ValueError:
    print(f"Header 'BY FREQUENCY' not found in {filename}.")
    return subjects, frequencies

  current_email = None
  current_subjects = []

  for line in lines[start_index:]:
    if " || Subjects: " in line:
      if current_email:
        subjects[current_email] = current_subjects
      email, subject_part = line.split(" || Subjects: ", 1)
      my_email, freq = email.split("||")
      my_email = my_email.strip()
      freq = freq.strip()
      current_email = my_email.strip()
      frequencies[current_email] = freq
      current_subjects = subject_part.strip().split(" | ")
    elif " || " in line:
      if current_email:
        subjects[current_email] = current_subjects
      email, _ = line.split(" || ", 1)
      my_email, freq = email.split("||")
      my_email = my_email.strip()
      freq = freq.strip()
      current_email = my_email.strip()
      frequencies[current_email] = freq
      current_subjects = []
    else:
      current_subjects.append(line.strip())

  if current_email:
    subjects[current_email] = current_subjects

  return subjects, frequencies


def tag_emails(emails, labels, tagged_filename, subjects, frequencies):
  """Tag emails with the given labels."""
  tagged_emails = {}
  for i, email in enumerate(emails, start=1):
    email_subjects = subjects.get(email, [])
    email_freq = frequencies.get(email, "N/A")
    subject_example = "\nSubjects:\n - " + \
        "\n - ".join(email_subjects) if email_subjects else ""
    print(f"\nTagging email: {email} (FREQ: {email_freq}){
          subject_example}\n({len(emails) - i} email addresses remaining)")

    labels.sort()
    print_labels_in_columns(labels, num_columns=3)
    print("0. Define a new label")

    while True:
      response = input(
          'Choose a number to tag this email or "n" to skip: ')
      if response == "n" or (response.isdigit() and 0 <= int(response) <= len(labels)):
        break
      else:
        print(f"Invalid input. Please enter a number between 0 and {
              len(labels)} or 'n' to skip.")

    if response.isdigit() and int(response) <= len(labels):
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
      except IOError as e:
        print(f"An IOError occurred: {e}")


def main():
  script_dir = os.path.dirname(os.path.realpath(__file__))
  os.chdir(script_dir)

  xmlupdate_file = os.path.join(script_dir, "xmlupdate.txt")
  labels_file = os.path.join(script_dir, "labels.txt")
  output_file = os.path.join(script_dir, "sorted_emails.txt")

  if not os.path.exists(output_file):
    print(
        f"File {output_file} not found. Please provide the sorted_emails.txt file.")
    return

  for file in [xmlupdate_file, labels_file]:
    if not os.path.exists(file) or os.path.getsize(file) == 0:
      with open(file, "w", encoding="utf-8") as f:
        pass

  emails = get_emails(output_file, xmlupdate_file)
  if not emails:
    print("No emails to process.")
    return

  labels = get_labels("mailFilters.xml", xmlupdate_file, labels_file)
  subjects, frequencies = extract_subjects(output_file)
  tag_emails(emails, labels, xmlupdate_file, subjects, frequencies)


if __name__ == "__main__":
  try:
    main()
  except KeyboardInterrupt:
    print("\nEmail Tagger Script Terminated.")
