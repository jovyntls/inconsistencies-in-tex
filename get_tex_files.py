import requests
from lxml import html
import os
from utils.logger import Log_level

"""Send a get request and ensure RESPONSE=200"""
def get_request(url, LOGGER):
    response = requests.get(url)
    if response.status_code != 200:
        # Print the response content (JSON, XML, HTML, etc.)
        raise RuntimeError("[get_request]: http response not 200")
    LOGGER.log(Log_level.DEBUG, f"get_request: (success) {url}")
    return response

"""Get the content from a URL using xpath"""
def get_content_from_page(url, xpath, LOGGER):
    response = get_request(url, LOGGER)
    html_source = html.fromstring(response.content)
    try: 
        return html_source.xpath(xpath)[0]
    except Exception as e:
        print(e)
        raise RuntimeError("failed at [get_content_from_html]")

"""[for arxiv] process a HTML element to get the papers"""
def list_item_to_download_links(list_item):
    ARXIV_BASE_URL = 'https://arxiv.org'
    if list_item.tag != 'dt':
        # we only care about <dt></dt>
        return
    a_hrefs = list_item.findall(".//a[@href]")
    arxiv_id_raw, other_elem = a_hrefs[0].text_content(), a_hrefs[-1]
    # validate or throw error
    is_valid =  arxiv_id_raw.startswith("arXiv:") and other_elem.text_content() == 'other' 
    if not is_valid:
        return
    arxiv_id = arxiv_id_raw[6:]
    return arxiv_id, ARXIV_BASE_URL + '/e-print/' + arxiv_id

def download_from_url_and_save(download_url, folder, filename, LOGGER):
    def save_file_to_folder(folder, file_content, filename):
        file_path = os.path.join(folder, filename)
        with open(file_path, 'wb') as file:
            file.write(file_content)
            LOGGER.log(Log_level.DEBUG, f"file written: {file_path}")
    response = get_request(download_url, LOGGER)
    save_file_to_folder(folder, response.content, filename)

def main(num_files, DOWNLOAD_FOLDER, LOGGER):
    # get the links to download
    url = 'https://arxiv.org/list/cs.IT/2308?skip=0&show=' + str(num_files)
    list_of_papers = get_content_from_page(url, '//*[@id="dlpage"]/dl', LOGGER)
    LOGGER.log(Log_level.INFO, f'starting download:\n\tfrom {url}\n\tto {DOWNLOAD_FOLDER}')
    download_links = {}
    for list_item in list_of_papers:
        res = list_item_to_download_links(list_item)
        if res != None:
            arxiv_id, download_url = res
            download_links[arxiv_id] = download_url

    # download and save
    for arxiv_id, link in download_links.items():
        download_from_url_and_save(link, DOWNLOAD_FOLDER, arxiv_id, LOGGER)

    LOGGER.log(Log_level.INFO, f'downloaded: {len(download_links)} papers')
    arxiv_ids = list(download_links.keys())
    LOGGER.log(Log_level.DEBUG, arxiv_ids)

    return arxiv_ids
