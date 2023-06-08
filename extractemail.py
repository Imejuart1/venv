import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import re
from bs4 import BeautifulSoup

options = webdriver.ChromeOptions()
# options.add_argument('--headless')  # run Chrome in headless mode
options.add_argument('--disable-gpu')  # Disable GPU acceleration (some websites block access from GPUs)
options.add_argument('--no-sandbox')  # Disable sandbox mode(some websites block access from sandboxed environments)

"""
brave_path = "C:/Program Files/BraveSoftware/Brave-Browser/Application/brave.exe"  # path to Brave browser executable
options.binary_location = brave_path
"""

chromedriver_path = os.path.join(os.getcwd(), 'chromedriver')  # path to ChromeDriver executable
service = Service(executable_path=chromedriver_path)

# start the webdriver with the Service object
driver = webdriver.Chrome(service=service, options=options)

# countries
country = "UK, USA, and Germany"

# var
distributor_links = set()


# Function to search for vendor website by product name
def get_manufacturer_website(product):
    # define the URL to search for the product
    url = "https://google.com/search?q=" + product + " website"

    # send a GET request to the URL
    driver.get(url)
    driver.implicitly_wait(600)

    # find the first search result link that matches the vendor pattern
    search_result_link = driver.find_element(By.CSS_SELECTOR, "div.g")

    # get the vendor URL from the href attribute of the anchor tag
    if search_result_link:
        # Get the href attribute of the anchor tag
        link = search_result_link.find_element(By.TAG_NAME, "a")
        vendor_url = link.get_attribute("href")
    else:
        vendor_url = None

    return vendor_url


# Function to search for distributors website by product name and country
def get_distributors_website(product):
    queries = ["Distributors of " + product, "Distributors of " + product + " in " + country]

    # Count variable to keep track of query loop
    count = 1

    for query in queries:  # loop through queries
        for page in range(3):  # loop over first 3 pages of search results
            url = f"https://www.google.com/search?q={query}&start={page * 10}"
            driver.get(url)
            driver.implicitly_wait(10)

            # Get all the search results
            search_results = driver.find_elements(By.CSS_SELECTOR, "div.g")

            # Iterate through the search results and extract the links
            for result in search_results:
                try:
                    # Extract the link and add it to the list
                    link = result.find_element(By.TAG_NAME, "a")
                    link_href = link.get_attribute("href")
                    if count < 10 and not link_href.endswith('.pdf'):
                        distributor_links.add(link_href)
                        count += 1
                    else:
                        count = 0
                        break
                except:
                    pass
    return distributor_links


# Function to decode email
def decode_email(encoded_email):
    """Decode the encoded email address"""
    # Remove the "data-cfemail" attribute from the span tag
    pattern = re.compile(r'data-cfemail="[a-z0-9]+')
    encoded_email = pattern.sub('', encoded_email)

    # Convert the hexadecimal values to ASCII characters
    key = int(encoded_email[:2], 16)
    decoded_email = ''.join([chr(int(encoded_email[i:i + 2], 16) ^ key) for i in range(2, len(encoded_email), 2)])

    return decoded_email


# Function to get email from "soup"
def get_email(links_, soup_):
    for link in links_:
        # Check if the link contains an email address
        if link.has_attr('href') and 'mailto:' in link['href']:
            return link['href'][7:]

    # If no email addresses were found in the links, check for an email address span tag
    email_span = soup_.find('span', {'class': '__cf_email__'})
    if email_span:
        # Decode the email address using Cloudflare's email obfuscation technique
        encoded_email = email_span['data-cfemail']
        pattern = re.compile(r'data-cfemail="[a-z0-9]+')
        encoded_email = pattern.sub('', encoded_email)
        key = int(encoded_email[:2], 16)
        decoded_email = ''.join(
            [chr(int(encoded_email[i:i + 2], 16) ^ key) for i in range(2, len(encoded_email), 2)])
        return decoded_email

    # If no email address span tag was found, use regex
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    email_tags = soup_.find_all(re.compile(email_pattern))

    for tag in email_tags:
        found_emails = re.findall(email_pattern, tag)
        if found_emails:
            return found_emails[0]


# Function to navigate vendor and distributors websites to extract emails
def get_vendor_emails(product_name):
    email_lists = set()

    try:
        print("Getting Manufacturer and Distributor's websites for " + product_name + "...")
        manufacturer_link = get_manufacturer_website(product_name)
        distributor_link = get_distributors_website(product_name)
        print("Gotten...")
    except:
        print("Error loading websites...")
    else:
        print("Extracting emails from the websites...")
        links = [manufacturer_link] + list(distributor_link)
        # to remove duplicates from list
        links = list(set(links))

        for website_link in links:
            # Load the website and wait for it to fully load
            try:
                driver.get(website_link)
                driver.implicitly_wait(600)
            except:
                continue
            else:
                # Get the page source and parse it with BeautifulSoup
                page_source = driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')
                all_links = []

                for link in soup.find_all("a", href=True):
                    # Append to list if new link contains original link
                    if str(link["href"]).startswith((str(website_link))) or link["href"].startswith('http'):
                        all_links.append(link["href"])

                    # Include all href that do not start with website link but with "/"
                    if str(link["href"]).startswith("/"):
                        if link["href"] not in all_links:
                            link_with_www = website_link + link["href"][1:]
                            all_links.append(link_with_www)

                if all_links:
                    list_links = [all_links[0]]

                    counts = 0
                    for link in all_links:
                        if 'contact' in link.lower():
                            list_links.append(link)
                            counts += 1
                            if counts == 3:
                                break

                    # Check each link for an email address
                    # keeps track of weblinks with contact in them
                    count = 0
                    email = None
                    if not email:
                        for weblink in list_links:
                            count += 1
                            try:
                                driver.get(weblink)
                                driver.implicitly_wait(600)

                            except:
                                print("Error loading " + weblink + " subpage.")
                                continue

                            else:
                                # get the subpage source and parse it with BeautifulSoup
                                page_source = driver.page_source
                                soup = BeautifulSoup(page_source, 'html.parser')

                                # Find all anchor tags on the page
                                links = soup.find_all('a')
                                if get_email(links, soup):
                                    email = get_email(links, soup).split("?")[0]
                                    email_lists.add(email)
        print("Gotten... or not :)")
        return email_lists

    driver.quit()
    return email_lists


# Example usage
#product_n = 'Wattco Fuel Oil Heater'
#emails_list = get_vendor_emails(product_n)
#print(emails_list)