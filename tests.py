from openai import OpenAI
import time

def test_openai_key(api_key):
    client = OpenAI(api_key=api_key)
    try:
        response = client.chat.completions.create(
            model="gpt-4o",  # On utilise le modèle le moins cher pour le test
            messages=[{"role": "user", "content": "Test"}],
            max_tokens=5  # Limite la réponse pour économiser des tokens
        )
        return True, "Clé valide"
    except Exception as e:
        return False, str(e)

def check_keys_from_file(file_path):
    try:
        # Lecture du fichier
        with open(file_path, 'r') as file:
            # Lecture de toutes les lignes et suppression des espaces
            keys = [line.strip() for line in file.readlines() if line.strip()]

        print(f"Nombre de clés trouvées : {len(keys)}\n")

        # Test de chaque clé
        for i, key in enumerate(keys, 1):
            print(f"Test de la clé #{i}: {key[:8]}...")  # Affiche seulement le début de la clé
            is_valid, message = test_openai_key(key)
            print(f"Résultat: {'✓' if is_valid else '✗'} - {message}\n")
            time.sleep(1)  # Pause d'une seconde entre chaque test

    except FileNotFoundError:
        print(f"Erreur: Le fichier {file_path} n'a pas été trouvé.")
    except Exception as e:
        print(f"Erreur lors de la lecture du fichier: {e}")

# Exécution du test
file_path = r"D:\code\keys.txt"
print("Début de la vérification des clés OpenAI...")
check_keys_from_file(file_path)