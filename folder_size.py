import os
from pathlib import Path
from datetime import datetime
import csv

TARGET_FOLDER = r"D:\Projet\2024\Transfin_260225"  # Dossier à analyser

def bytes_to_mb(bytes_size):
    return bytes_size / (1024 * 1024)

def get_folder_content():
    folder_path = str(TARGET_FOLDER)
    files_info = []

    for item in os.scandir(folder_path):
        try:
            if item.is_file():
                size = os.path.getsize(item.path)
            else:
                size = sum(f.stat().st_size for f in Path(item.path).rglob('*') if f.is_file())

            size_mb = bytes_to_mb(size)

            files_info.append({
                'nom': item.name,
                'type': 'Dossier' if item.is_dir() else 'Fichier',
                'taille_mb': f"{size_mb:.2f}",
                'date_modification': datetime.fromtimestamp(item.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                'taille_mb_raw': size_mb
            })

        except (PermissionError, OSError) as e:
            print(f"Erreur lors de l'accès à {item.name}: {e}")

    return files_info

def save_to_csv(files_info):
    folder_name = os.path.basename(TARGET_FOLDER.rstrip('/\\'))
    output_file = f"contenu_{folder_name}.csv"
    folder_path = str(Path.home() / "Documents")
    output_path = os.path.join(folder_path, output_file)

    fieldnames = ['nom', 'type', 'taille_mb', 'date_modification']

    with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f,
                                fieldnames=fieldnames,
                                quoting=csv.QUOTE_ALL,
                                delimiter=';')

        writer.writeheader()

        for item in files_info:
            row = {k: v for k, v in item.items() if k != 'taille_mb_raw'}
            writer.writerow(row)

    return output_path

def main():
    print(f"Analyse du dossier {TARGET_FOLDER} ...")

    files_info = get_folder_content()
    files_info.sort(key=lambda x: (x['type'] != 'Dossier', -x['taille_mb_raw']))
    output_path = save_to_csv(files_info)

    print(f"\nLes résultats ont été sauvegardés dans : {output_path}")

    total_files = sum(1 for item in files_info if item['type'] == 'Fichier')
    total_folders = sum(1 for item in files_info if item['type'] == 'Dossier')
    total_size_mb = sum(item['taille_mb_raw'] for item in files_info)

    print(f"\nRésumé:")
    print(f"Nombre total de fichiers : {total_files}")
    print(f"Nombre total de dossiers : {total_folders}")
    print(f"Taille totale : {total_size_mb:.2f} MB")

if __name__ == "__main__":
    main()