import csv

def generate_sql_updates(csv_file_path, output_file_path):
    # Ouvrir le fichier de sortie en mode écriture
    with open(output_file_path, 'w', encoding='utf-8') as sql_file:
        # Lire le fichier CSV
        with open(csv_file_path, 'r', encoding='utf-8') as csv_file:
            csv_reader = csv.DictReader(csv_file)

            # Pour chaque ligne du CSV
            for row in csv_reader:
                # Créer la requête SQL UPDATE
                sql_update = f"UPDATE SENDER SET SEN_PHONE_NUMBER1='{row['telephone1']}'"

                # Ajouter le deuxième numéro de téléphone s'il existe
                if row['telephone2']:
                    sql_update += f", SEN_PHONE_NUMBER2='{row['telephone2']}'"

                # Ajouter la condition WHERE
                sql_update += f" WHERE SEN_ID={row['id']};\n"

                # Écrire la requête dans le fichier de sortie
                sql_file.write(sql_update)

# Utilisation du script
csv_file_path = r"D:\code\telephone_valide.csv"
output_file_path = r"D:\code\updates_sender_phone.sql"

generate_sql_updates(csv_file_path, output_file_path)