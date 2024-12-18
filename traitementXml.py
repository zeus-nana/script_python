import xml.etree.ElementTree as ET
import os
from datetime import datetime
from collections import Counter

def process_xml_file(xml_file_path):
    """Traite un fichier XML et retourne la liste des EndToEndId"""
    try:
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
        ns = {'ns': 'urn:iso:std:iso:20022:tech:xsd:pain.001.001.09'}

        end_to_end_ids = []
        for end_to_end_id in root.findall('.//ns:EndToEndId', ns):
            end_to_end_ids.append(end_to_end_id.text)

        return end_to_end_ids, None
    except ET.ParseError as e:
        return [], f"Erreur de parsing pour {xml_file_path}: {str(e)}"
    except Exception as e:
        return [], f"Erreur lors du traitement de {xml_file_path}: {str(e)}"

def find_xml_files(directory):
    """Trouve tous les fichiers XML dans le répertoire et ses sous-répertoires"""
    xml_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.xml'):
                xml_files.append(os.path.join(root, file))
    return xml_files

def extract_all_end_to_end_ids(directory):
    # Créer un dossier 'output' s'il n'existe pas
    output_dir = os.path.join(directory, 'output')
    os.makedirs(output_dir, exist_ok=True)

    # Créer des noms de fichiers avec timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = os.path.join(output_dir, f'end_to_end_ids_{timestamp}.txt')
    duplicates_file = os.path.join(output_dir, f'duplicates_{timestamp}.txt')
    error_file = os.path.join(output_dir, f'errors_{timestamp}.txt')

    # Trouver tous les fichiers XML
    xml_files = find_xml_files(directory)

    if not xml_files:
        print("Aucun fichier XML trouvé dans le répertoire.")
        return

    # Traiter chaque fichier XML
    all_ids = []
    errors = []

    for xml_file in xml_files:
        print(f"Traitement de {xml_file}")
        ids, error = process_xml_file(xml_file)
        if error:
            errors.append(error)
        all_ids.extend(ids)

    # Compter les occurrences et identifier les doublons
    id_counter = Counter(all_ids)
    unique_ids = sorted(id_counter.keys())
    duplicates = {id_: count for id_, count in id_counter.items() if count > 1}

    # Écrire les IDs uniques dans le fichier principal
    with open(output_file, 'w', encoding='utf-8') as f:
        for i, id_value in enumerate(unique_ids):
            if i < len(unique_ids) - 1:
                f.write(f"'{id_value}',\n")
            else:
                f.write(f"'{id_value}'")

    # Écrire les informations sur les doublons dans un fichier séparé
    if duplicates:
        with open(duplicates_file, 'w', encoding='utf-8') as f:
            f.write("Doublons trouvés :\n\n")
            for id_, count in sorted(duplicates.items()):
                f.write(f"'{id_}' : {count} occurrences\n")

    # Écrire les erreurs dans un fichier séparé
    if errors:
        with open(error_file, 'w', encoding='utf-8') as f:
            for error in errors:
                f.write(f"{error}\n")

    # Afficher les statistiques
    print(f"\nTraitement terminé :")
    print(f"- {len(xml_files)} fichiers XML traités")
    print(f"- {len(all_ids)} EndToEndId trouvés au total")
    print(f"- {len(unique_ids)} EndToEndId uniques")
    print(f"- {len(duplicates)} EndToEndId en doublon")
    print(f"- {len(errors)} erreurs rencontrées")
    print(f"\nRésultats sauvegardés dans : {output_file}")
    if duplicates:
        print(f"Rapport des doublons dans : {duplicates_file}")
    if errors:
        print(f"Erreurs enregistrées dans : {error_file}")

# Utilisation
directory_path = r"D:\code\171224"
extract_all_end_to_end_ids(directory_path)