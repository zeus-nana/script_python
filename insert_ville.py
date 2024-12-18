import csv
from datetime import datetime

def escape_sql_string(text):
    return str(text).replace("'", "''")

def csv_to_sql_oracle(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as csv_file:
        csv_reader = csv.DictReader(csv_file)

        with open(output_file, 'w', encoding='utf-8') as sql_file:
            for row in csv_reader:
                ville_name = escape_sql_string(row['VI_LIBELLE'])
                user_create = escape_sql_string(row['USER_CREATE'])
                user_modif = escape_sql_string(row['USER_MODIF'])

                # Utilisation de S_VILLE.nextval pour l'ID
                insert_sql = f"""INSERT INTO ville VALUES (S_VILLE.nextval, '{ville_name}', {row['VI_ZN_ID']}, {row['STATUT']}, '{user_create}', '{user_modif}', SYSDATE, SYSDATE);
"""
                sql_file.write(insert_sql)

            sql_file.write("\nCOMMIT;")

# Utilisation du script
input_csv = r"D:\code\ville.csv"
output_sql = r"D:\code\ville_insert.sql"

try:
    csv_to_sql_oracle(input_csv, output_sql)
    print(f"Le fichier SQL a été généré avec succès : {output_sql}")
except Exception as e:
    print(f"Une erreur s'est produite : {str(e)}")