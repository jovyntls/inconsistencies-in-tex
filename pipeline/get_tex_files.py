import requests
from lxml import html
import os
from utils.logger import PIPELINE_LOGGER as LOGGER
from config import TEX_FILE_DOWNLOAD_XPATH, NUM_ATTEMPTS, YEAR_AND_MONTH
from constants.arxiv_subjects import SUBJECTS

"""Get the URL to download for each arxiv category (subject)"""
def build_download_url(subject):
    yyyy = '20' + YEAR_AND_MONTH[:2]
    mm = YEAR_AND_MONTH[-2:]
    url = f'https://arxiv.org/list/{subject}/{yyyy}-{mm}?skip=0&show={str(NUM_ATTEMPTS)}'
    return url

"""Send a get request and ensure RESPONSE=200"""
def get_request(url):
    response = requests.get(url)
    if response.status_code != 200:
        # Print the response content (JSON, XML, HTML, etc.)
        raise RuntimeError("[get_request]: http response not 200")
    LOGGER.debug(f"get_request: (success) {url}")
    return response

"""Get the content from a URL using xpath"""
def get_content_from_page(url, xpath):
    response = get_request(url)
    html_source = html.fromstring(response.content)
    try: 
        res = html_source.xpath(xpath)
        if len(res) == 0: 
            LOGGER.debug(f'no papers found for {url=}')
            return []
        else: return res[0]
    except Exception as e:
        print(e)
        raise RuntimeError("failed at [get_content_from_html]")

"""[for arxiv] process a HTML element to get the papers"""
def list_of_papers_to_download_links(element_list):
    ARXIV_BASE_URL = 'https://arxiv.org'
    # we only care about <dt></dt>
    list_of_papers = [item for item in element_list if item.tag == 'dt']
    download_links = {}
    for list_item in list_of_papers:
        a_hrefs = list_item.findall(".//a[@href]")
        arxiv_id_raw, other_elem = a_hrefs[0].text_content().strip(), a_hrefs[-1].text_content().strip()
        # validate or throw error
        is_valid =  arxiv_id_raw.startswith("arXiv:") and other_elem == 'other' 
        if not is_valid: continue
        arxiv_id = arxiv_id_raw[6:]
        url = ARXIV_BASE_URL + '/e-print/' + arxiv_id
        download_links[arxiv_id] = url
        LOGGER.debug(f'collected link: {arxiv_id=} {url=}')
        if len(download_links) == NUM_ATTEMPTS: break
    return download_links

def get_download_links(url):
    elem_list_of_papers = get_content_from_page(url, TEX_FILE_DOWNLOAD_XPATH)
    return list_of_papers_to_download_links(elem_list_of_papers)

def download_from_url_and_save(download_url, folder, filename):
    def save_file_to_folder(folder, file_content, filename):
        file_path = os.path.join(folder, filename)
        with open(file_path, 'wb') as file:
            file.write(file_content)
            LOGGER.debug(f"file written: {file_path}")
    response = get_request(download_url)
    save_file_to_folder(folder, response.content, filename)

def get_download_links_by_subject():
    download_links = {}
    subjects = SUBJECTS.keys()

    # get the links to download
    LOGGER.info('collecting urls for papers...')
    for subject in subjects:
        url = build_download_url(subject)
        LOGGER.debug(f'getting papers: from {url}')
        subject_download_links = get_download_links(url)
        download_links.update(subject_download_links)
    LOGGER.info(f'collected {len(download_links)} urls for papers in {len(subjects)} subjects')
    return download_links

def main(DOWNLOAD_FOLDER, download_by_arxiv_ids):
    # collect links
    download_links = {}
    if len(download_by_arxiv_ids) == 0:
        download_links = get_download_links_by_subject()
    else:
        download_links = { arxiv_id: f'https://arxiv.org/e-print/{arxiv_id}' for arxiv_id in download_by_arxiv_ids }

    # download and save
    LOGGER.info(f'starting downloads...')
    for arxiv_id, link in download_links.items():
        LOGGER.debug(f'starting download:\n\tfrom {link}\n\tto {DOWNLOAD_FOLDER}')
        download_from_url_and_save(link, DOWNLOAD_FOLDER, arxiv_id)
    LOGGER.info(f'downloaded: {len(download_links)} papers')
    arxiv_ids = list(download_links.keys())
    LOGGER.debug(arxiv_ids)

    return arxiv_ids
