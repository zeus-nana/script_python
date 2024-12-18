import os
from pathlib import Path
from datetime import datetime
import csv

def bytes_to_mb(bytes_size):
    """Convertit une taille en bytes en mégaoctets"""
    return bytes_size / (1024 * 1024)

def get_folder_content():
    # Obtenir le chemin du dossier Téléchargements
    folder_path = str(Path.home() / "Desktop")  # Pour Windows/Linux
    # Pour macOS, on peut aussi utiliser : folder_path = str(Path.home() / "Téléchargements")

    # Liste pour stocker les informations
    files_info = []

    # Parcourir tous les fichiers et dossiers
    for item in os.scandir(folder_path):
        try:
            # Obtenir la taille
            if item.is_file():
                size = os.path.getsize(item.path)
            else:  # Pour les dossiers, calculer la taille totale
                size = sum(f.stat().st_size for f in Path(item.path).rglob('*') if f.is_file())

            # Convertir la taille en MB
            size_mb = bytes_to_mb(size)

            files_info.append({
                'nom': item.name,
                'type': 'Dossier' if item.is_dir() else 'Fichier',
                'taille_mb': f"{size_mb:.2f}",  # Supprimé le "MB" pour éviter les espaces
                'date_modification': datetime.fromtimestamp(item.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                'taille_mb_raw': size_mb  # Pour le tri
            })

        except (PermissionError, OSError) as e:
            print(f"Erreur lors de l'accès à {item.name}: {e}")

    return files_info

def save_to_csv(files_info, output_file="contenu_IdeaProjects.csv"):
    # Créer le chemin complet pour le fichier CSV dans le dossier Téléchargements
    folder_path = str(Path.home() / "Desktop")
    output_path = os.path.join(folder_path, output_file)

    # Définir les en-têtes du CSV
    fieldnames = ['nom', 'type', 'taille_mb', 'date_modification']

    # Écrire le fichier CSV avec les paramètres appropriés pour gérer les caractères spéciaux
    with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:  # utf-8-sig pour Excel
        writer = csv.DictWriter(f,
                                fieldnames=fieldnames,
                                quoting=csv.QUOTE_ALL,  # Mettre des guillemets autour de toutes les valeurs
                                delimiter=';')          # Utiliser le point-virgule comme séparateur

        # Écrire l'en-tête
        writer.writeheader()

        # Écrire les données (en excluant taille_mb_raw qui n'est utilisé que pour le tri)
        for item in files_info:
            row = {k: v for k, v in item.items() if k != 'taille_mb_raw'}
            writer.writerow(row)

    return output_path

def main():
    print("Analyse du contenu du dossier ...")

    # Obtenir les informations
    files_info = get_folder_content()

    # Trier par type puis par taille (du plus grand au plus petit)
    files_info.sort(key=lambda x: (x['type'] != 'Dossier', -x['taille_mb_raw']))

    # Sauvegarder en CSV
    output_path = save_to_csv(files_info)

    print(f"\nLes résultats ont été sauvegardés dans : {output_path}")

    # Afficher un petit résumé
    total_files = sum(1 for item in files_info if item['type'] == 'Fichier')
    total_folders = sum(1 for item in files_info if item['type'] == 'Dossier')
    total_size_mb = sum(item['taille_mb_raw'] for item in files_info)

    print(f"\nRésumé:")
    print(f"Nombre total de fichiers : {total_files}")
    print(f"Nombre total de dossiers : {total_folders}")
    print(f"Taille totale : {total_size_mb:.2f} MB")

if __name__ == "__main__":
    main()