import csv
import requests
import os
from bs4 import BeautifulSoup


def extract_product_info(product_url):
    """Fonction pour extraire les informations d'un produit"""
    page = requests.get(product_url)
    soup = BeautifulSoup(page.content, 'html.parser')

    # Extraction des informations du produit
    products = soup.findAll('article')
    product_info = {}
    product_info['product_page_url'] = product_url
    try:
        product_info['upc'] = soup.find('th', string='UPC').find_next('td').get_text()
    except AttributeError:
        product_info['upc'] = " N/A "
    product_info['title'] = soup.find('h1').text
    try:
        product_info['price_excluding_tax'] = soup.find('th', string='Price (excl. tax)').find_next('td').get_text()[1:]
    except AttributeError:
        product_info['price_excluding_tax'] = " N/A "
    try:
        product_info['price_including_tax'] = soup.find('th', string='Price (incl. tax)').find_next('td').get_text()[1:]
    except AttributeError:
        product_info['price_including_tax'] = " N/A "
    try:
        product_info['number_available'] = soup.find('th', string='Availability').find_next('td').get_text().strip()[10:]
    except AttributeError:
        product_info['number_available'] = " N/A "
    try:
        product_info['product_description'] = soup.find('div', {'id': 'product_description'}).find_next('p').get_text()
    except AttributeError:
        product_info['product_description'] = " N/A "
    category_element = soup.find('a', href='../category/books/')
    if category_element:
        product_info['category'] = category_element.text
    else:
        product_info['category'] = 'Unknown category'
    try:
        product_info['review_rating'] = soup.find('p', {'class': 'star-rating'})['class'][1]
    except AttributeError:
        product_info['review_rating'] = " N/A "
    except TypeError:
        product_info['review_rating'] = " N/A "
    try:
        product_info['image_url'] = base_url + soup.find('img')['src'][6:]
    except AttributeError:
        product_info['image_url'] = " N/A "
    except TypeError:
        product_info['image_url'] = " N/A "
    return product_info


def extract_categories_links(index_url, base_url):
    """Fonction pour extraire les liens vers toutes les catégories de livres d'un site"""
    home_page = requests.get(index_url)
    soup = BeautifulSoup(home_page.content, 'html.parser')

    categories_links = []
    categories_list = soup.find('ul', {'class': 'nav-list'}).find_all('a')  
    for category in categories_list:
        category_url = base_url + category['href']
        categories_links.append({'category': category.text, 'category_url': category_url})
        
        while True:
            products_info = []
            category_page = requests.get(category_url)
            category_soup = BeautifulSoup(category_page.content, 'html.parser')
            products_list = category_soup.find_all('article', {'class': 'product_pod'})
            for product in products_list:
                if product.find('a')['href'].count('/') >= 4:
                    product_url = base_url + 'catalogue/' + product.find('a')['href'][9:]
                    product_info = extract_product_info(product_url)
                    products_info.append(product_info)
                else:
                    product_url = base_url + 'catalogue/' + product.find('a')['href'][6:]
                    product_info = extract_product_info(product_url)
                    products_info.append(product_info)
            next_page = category_soup.find('li', {'class': 'next'})
            if not next_page:
                break
            category_url = base_url + 'catalogue/category/books/' + next_page.find('a')['href']

    return categories_links



def category_csv(category_name, products_info):
    """Fonction pour enregistrer les informations des produits d'une catégorie dans un fichier CSV"""
    print(category_name)
    filename = f"{category_name.strip()}.csv"
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['product_page_url', 'upc', 'title', 'price_including_tax', 'price_excluding_tax', 'number_available', 'product_description', 'category', 'review_rating', 'image_url', 'category_url']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for product_info in products_info:
            writer.writerow(product_info)




def create_category_csv(categories_links, base_url):
    """Fonction pour créer un fichier CSV pour chaque catégorie de livres"""
    for category_info in categories_links:
        category_url = category_info['category_url']
        category_name = category_info['category']
        products_info = extract_categories_links(category_url, base_url)
        category_products = []
        for product_info in products_info:
            if product_info['category'] == category_name:
                category_products.append(product_info)
        category_csv(category_name, category_products)


if __name__ == '__main__':
    base_url = 'http://books.toscrape.com/'
    index_url = base_url + 'index.html'
    categories_links = extract_categories_links(index_url, base_url)
    create_category_csv(categories_links, base_url)

