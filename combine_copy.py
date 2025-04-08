import os
import datetime

# Configuration
folder_to_analyse = r"C:\Users\fnana\StudioProjects\test_2025"  # Dossier à analyser
output_folder = r"d:\code"  # Dossier de sortie
structure_only = True  # Si True, n'affiche que les chemins sans le contenu

# Création du dossier de sortie s'il n'existe pas
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Nom du fichier de sortie avec horodatage
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
output_filename = os.path.join(output_folder, f"analyse_{timestamp}.txt")

# Fonction pour parcourir un dossier et ses sous-dossiers
def analyse_folder(folder_path, output_file):
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)

            # Écriture du chemin du fichier
            output_file.write(f"// {file_path}\n")

            # Si structure_only est False, on écrit aussi le contenu
            if not structure_only:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        output_file.write(content)
                except Exception as e:
                    output_file.write(f"[Erreur de lecture: {str(e)}]\n")

                # Ajouter une ligne vide après chaque fichier pour la lisibilité
                output_file.write("\n")

# Exécution principale
try:
    with open(output_filename, 'w', encoding='utf-8') as output_file:
        # Écrire un en-tête avec les informations sur l'analyse
        output_file.write(f"// Analyse du dossier: {folder_to_analyse}\n")
        output_file.write(f"// Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        output_file.write(f"// Mode: {'Structure uniquement' if structure_only else 'Structure et contenu'}\n")
        output_file.write("//================================================\n\n")

        # Lancer l'analyse
        analyse_folder(folder_to_analyse, output_file)

    print(f"Analyse terminée! Fichier de sortie créé: {output_filename}")

except Exception as e:
    print(f"Une erreur est survenue: {str(e)}")