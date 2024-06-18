import os
import re
import xml.etree.ElementTree as ET


def get_emails(filename, tagged_filename):
    """Extract emails from the given files."""
    try:
        with open(filename, 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"File {filename} not found.")
        return []
    start_index = lines.index("BY FREQUENCY\n") + 1
    emails = [line.split(' || ')[0] for line in lines[start_index:]]

    try:
        with open(tagged_filename, 'r') as f:
            tagged_emails = [line.split(': ')[0] for line in f.readlines()]
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
    root = tree.getroot()
    labels = []
    for prop in root.findall(".//apps:property[@name='label']", 
                             namespaces={'apps': 'http://schemas.google.com/apps/2006'}):
        value = prop.get('value')
        if value is not None:
            labels.append(value)

    try:
        with open(tagged_filename, 'r') as f:
            for line in f.readlines():
                tags = line.split(': ')[1].strip().split(', ')
                labels.extend(tags)
    except FileNotFoundError:
        print(f"File {tagged_filename} not found.")
        return []

    if os.path.exists(labels_filename):
        try:
            with open(labels_filename, 'r') as f:
                labels.extend([re.sub(r'^\d+\. ', '', line).strip() for line in f.readlines()])
        except FileNotFoundError:
            print(f"File {labels_filename} not found.")
            return []
    else:
        open(labels_filename, 'w').close()

    return list(set(labels))


def tag_emails(emails, labels, tagged_filename):
    """Tag emails with the given labels."""
    tagged_emails = {}
    for i, email in enumerate(emails, start=1):
        print(f"Tagging email: {email} ({len(emails) - i} email addresses remaining)")
        labels.sort()
        for i, label in enumerate(labels, start=1):
            print(f"{i}. {label}")
        print("0. Define a new label")
        response = input("Choose a number to tag this email or 'n' to skip: ")
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
                with open(tagged_filename, 'a') as f:
                    f.write(f'{email}: {", ".join(tagged_emails[email])}\n')
            except FileNotFoundError:
                print(f"File {tagged_filename} not found.")
                return {}
    return tagged_emails


def main():
    script_dir = os.path.dirname(os.path.realpath(__file__))
    os.chdir(script_dir)

    xmlupdate_file = os.path.join(script_dir, 'xmlupdate.txt')
    labels_file = os.path.join(script_dir, 'labels.txt')

    if not os.path.exists(xmlupdate_file):
        open(xmlupdate_file, 'w').close()

    if not os.path.exists(labels_file):
        open(labels_file, 'w').close()

    emails = get_emails(os.path.join(script_dir, 'output.txt'), xmlupdate_file)
    labels = get_labels(os.path.join(script_dir, 'mailFilters.xml'), xmlupdate_file, labels_file)
    tagged_emails = tag_emails(emails, labels, xmlupdate_file)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nEmail Tagger Script Terminated.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
