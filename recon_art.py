import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

def setup_driver():
    """Configure et retourne le driver Selenium."""
    chrome_options = Options()
    # Décommenter pour exécuter en mode headless (sans interface graphique)
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1920,1080")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def login(driver, url, username, password):
    """Se connecte au site ReconArt."""
    driver.get(url)

    # Attendre que la page de connexion se charge
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "user_email"))
        )

        # Remplir les champs de connexion
        driver.find_element(By.ID, "user_email").send_keys(username)
        driver.find_element(By.ID, "user_password").send_keys(password)
        driver.find_element(By.NAME, "commit").click()

        # Attendre que la redirection se termine
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".course-table"))
        )
        return True
    except TimeoutException:
        print("Échec de connexion - vérifiez vos identifiants ou l'URL")
        return False

def get_menu_items(driver):
    """Récupère tous les éléments du menu de navigation."""
    menu_items = []
    try:
        # Attendre que le menu soit chargé
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "ul.table-of-contents li"))
        )

        # Récupérer tous les éléments du menu
        items = driver.find_elements(By.CSS_SELECTOR, "ul.table-of-contents li a")
        for item in items:
            menu_items.append({
                "title": item.text.strip(),
                "link": item.get_attribute("href")
            })
    except Exception as e:
        print(f"Erreur lors de la récupération des éléments du menu: {e}")

    return menu_items

def clean_filename(title):
    """Nettoie le titre pour en faire un nom de fichier valide."""
    invalid_chars = '<>:"/\\|?*'
    filename = title.strip()
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename

def extract_page_content(driver, url, output_dir):
    """Extrait le contenu d'une page et le sauvegarde dans un fichier texte."""
    try:
        driver.get(url)

        # Attendre que le contenu principal soit chargé
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".activity-content"))
        )

        # Récupérer le titre et le contenu
        title_element = driver.find_element(By.CSS_SELECTOR, "h1")
        title = title_element.text.strip()

        content_element = driver.find_element(By.CSS_SELECTOR, ".activity-content")
        content = content_element.text.strip()

        # Créer un nom de fichier à partir du titre
        filename = clean_filename(title) + ".txt"
        filepath = os.path.join(output_dir, filename)

        # Sauvegarder le contenu dans un fichier
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"Titre: {title}\n\n")
            f.write(content)

        print(f"Page extraite: {title}")
        return title
    except Exception as e:
        print(f"Erreur lors de l'extraction de la page {url}: {e}")
        return None

def main():
    # Configuration
    base_url = "https://reconart.northpass.com/courses/"
    username = "fnana@avssarl.com"
    password = "Trinita#1"
    output_dir = r"d:code/reconart"

    # Créer le répertoire de sortie s'il n'existe pas
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Initialiser le driver
    driver = setup_driver()

    try:
        # Se connecter
        if login(driver, base_url, username, password):
            print("Connexion réussie!")

            # Récupérer les éléments du menu
            menu_items = get_menu_items(driver)
            print(f"Nombre de pages trouvées: {len(menu_items)}")

            # Parcourir chaque page et extraire son contenu
            for i, item in enumerate(menu_items, 1):
                print(f"Traitement de la page {i}/{len(menu_items)}: {item['title']}")
                extract_page_content(driver, item['link'], output_dir)

                # Pause pour éviter de surcharger le serveur
                time.sleep(10)

            print(f"Extraction terminée! Les fichiers sont sauvegardés dans le dossier '{output_dir}'")
    except Exception as e:
        print(f"Une erreur est survenue: {e}")
    finally:
        # Fermer le driver
        driver.quit()

if __name__ == "__main__":
    main()