from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pickle
import json
import random
import sys


def setup_browser():
    """Настройка и инициализация браузера"""
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-notifications")
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(options=options)


def load_search_queries():
    """Загрузка поисковых запросов из JSON файла"""
    with open('data/query.json', 'r', encoding='utf-8') as file:
        data = json.load(file)
    querys = [value for item in data for value in item.values()]
    print(f'Вы передали запросы :{querys}')
    return querys


def init(browser):
    """Инициализация браузера"""
    browser.get('https://ru.pinterest.com/')
    try:
        for cookie in pickle.load(open('cookiewriter/session', 'rb')):
            browser.add_cookie(cookie)
        time.sleep(2)
        browser.refresh()
    except Exception as e:
        print(f"Ошибка загрузки cookies: {e}")
        raise


def search(browser, word, link_index):
    """Поиск и сохранение изображения"""
    wait = WebDriverWait(browser, 10)

    try:
        # Поиск

        searchS = wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//input[@aria-label="Поиск" or @placeholder="Поиск"]')))
        searchS.click()
        searchS.clear()
        time.sleep(1)
        searchS.clear()
        searchS.send_keys(word + '\ue007')
        print(f"Поиск: {word}")
        time.sleep(3)

        # Случайный скролл(можно настроить самому,я сделал это чтобы были рандомные элементы
        scroll_distance = random.randint(300, 1500)
        browser.execute_script(f"window.scrollBy(0, {scroll_distance});")
        time.sleep(1)

        # Поиск пинов
        pins = wait.until(EC.presence_of_all_elements_located(
            (By.XPATH, '//div[@data-test-id="pin"]')))

        if not pins:
            print("Пины не найдены")
            return None

        random_pin = random.choice(pins)
        random_pin.click()
        print("Пин найден")
        time.sleep(5)


        image = wait.until(EC.presence_of_element_located(
            (By.XPATH, '//img[contains(@src, "pinimg.com")]')))
        img_url = image.get_attribute('src')

        browser.execute_script(f"window.open('{img_url}', '_blank');")
        WebDriverWait(browser, 5).until(lambda d: len(d.window_handles) > 1)
        browser.switch_to.window(browser.window_handles[1])


        img_element = wait.until(EC.presence_of_element_located((By.XPATH, '//img[@src]')))
        img_url2 = img_element.get_attribute('src')

        fin_url = img_url2
        if '/60x60/' in img_url2:
            fin_url = img_url2.replace('/60x60/', '/originals/')
        elif '/236x/' in img_url2:
            fin_url = img_url2.replace('/236x/', '/originals/')

        return fin_url

    except Exception as e:
        print(f"Ошибка поиска: {e}")
        browser.save_screenshot(f'error_{word.replace(" ", "_")}.png')
        return None
    finally:
        if len(browser.window_handles) > 1:
            browser.close()
            browser.switch_to.window(browser.window_handles[0])


def main():
    """Основная функция запуска """
    try:
        browser = setup_browser()
        search_queries = load_search_queries()
        links_list = [{}]

        init(browser)

        for index, item in enumerate(search_queries):
            max_retries = 3
            attempt = 0

            while attempt < max_retries:
                result = search(browser, item, index)
                if result:
                    links_list[0][f"link{index + 1}"] = result
                    print(f"Ссылка {index + 1} сохранена: {result}")
                    break
                else:
                    attempt += 1
                    print(f"Не удалось получить ссылку для: {item} (попытка {attempt}/{max_retries})")
            else:
                print(f"Не удалось получить ссылку для {item} после {max_retries} попыток")


        with open('data/links.json', 'w', encoding='utf-8') as file:
            json.dump(links_list, file, indent=4, ensure_ascii=False)
        print("Результаты сохранены в links.json")

    except Exception as e:
        print(f"Критическая ошибка: {e}")
        sys.exit(1)

main()
