import pandas as pd
import os # Pour vérifier si le fichier de sortie existe déjà

# --- Configuration ---
# Chemin vers votre fichier Excel d'entrée
input_file_path = r"D:\Téléchargements\MatchingExport_04122025130222.xlsx"

# Nom du fichier Excel de sortie (sera créé dans le même dossier que le fichier d'entrée)
output_file_name = "MatchingExport_Unique_Transactions.xlsx"
output_file_path = os.path.join(os.path.dirname(input_file_path), output_file_name)

# Nom de la colonne sur laquelle baser l'unicité
key_column = "TransactionReferenceNumber"

# --- Traitement ---
print(f"Début du traitement du fichier : {input_file_path}")

try:
    # 1. Lire le fichier Excel dans un DataFrame pandas
    print("Lecture du fichier Excel...")
    df = pd.read_excel(input_file_path)
    print(f"Fichier lu. Nombre total de lignes : {len(df)}")

    # 2. Vérifier si la colonne clé existe
    if key_column not in df.columns:
        print(f"ERREUR : La colonne '{key_column}' spécifiée n'a pas été trouvée dans le fichier.")
        print("Colonnes disponibles :", df.columns.tolist())
    else:
        # 3. Supprimer les doublons en se basant sur la colonne 'TransactionReferenceNumber'
        # 'keep='first'' signifie que pour chaque groupe de doublons, la première ligne rencontrée est conservée.
        # Vous pouvez changer pour 'last' si vous préférez conserver la dernière.
        print(f"Suppression des doublons basée sur la colonne '{key_column}'...")
        df_unique = df.drop_duplicates(subset=[key_column], keep='first')
        nb_lignes_uniques = len(df_unique)
        nb_lignes_supprimees = len(df) - nb_lignes_uniques
        print(f"Nombre de lignes uniques conservées : {nb_lignes_uniques}")
        print(f"Nombre de lignes doublons supprimées : {nb_lignes_supprimees}")

        # 4. Sauvegarder le DataFrame résultant dans un nouveau fichier Excel
        print(f"Sauvegarde des données uniques dans : {output_file_path}...")
        # 'index=False' évite d'écrire l'index du DataFrame (les numéros de ligne 0, 1, 2...)
        # comme une colonne dans le fichier Excel de sortie.
        df_unique.to_excel(output_file_path, index=False, engine='openpyxl') # openpyxl est souvent requis pour .xlsx
        print("Sauvegarde terminée.")

        print("\nTraitement terminé avec succès !")

except FileNotFoundError:
    print(f"ERREUR : Le fichier d'entrée '{input_file_path}' n'a pas été trouvé.")
    print("Veuillez vérifier que le chemin d'accès et le nom du fichier sont corrects.")
except ImportError:
    print("ERREUR : La bibliothèque pandas ou openpyxl n'est pas installée.")
    print("Veuillez les installer en utilisant pip :")
    print("pip install pandas openpyxl")
except Exception as e:
    print(f"Une erreur inattendue est survenue : {e}")
    print("Veuillez vérifier le fichier Excel et le script.")