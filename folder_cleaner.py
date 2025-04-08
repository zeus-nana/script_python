import os
import shutil
import platform
from pathlib import Path

def get_download_folder():
    """Récupère automatiquement le chemin du dossier Téléchargements selon le système d'exploitation."""
    if platform.system() == "Windows":
        import winreg
        sub_key = r'SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders'
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, sub_key) as key:
            return winreg.QueryValueEx(key, '{374DE290-123F-4565-9164-39C4925E467B}')[0]
    elif platform.system() == "Darwin":  # macOS
        return os.path.join(os.path.expanduser('~'), 'Downloads')
    else:  # Linux et autres
        return os.path.join(os.path.expanduser('~'), 'Downloads')

def get_file_category(file_path):
    """Détermine la catégorie d'un fichier basé sur son extension."""
    extension = os.path.splitext(file_path)[1].lower()

    # Dictionnaire associant les extensions aux catégories
    categories = {
        # Documents
        '.pdf': 'Documents/PDF',
        '.doc': 'Documents/Word',
        '.docx': 'Documents/Word',
        '.txt': 'Documents/Texte',
        '.odt': 'Documents/Texte',
        '.rtf': 'Documents/Texte',
        '.xls': 'Documents/Excel',
        '.xlsx': 'Documents/Excel',
        '.ppt': 'Documents/PowerPoint',
        '.pptx': 'Documents/PowerPoint',

        # Images
        '.jpg': 'Images/JPG',
        '.jpeg': 'Images/JPG',
        '.png': 'Images/PNG',
        '.gif': 'Images/GIF',
        '.bmp': 'Images/Autres',
        '.tiff': 'Images/Autres',
        '.svg': 'Images/Vectorielles',

        # Vidéos
        '.mp4': 'Videos/MP4',
        '.avi': 'Videos/AVI',
        '.mov': 'Videos/MOV',
        '.mkv': 'Videos/MKV',
        '.wmv': 'Videos/Autres',

        # Audio
        '.mp3': 'Audio/MP3',
        '.wav': 'Audio/WAV',
        '.flac': 'Audio/FLAC',
        '.ogg': 'Audio/OGG',

        # Archives
        '.zip': 'Archives/ZIP',
        '.rar': 'Archives/RAR',
        '.7z': 'Archives/7Z',
        '.tar': 'Archives/TAR',
        '.gz': 'Archives/GZ',

        # Exécutables
        '.exe': 'Executables/EXE',
        '.msi': 'Executables/MSI',
        '.bat': 'Executables/Scripts',
        '.ps1': 'Executables/Scripts',

        # Code
        '.py': 'Code/Python',
        '.js': 'Code/JavaScript',
        '.html': 'Code/HTML',
        '.css': 'Code/CSS',
        '.java': 'Code/Java',
        '.c': 'Code/C_C++',
        '.cpp': 'Code/C_C++',
        '.h': 'Code/C_C++',
    }

    return categories.get(extension, 'Autres')

def organize_downloads():
    """Organise les fichiers du dossier de téléchargement par catégorie et déplace les dossiers."""
    # Chemins des dossiers
    source_folder = get_download_folder()
    destination_folder = r"D:\Téléchargements"

    print(f"Dossier source: {source_folder}")
    print(f"Dossier destination: {destination_folder}")

    # Création du dossier de destination s'il n'existe pas
    Path(destination_folder).mkdir(parents=True, exist_ok=True)

    # Liste des éléments dans le dossier source
    items = os.listdir(source_folder)

    # Compteurs pour le rapport
    moved_folders = 0
    moved_files = 0
    errors = 0

    for item in items:
        source_path = os.path.join(source_folder, item)

        try:
            # Si c'est un dossier, le déplacer directement
            if os.path.isdir(source_path):
                destination_path = os.path.join(destination_folder, item)

                # Éviter d'écraser un dossier existant
                if os.path.exists(destination_path):
                    print(f"Le dossier '{item}' existe déjà dans la destination, création d'une copie...")
                    i = 1
                    while os.path.exists(destination_path + f" ({i})"):
                        i += 1
                    destination_path = destination_path + f" ({i})"

                shutil.move(source_path, destination_path)
                print(f"Dossier déplacé: {item} -> {destination_path}")
                moved_folders += 1

            # Si c'est un fichier, le classer par catégorie
            elif os.path.isfile(source_path):
                category = get_file_category(item)
                category_folder = os.path.join(destination_folder, category)

                # Création du dossier de catégorie s'il n'existe pas
                Path(category_folder).mkdir(parents=True, exist_ok=True)

                destination_path = os.path.join(category_folder, item)

                # Éviter d'écraser un fichier existant
                if os.path.exists(destination_path):
                    name, ext = os.path.splitext(item)
                    i = 1
                    while os.path.exists(os.path.join(category_folder, f"{name} ({i}){ext}")):
                        i += 1
                    destination_path = os.path.join(category_folder, f"{name} ({i}){ext}")

                shutil.move(source_path, destination_path)
                print(f"Fichier classé: {item} -> {category}")
                moved_files += 1

        except Exception as e:
            print(f"Erreur lors du traitement de '{item}': {str(e)}")
            errors += 1

    # Rapport final
    print("\nRAPPORT DE TRI:")
    print(f"- {moved_folders} dossiers déplacés")
    print(f"- {moved_files} fichiers classés")
    print(f"- {errors} erreurs rencontrées")

if __name__ == "__main__":
    print("Début du tri des téléchargements...")
    organize_downloads()
    print("Opération terminée!")