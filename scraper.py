import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import time
import csv
import os

def parse_dns(search_query):
    options = uc.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")

    driver = uc.Chrome(options=options)
    
    try:
        driver.get(f"https://www.dns-shop.ru/search/?q={search_query}")
        
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "catalog-product"))
        )
        
        last_height = driver.execute_script("return document.body.scrollHeight")
        scroll_attempts = 0
        
        while scroll_attempts < 5:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
            scroll_attempts += 1
        
        products = driver.find_elements(By.CLASS_NAME, "catalog-product")
        print(f"Найдено товаров: {len(products)}")
        
        # Словарь для хранения уникальных товаров
        unique_products = {}
        for product in products:
            try:
                ActionChains(driver).move_to_element(product).perform()
                time.sleep(0.2)
                
                name = product.find_element(By.CLASS_NAME, "catalog-product__name").text.strip()
                price_element = product.find_element(By.CLASS_NAME, "product-buy__price")
                
                def get_clean_price(element):
                    full_text = element.get_attribute("textContent").strip()
                    return ' '.join(full_text.split()).split('₽')[0].strip()
                
                clean_price = get_clean_price(price_element)
                
                # Проверяем на дубликаты по названию и цене
                product_key = (name, clean_price)
                if product_key not in unique_products:
                    link = product.find_element(By.CLASS_NAME, "catalog-product__name").get_attribute("href")
                    try:
                        img = product.find_element(By.CSS_SELECTOR, ".catalog-product__image img.loaded")
                        link_photo = img.get_attribute("src") or img.get_attribute("data-src")
                    except:
                        link_photo = "Нет фото"
                    
                    unique_products[product_key] = [name, clean_price, link, link_photo]
            except Exception as e:
                print(f"Ошибка парсинга товара: {str(e)}")
                continue
        
        os.makedirs("temp", exist_ok=True)

        # Преобразуем словарь обратно в список
        data = list(unique_products.values())

        with open(f"temp/dns_{search_query}.csv", "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["Название", "Цена", "Ссылка", "Ссылка_на_фото"])
            writer.writerows(data)
        
        print(f"Уникальных товаров сохранено: {len(data)}")
        return data
    
    finally:
        driver.quit()
