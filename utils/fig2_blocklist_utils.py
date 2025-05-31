import numpy as np
import matplotlib.pyplot as plt
import requests
from requests.auth import HTTPBasicAuth
from bs4 import BeautifulSoup
import json
import socket
import concurrent.futures


###################### CENSYS QUERY PROCESSING FUNCTIONS ######################

def get_dns_names_from_query(data):
    count = 0
    dns_names = []
    for i in range(len(data['result']['hits'])):
        if 'dns' in data['result']['hits'][i].keys():
            result = data['result']['hits'][i]['dns']['reverse_dns']['names']
            dns_names.append(result)
            count += len(result)

    return dns_names

def get_ips_from_query(data):
    count = 0
    ips = []
    for i in range(len(data['result']['hits'])):
        if 'dns' in data['result']['hits'][i].keys():
            result = data['result']['hits'][i]['ip']
            ips.append(result)
            count += len(result)
    return ips


def flatten_array(arr):
    for item in arr:
        if isinstance(item, list):
            yield from flatten_array(item)
        else:
            yield item


###################### BLOCKLIST PROCESSING FUNCTIONS ######################

def convert_dns_files_to_ip(input_dns_file,output_ip_file):

    # Read and load the JSON file
    with open(input_dns_file, "r") as f:
        blocklist_pharmacy_safe = [line.strip() for line in f]


    def task(host):
        try:
            ip_address = socket.gethostbyname(host)
            print(f"The IP address of {host} is: {ip_address}")
            return ip_address
        except socket.gaierror as e:
            print(f"Error resolving hostname {host}: {e}")
            return ''


    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Submit tasks to the executor
        futures = [executor.submit(task, host) for host in blocklist_pharmacy_safe]
        # Collect the results
        results = [future.result() for future in concurrent.futures.as_completed(futures)]


    filtered_arr = [s for s in results if s != '']
    with open(output_ip_file,'w') as f:
        for line in filtered_arr:
            f.write(line + '\n')



def fetch_illegal_pharmacies():
    url = 'https://safe.pharmacy/not-recommended-sites/'
    headers = {
        'User-Agent': 'Mozilla/5.0'
    }

    # Send a GET request to the URL
    response = requests.get(url, headers=headers)
    response.raise_for_status()  # Raise an exception for HTTP errors

    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find all anchor tags that contain the pharmacy URLs
    pharmacy_links = soup.find_all('a', href=True)

    # Extract the text from each link, which represents the pharmacy URL
    pharmacies = [link.get_text(strip=True).split('/')[0] for link in pharmacy_links if link.get_text(strip=True)]

    return pharmacies


def read_ip_blocklists(file,offset=0):

    with open(file) as f:
        lines = f.readlines()

    lines = lines[offset:]
    ret = [line.replace('\n','').split('/')[0] for line in lines]
    return ret


def get_shared_entries(list1,list2):

    # Convert to sets
    set1 = set(list1)
    set2 = set(list2)

    # Find intersection
    shared = list(set1.intersection(set2))
    return shared