import csv
import requests
import os
from bs4 import BeautifulSoup


def extract_product_info(product_url):
    """Fonction pour extraire les informations d'un produit et télécharger son image"""
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
    try:
        product_info['category'] = soup.find('ul', {'class': 'breadcrumb'}).find_all('a')[2].get_text().strip() # erreur ici mais pq ? html parser met tout au format text directement donc mon get_text prend toute la ligne en compte ? pourquoi fonctionne avec l'autre script ? 
    except AttributeError:
        product_info['category'] = "NA"
    try:
        product_info['review_rating'] = soup.find('p', {'class': 'star-rating'})['class'][1]
    except AttributeError:
        product_info['review_rating'] = " N/A "
    except TypeError:
        product_info['review_rating'] = " N/A "
    try:
        image_url = base_url + soup.find('img')['src'][6:]
        product_info['image_url'] = image_url
        
        image_name = os.path.basename(image_url)
        image_path = os.path.join(product_info['category'], image_name)

        response = requests.get(image_url)
        
        if response.status_code == 200:
            if not os.path.exists(product_info['category']):
                os.makedirs(product_info['category'])

            with open(image_path, 'wb') as f:
                f.write(response.content)

                print(f"Image {image_name} enregistrée avec succès !")
        else:
            print(f"La requête pour l'image {image_url} a échoué.")
    except AttributeError:
        product_info['image_url'] = " N/A "
    except TypeError:
        product_info['image_url'] = " N/A "
    return product_info


def extract_categories_links(index_url, base_url):
    home_page = requests.get(base_url)
    soup = BeautifulSoup(home_page.content, 'html.parser')

    categories_links = []
    categories_list = soup.find('ul', {'class': 'nav-list'}).find_all('a')  
    for category in categories_list:
        categories_links.append({'category': category.text, 'category_url': base_url + category['href']})

    return categories_links


def write_product_category_csv(category_name, products_info):
    folder_name = category_name.strip()
    folder_path = os.path.join(os.getcwd(), folder_name)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    filename = os.path.join(folder_path, f"{folder_name}.csv")
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['product_page_url', 'upc', 'title', 'price_including_tax', 'price_excluding_tax', 'number_available', 'product_description', 'category', 'review_rating', 'image_url', 'category_url']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for product_info in products_info:
            writer.writerow(product_info)



def create_category_csv(categories_links, base_url):
    for category_info in categories_links:
        category_url = category_info['category_url']
        category_name = category_info['category']
        products_info = []
        current_page_url = category_url
        while current_page_url is not None:
            current_page = requests.get(current_page_url)
            soup = BeautifulSoup(current_page.content, 'html.parser')
            products = soup.find_all('article', {'class': 'product_pod'})
            for product in products:
                if product.find('a')['href'].count('/') >= 4:
                    product_url = base_url + 'catalogue/' + product.find('a')['href'][9:]
                    product_info = extract_product_info(product_url)
                    product_info['category'] = category_name
                    products_info.append(product_info)
                else:
                    product_url = base_url + 'catalogue/' + product.find('a')['href'][6:]
                    product_info = extract_product_info(product_url)
                    product_info['category'] = category_name
                    products_info.append(product_info)
            next_page = soup.find('li', {'class': 'next'})
            if next_page is not None:
                current_page_url = base_url + next_page.find('a')['href']
            else:
                current_page_url = None
        write_product_category_csv(category_name, products_info)



if __name__ == '__main__':
    base_url = 'http://books.toscrape.com/'
    index_url = base_url + 'index.html'
    categories_links = extract_categories_links(index_url, base_url)
    create_category_csv(categories_links, base_url)

