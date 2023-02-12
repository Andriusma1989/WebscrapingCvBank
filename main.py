import logging
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException
import yaml

# setting counter to count scraped pages
counter = 0


def open_file_with_headers(filename: str, headers: str):
    """Creates a file with provided headers. Separate headers with "," and finish with new line seperator"""
    file = open(filename, 'w', encoding="utf-8-sig")
    file.write(headers)
    return file


def click_element(ch_driver, element: str) -> None:
    """Finds element by ID and clicks on it """
    WebDriverWait(ch_driver, 30).until(EC.element_to_be_clickable((By.ID, element))).click()


def element_text(ch_driver, element: str) -> str:
    """find element by CSS selector and return element text"""
    return ch_driver.find_element(By.CSS_SELECTOR, element).text


def generating_url_list(ch_driver, element: str) -> list:
    """ Finds element by XPATH and returns a list of urls"""
    urls = WebDriverWait(ch_driver, 30).until(EC.visibility_of_all_elements_located((By.XPATH, element)))
    u_list = [url.get_attribute('href') for url in urls]
    return u_list


def get_total_pages(ch_driver, logger) -> int:
    """extracting total pages from the element. If the element index is not found returns 1"""
    try:
        pages = ch_driver.find_elements(By.CSS_SELECTOR, "#main > ul > li:nth-child(1) > ul >li")
        return int(pages[-1].text)
    except IndexError as er:
        logger.error(er)
        return 1


def go_back(ch_driver) -> None:
    """go back from article page to main page"""
    ch_driver.find_element(By.LINK_TEXT, "« Back to job ad list").click()


def next_page(ch_driver, logger) -> None:
    """clicking next page"""
    try:
        ch_driver.find_element(By.LINK_TEXT, "»").click()
    except NoSuchElementException as er:
        # if element is not found. It means there is no further page
        logger.error(er)
        pass
    except ElementClickInterceptedException as er:
        logger.error(er)
        ch_driver.find_element(By.LINK_TEXT, "»").click()


def user_search_input() -> str:
    """Returns User search input"""
    return str(input("Please Enter search input for CV Bank: "))


def scraping(url_list, ch_driver, logger, csv_file):
    """function is opening urls one by one and extracting text from required elements. Writes down the text into csv
                file """
    global counter
    for url in url_list:
        ch_driver.get(url)
        time.sleep(1)
        job_title = element_text(ch_driver, '#jobad_heading1')
        job_location = element_text(ch_driver, '#jobad_location')
        job_company = job_location.split(" - ")[-1]
        job_city = job_location.split(" - ")[0]
        # If element can't be found exceptions are executed.
        # Element text is being changed by empty string and exception is logged
        try:
            job_expiration = element_text(ch_driver, '#jobad_expiration')
        except NoSuchElementException as er:
            job_expiration = " "
            logger.error(er)
        try:
            job_salary = \
                element_text(ch_driver, 'span.salary_amount') + " " + \
                element_text(ch_driver, 'span.salary_period') + " " + \
                element_text(ch_driver, 'span.salary_calculation')
        except NoSuchElementException as er:
            job_salary = " "
            logger.error(er)
        try:
            job_viewed = element_text(ch_driver, '#job_ad_statistics > div > strong')
        except NoSuchElementException as er:
            job_viewed = " "
            logger.error(er)
        try:
            job_applied = element_text(ch_driver, '#job_ad_statistics > div:nth-child(2) > strong')
        except NoSuchElementException as er:
            job_applied = " "
            logger.error(er)
        finally:
            # element text which has comas are changed to dots and every element text is separated by comma and new
            # line is added by the end of every url for csv file format
            csv_file.write(
                job_title.replace(",", ".") + "," + job_company.replace(",", ".") + "," + job_city.replace(",", ".") +
                "," + job_salary + "," + job_viewed + "," + job_applied + "," + job_expiration + "," + url + "\n")
            counter += 1


def start() -> None:
    """main app function"""
    with open('Config/main_config.yaml') as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

    user_input = user_search_input()

    # setting logger parameters
    logging.basicConfig(filename=config['log_file'],
                        level=logging.INFO,
                        format='%(asctime)s : %(name)s : %(message)s')
    logger = logging.getLogger(__name__)

    # setting chrome driver parameters
    op = webdriver.ChromeOptions()
    ch_driver = webdriver.Chrome(service=ChService('chromedriver.exe'), options=op)
    ch_driver.get(config['start_page'])
    ch_driver.maximize_window()

    # accepting cookies
    click_element(ch_driver, 'onetrust-accept-btn-handler')
    time.sleep(2)

    # opening a csv file with necessary headers
    csv_file = open_file_with_headers(config['save_file'], "Title, Company, City, Salary, View Count, Applicant Count, "
                                                           "Add Expiration, URL\n")

    # inputting and entering search
    ch_driver.find_element(By.ID, 'filter_keyword').send_keys(user_input)
    click_element(ch_driver, "main_filter_submit")
    time.sleep(2)

    # if user input is not valid asking again for new input till we get some result
    while "No ads found" in ch_driver.find_element(By.CSS_SELECTOR, "#main").text:
        # logging wrong user input
        logger.info(f"User Input: {user_input} is not valid")
        ch_driver.find_element(By.ID, 'filter_keyword').clear()
        user_input = str(input("Please Enter a valid search input for CV Bank: "))
        ch_driver.find_element(By.ID, 'filter_keyword').send_keys(user_input)
        click_element(ch_driver, "main_filter_submit")
        time.sleep(2)

    # setting total pages nad logging them
    pages = get_total_pages(ch_driver, logger)
    logger.info(f"Total pages : {pages}")

    # logging total articles
    logger.info(element_text(ch_driver, '#js_id_id_job_ad_list > span'))

    # setting while loop for looping through all pages and scraping data
    page = 1
    while page <= pages:
        url_list = generating_url_list(ch_driver, "/html[1]/body[1]/div[1]/div[1]/div[1]/main[1]/div[1]/article/a")
        scraping(url_list, ch_driver, logger, csv_file)
        go_back(ch_driver)
        next_page(ch_driver, logger)
        page += 1

    # logging total scraped
    logger.info(f"Scraped adds: {counter}")
    print(f"Scraping finished. Total adds scraped {counter}")
    ch_driver.close()


start()