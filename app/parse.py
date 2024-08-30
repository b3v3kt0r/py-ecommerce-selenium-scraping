import csv
from dataclasses import dataclass, fields, astuple
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers")
LAPTOPS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/laptops/")
TABLETS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/tablets/")
PHONES_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones/")
TOUCH_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch/")

URLS_FIELDS = [HOME_URL, COMPUTERS_URL, LAPTOPS_URL, TABLETS_URL, PHONES_URL, TOUCH_URL]


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int
    additional_info: dict


PRODUCT_FIELDS = [field.name for field in fields(Product)]

_driver: WebDriver | None = None


def get_driver() -> WebDriver:
    return _driver


def set_driver(new_driver: WebDriver) -> None:
    global _driver
    _driver = new_driver


def parse_hdd_block_prices(product_soup: BeautifulSoup) -> dict[str, float]:
    detailed_url = urljoin(BASE_URL, product_soup.select_one(".title")["href"])
    driver = get_driver()
    driver.get(detailed_url)
    prices = {}
    try:
        swatches = driver.find_element(By.CLASS_NAME, "swatches")
        buttons = swatches.find_elements(By.TAG_NAME, "button")

        for button in buttons:
            if not button.get_property("disabled"):
                button.click()
                prices[button.get_property("value")] = float(driver.find_element(
                    By.CLASS_NAME, "price"
                ).text.replace("$", ""))

    except (NoSuchElementException, ElementClickInterceptedException):
        return prices


def parse_single_product(product_soup) -> Product:
    hdd_prices = parse_hdd_block_prices(product_soup)
    return Product(
        title=product_soup.select_one(".title")["title"],
        description=product_soup.select_one(".description").text,
        price=float(product_soup.select_one(".price").text.replace("$", "")),
        rating=int(product_soup.select_one("p[data-rating]")["data-rating"]),
        num_of_reviews=int(product_soup.select_one(".review-count").text[0]),
        additional_info={"hdd_prices": hdd_prices},
    )


def get_all_products(url, driver) -> [Product]:
    driver.get(url)

    while True:
        try:
            more_button = driver.find_element(By.CLASS_NAME, "ecomerce-items-scroll-more")
            more_button.click()
        except (NoSuchElementException, ElementClickInterceptedException):
            break

    products = BeautifulSoup(
        driver.page_source,
        "html.parser").select(".thumbnail")

    return [parse_single_product(product_soup) for product_soup in products]


def write_quotes_to_csv(products: [Product], filename: str) -> None:
    with open(filename, "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def parse_urls(driver: WebDriver, urls: list):
    all_products = []
    for url in urls:
        all_products.extend(get_all_products(url, driver))
    return all_products


def main(output_csv_path: str) -> None:
    with webdriver.Chrome() as new_driver:
        set_driver(new_driver)
        products = parse_urls(driver=new_driver, urls=URLS_FIELDS)
        write_quotes_to_csv(products, output_csv_path)


if __name__ == "__main__":
    main("info.csv")
