import csv

# Fichiers sources
input_gda = r"d:/code/statut_gda_risque_potentiel.csv"
input_ppe = r"d:/code/statut_ppe_risque_potentiel.csv"
input_non_filtered = r"d:/code/non_filtered.csv"

# Fichiers de sortie SQL
output_gda_sql = r"d:/code/update_gda.sql"
output_ppe_sql = r"d:/code/update_ppe.sql"
output_non_filtered_sql = r"d:/code/update_non_filtered.sql"

# Fonction pour générer les fichiers SQL
def generate_sql(input_file, output_file, data2_value, data3_value):
    with open(input_file, mode='r', encoding='utf-8') as infile, \
            open(output_file, mode='w', encoding='utf-8') as outfile:

        reader = csv.DictReader(infile)
        for row in reader:
            sen_id = row.get("ID Unique")  # Remplacez par le nom exact de la colonne si nécessaire
            if sen_id:  # Vérifier que l'ID est présent
                sql_line = f'UPDATE SENDER SET DATA2="{data2_value}", DATA3="{data3_value}" WHERE SEN_ID = {sen_id};\n'
                outfile.write(sql_line)

# Génération des fichiers SQL
generate_sql(input_gda, output_gda_sql, data2_value="D", data3_value="BLACKLIST")
generate_sql(input_ppe, output_ppe_sql, data2_value="A", data3_value="PPE")
generate_sql(input_non_filtered, output_non_filtered_sql, data2_value="A", data3_value="RAS")

print(f"Fichiers SQL générés :")
print(f"- {output_gda_sql}")
print(f"- {output_ppe_sql}")
print(f"- {output_non_filtered_sql}")