import pandas as pd
import psycopg2
import time
from datetime import datetime

# Configuration PostgreSQL
pg_host = "localhost"
pg_port = "5432"
pg_database = "uni"
pg_username = "postgres"
pg_password = "trinita"  # À remplacer si nécessaire

# Chemin du fichier Excel
excel_file = r"D:\code\jour\300425\etat_client_eumm.xlsx"

def copy_data():
    start_time = time.time()

    print("Lecture du fichier Excel...")
    # Lecture du fichier Excel
    df = pd.read_excel(excel_file)

    # Vérification si la première ligne est un en-tête
    if df.iloc[0, 0] == 'Nom/Prenom':
        print("Suppression de la ligne d'en-tête...")
        df = df.iloc[1:].reset_index(drop=True)

    # Création d'un nouveau DataFrame avec les colonnes correctement mappées
    df_mapped = pd.DataFrame({
        'nom_prenom': df.iloc[:, 0],  # Colonne A: Nom/Prenom
        'date_de_naissance': pd.to_datetime(df.iloc[:, 1], errors='coerce'),  # Colonne B: Date de Naissance
        'lieu_de_naissance': df.iloc[:, 2],  # Colonne C: Lieu de Naissance
        'type_piece_identite': df.iloc[:, 3],  # Colonne D: Type de Piece D'identité
        'numero_piece_identite': df.iloc[:, 4],  # Colonne E: Numero de Piece D'identité
        'date_expiration_piece': pd.to_datetime(df.iloc[:, 5], errors='coerce')  # Colonne F: Date D'expiration de la Piece
    })

    total_records = len(df_mapped)
    print(f"Nombre total d'enregistrements: {total_records}")

    print("Connexion à PostgreSQL...")
    pg_conn = psycopg2.connect(
        host=pg_host, port=pg_port, dbname=pg_database,
        user=pg_username, password=pg_password
    )
    pg_cursor = pg_conn.cursor()

    try:
        # Vider la table cible
        pg_cursor.execute("TRUNCATE TABLE client_eumm RESTART IDENTITY")
        pg_conn.commit()

        # Conversion des valeurs NaN en None pour PostgreSQL
        df_mapped = df_mapped.where(pd.notna(df_mapped), None)

        # Préparation de la requête d'insertion
        insert_query = """
        INSERT INTO client_eumm 
        (nom_prenom, date_de_naissance, lieu_de_naissance, 
         type_piece_identite, numero_piece_identite, date_expiration_piece)
        VALUES (%s, %s, %s, %s, %s, %s)
        """

        # Copier par lots
        batch_size = 1000
        processed = 0

        print("Début de la copie...")

        # Traitement par lots
        data_to_insert = []
        for _, row in df_mapped.iterrows():
            data_to_insert.append((
                row['nom_prenom'],
                row['date_de_naissance'].date() if pd.notna(row['date_de_naissance']) else None,
                row['lieu_de_naissance'],
                row['type_piece_identite'],
                row['numero_piece_identite'],
                row['date_expiration_piece'].date() if pd.notna(row['date_expiration_piece']) else None
            ))

        # Traitement par lots
        for i in range(0, len(data_to_insert), batch_size):
            batch = data_to_insert[i:i+batch_size]
            pg_cursor.executemany(insert_query, batch)
            pg_conn.commit()

            processed += len(batch)
            print(f"Progrès: {processed}/{total_records} ({processed/total_records*100:.2f}%)")

        print(f"Copie terminée! {processed} enregistrements en {time.time() - start_time:.2f} secondes.")

    except Exception as e:
        print(f"Erreur: {e}")
        pg_conn.rollback()

    finally:
        pg_cursor.close()
        pg_conn.close()
        print("Connexion fermée.")

if __name__ == "__main__":
    copy_data()