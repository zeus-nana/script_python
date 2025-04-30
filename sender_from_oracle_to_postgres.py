import cx_Oracle
import psycopg2
import time
from datetime import datetime

# Configuration Oracle
oracle_username = "EUING"
oracle_password = "trinita"  # À remplacer
oracle_dsn = "localhost:1521/EUING"  # Format SID

# Configuration PostgreSQL
pg_host = "localhost"
pg_port = "5432"
pg_database = "uni"
pg_username = "postgres"
pg_password = "trinita"  # À remplacer

def copy_data():
    start_time = time.time()

    print("Connexion à Oracle...")
    oracle_conn = cx_Oracle.connect(oracle_username, oracle_password, oracle_dsn)
    oracle_cursor = oracle_conn.cursor()

    print("Connexion à PostgreSQL...")
    pg_conn = psycopg2.connect(
        host=pg_host, port=pg_port, dbname=pg_database,
        user=pg_username, password=pg_password
    )
    pg_cursor = pg_conn.cursor()

    try:
        # Vider la table cible
        pg_cursor.execute("TRUNCATE TABLE SENDER")
        pg_conn.commit()

        # Compter les enregistrements
        oracle_cursor.execute("SELECT COUNT(*) FROM EUING.SENDER")
        total_records = oracle_cursor.fetchone()[0]
        print(f"Nombre total d'enregistrements: {total_records}")

        # Récupérer les données
        oracle_cursor.execute("SELECT * FROM EUING.SENDER")

        # Récupérer les noms de colonnes
        column_names = [desc[0] for desc in oracle_cursor.description]
        placeholders = ", ".join(["%s"] * len(column_names))
        columns = ", ".join(column_names)

        # Requête d'insertion
        insert_query = f"INSERT INTO SENDER ({columns}) VALUES ({placeholders})"

        # Copier par lots
        batch_size = 1000
        processed = 0
        batch = []

        print("Début de la copie...")

        for row in oracle_cursor:
            batch.append(row)
            processed += 1

            if len(batch) >= batch_size:
                pg_cursor.executemany(insert_query, batch)
                pg_conn.commit()
                print(f"Progrès: {processed}/{total_records} ({processed/total_records*100:.2f}%)")
                batch = []

        # Traiter le dernier lot
        if batch:
            pg_cursor.executemany(insert_query, batch)
            pg_conn.commit()

        print(f"Copie terminée! {processed} enregistrements en {time.time() - start_time:.2f} secondes.")

    except Exception as e:
        print(f"Erreur: {e}")
        pg_conn.rollback()

    finally:
        oracle_cursor.close()
        oracle_conn.close()
        pg_cursor.close()
        pg_conn.close()
        print("Connexions fermées.")

if __name__ == "__main__":
    copy_data()