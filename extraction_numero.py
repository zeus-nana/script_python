import pandas as pd
import os

def extract_phone_by_country(csv_path, target_countries):
    # Lire les données du fichier CSV en forçant les colonnes 'telephone1' et 'telephone2' à être des chaînes
    df = pd.read_csv(csv_path, dtype={'telephone1': str, 'telephone2': str})

    # Filtrer les lignes correspondant aux pays cibles
    filtered_df = df[df['pays'].isin(target_countries)]

    # Obtenir le dossier du fichier CSV
    output_dir = os.path.dirname(csv_path)

    # Construire le chemin du fichier de sortie
    output_path = os.path.join(output_dir, 'extrait_numero_pays.csv')

    # Sauvegarder le fichier CSV filtré
    filtered_df.to_csv(output_path, index=False, encoding='utf-8')

    print(f"Lignes extraites et enregistrées dans : {output_path}")

if __name__ == "__main__":
    csv_path = r"d:/code/telephones_cleaned.csv"
    extract_phone_by_country(csv_path, ['FRANCE', 'BELGIQUE', 'ALLEMAGNE'])
