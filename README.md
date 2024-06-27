# Gmail Filter Sorting Utility

This Python module provides a convenient tool for creating a bunch of handy Gmail Filters.
**Run.py** is the main Operation Center, which is the only file you need to run.

**NOTE: You must complete your GMail API OAuth2 Setup
(To obtain your credentials.json file, which must be moved to your cloned directory)**

A useful guide for that can be found [here](https://mailtrap.io/blog/send-emails-with-gmail-api/)

## Project Overview

The project consists of several Python scripts designed to automate specific tasks related to managing email data. Each script serves a distinct purpose:

- **email\_fix.py**: Reads the metadata of your top n chunk of emails [default: 40,000],and indexes all unique email addresses. [This operation takes a considerable amount of time.]
- **tag\_all\_emails.py**: Allows you to **manually** tag each unique email address for proper categorization [and sub-categorization].
- **generate\_filter\_xmls.py**: Generates an XML file that can be imported in Gmail to apply filters based on the criteria that you set.

* * *
* * *

## Some Pre-Requisite Work

### MISSION 1: SET UP YOUR OAUTH2

Option 1: Follow [this guide](https://mailtrap.io/blog/send-emails-with-gmail-api/) until the end of step 3

Option 2: TBA

### MISSION 2: **Download your mailFilters.xml from Gmail**

1. Click the Settings Icon on the top-right of the screen

![image](https://github.com/danyshs/Gmail_Sorting/assets/170024365/a30d959c-55d6-43a7-b296-cd55044b4bb5)
* * *

2. Select "See all Settings"

![image](https://github.com/danyshs/Gmail_Sorting/assets/170024365/809a27a7-6909-4219-ad3a-3b79fe35cb99)
* * *

3. Select "Filters and blocked Addresses"

![image](https://github.com/danyshs/Gmail_Sorting/assets/170024365/f60953c5-f11e-4b1b-924f-4d3cfc13d213)
* * *

4. Then, at the bottom of the page, Select All, and Export.

![image](https://github.com/danyshs/Gmail_Sorting/assets/170024365/fdc49755-b6d0-4812-abc7-f48717d07eb1)
* * *
* * *

## Getting Started

1. **Clone the Repository**: Clone this repository to your local machine using:

        git clone https://github.com/danyshs/Gmail_Sorting.git

2. **Navigate to the Directory**: Enter the directory where the scripts are located:

        cd Gmail_Sorting

3. **Run the Script**: Execute the main script `run.py`. This script guides you through the process of selecting and running the desired automation script:

        python run.py

    Follow the prompts to choose which task you want to execute.

## Usage

- Upon running `run.py`, you will see a list of available scripts along with their descriptions.
- Enter the number corresponding to the script you wish to run.

# 1 -> **email\_fix.py**: Reads the metadata of your top n chunk of emails, lists unique email addresses sorted alphabetically and by frequency, stores it in a text file) [Takes a long while]

# 2 -> **tag\_all\_emails.py**: Allows you to **manually** tag each unique email address for proper categorization [and sub-categorization]. Requires the output file of #1

# 3 -> **generate\_filter\_xmls.py**: Generates an XML file that can be imported in Gmail to apply filters based on the criteria that you set. Requires the output file of #2

* * *

These have been separated into 3 separate files for the user's ease.

- #1 takes a while and can be set to run at a time one isn't using the machine

- #2 can be done in small bursts to fully categorize emails within categories you have, and you can keep creating new categories as you go

- #3 is instant, and adds to your existing `mailFilters.xml` file

## Requirements

- Python 3.x
- Google OAuth2 Setup (To obtain both a credentials.json file, which must be moved to your cloned directory)

## Contributing

Contributions are welcome! If you find any issues or have suggestions for improvements, please feel free to open an issue or a pull request.

## License

This project is (to be) licensed under the MIT License (when possible).
Feel free to use it as you see fit.

## Acknowledgments

- This script runner was developed to ease the automation of emails into folders within Gmail.
- Inspired by the need for efficient handling of large datasets in email processing workflows.

* * *
