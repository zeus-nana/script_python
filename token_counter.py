import os
import re
import tiktoken

# Configuration
folder_path = r"C:\Users\fnana\StudioProjects\cpt_client_new\lib"  # Dossier à analyser
file_extensions = ["ts", "tsx", "js", "jsx", "py", "html", "css", "txt", "dart"]  # Types de fichiers à examiner

# Initialiser l'encodeur GPT
enc = tiktoken.get_encoding("cl100k_base")  # Encodeur utilisé par les modèles Claude

def count_tokens_in_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            tokens = enc.encode(content)
            return len(tokens)
    except Exception as e:
        print(f"Erreur lors de la lecture du fichier {file_path}: {e}")
        return 0

def main():
    total_tokens = 0
    file_count = 0

    for root, dirs, files in os.walk(folder_path):
        for file in files:
            # Vérifier si l'extension du fichier est dans la liste des extensions à analyser
            ext = file.split('.')[-1]
            if ext in file_extensions:
                file_path = os.path.join(root, file)
                tokens_in_file = count_tokens_in_file(file_path)
                total_tokens += tokens_in_file
                file_count += 1
                print(f"{file_path}: {tokens_in_file} tokens")

    print(f"\nRésumé:")
    print(f"Nombre total de fichiers analysés: {file_count}")
    print(f"Nombre total de tokens: {total_tokens}")

if __name__ == "__main__":
    main()