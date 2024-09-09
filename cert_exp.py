import socket
import ssl
import json
import os
from datetime import datetime

DOMAIN_LIST = "domains.json"

def load_domain_list():
    """load the list of domains from a JSON file,"""
    if os.path.exists(DOMAIN_LIST):
        with open(DOMAIN_LIST, "r") as file:
            return json.load(file)
    return []

def get_ssl_expiration_date(domain):
    # Set up a connection to the domain on port 443
    context = ssl.create_default_context()
    
    try:
        with socket.create_connection((domain, 443)) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                # Get the certificate
                cert = ssock.getpeercert()
                
                # Extract the expiration date
                expiration_date_str = cert['notAfter']
                
                # Convert the expiration date to a datetime object
                expiration_date = datetime.strptime(expiration_date_str, "%b %d %H:%M:%S %Y %Z")
                
                return expiration_date
    except Exception as e:
        return f"Error fetching SSL certificate for {domain}: {e}"

def check_domains_ssl_expiration(domains):
    for domain in domains:
        expiration_date = get_ssl_expiration_date(domain)
        if isinstance(expiration_date, datetime):
            print(f"Domain: {domain}, SSL Certificate Expiration Date: {expiration_date}")
        else:
            print(f"Domain: {domain}, Error: {expiration_date}")

# Example usage with a list of domains
domains_to_check = load_domain_list()
check_domains_ssl_expiration(domains_to_check)
