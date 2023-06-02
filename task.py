import argparse
import csv
import grequests
import asyncio
from playwright.async_api import async_playwright

search_url = "https://api.bing.microsoft.com/v7.0/search"

parser = argparse.ArgumentParser(description='This finds LinkedIn urls for given companies in a CSV')
parser.add_argument('f', metavar='filename', help='Path for the input CSV')
parser.add_argument('k', help='Key for Bing Search API')
parser.add_argument('--header', help='Input file has header', action='store_true', default=False)
parser.add_argument('-o', metavar='output', help='Path of LinkedIn urls output CSV', default='output.csv')
parser.add_argument('-n', help='Generate other file with the employees count', action='store_true')
args = parser.parse_args()

headers = {"Ocp-Apim-Subscription-Key": args.k}
search_terms = []

with open(args.f, mode='r') as companies_file:
    reader = csv.reader(companies_file)
    # Ignore header
    if args.header:
        next(reader)
    for i, row in enumerate(reader):
        search_term = f'site:www.linkedin.com/company {row[0]}'
        search_terms.append(search_term)

rs = (grequests.get(search_url, headers=headers, params={"q": search}) for search in search_terms)
responses = grequests.map(rs)

with open(args.o, mode='w', newline='') as linked_urls:
    writer = csv.writer(linked_urls,delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
    for response in responses:
        resJson = response.json()
        webPage = resJson['webPages']['value'][0]['url'].rstrip()
        writer.writerow([webPage])

urls = []

with open(args.o, mode='r') as links:
    reader = csv.reader(links)
    for i, row in enumerate(reader):
        urls.append(row[0])


async def getEmployees(urls):
    employees = []
    for i, url in enumerate(urls):
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(url, wait_until='networkidle')
            elem = await page.get_by_text('employees', exact=False).all_inner_texts()
            elem = 0 if len(elem)==0 else elem[0]
            employees.append(elem)
            await browser.close()
    
    with open(args.f, mode='w', newline='') as csv_file:
        writer = csv.writer(csv_file,delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        for i, elem in enumerate(search_terms):
            writer.writerow([elem.split()[1], employees[i]])

asyncio.run(getEmployees(urls))