import csv

# Fonction pour vérifier si un ID est numérique
def is_numeric(value):
    return value.isdigit()

# Chemins des fichiers
input_file = r"d:/code/up.csv"
output_non_numeric = r"d:/code/non_numeric_ids.csv"
output_numeric = r"d:/code/numeric_ids.csv"

# Traitement des fichiers
with open(input_file, mode='r', encoding='utf-8') as infile, \
        open(output_non_numeric, mode='w', newline='', encoding='utf-8') as non_numeric_file, \
        open(output_numeric, mode='w', newline='', encoding='utf-8') as numeric_file:

    reader = csv.reader(infile)
    writer_non_numeric = csv.writer(non_numeric_file)
    writer_numeric = csv.writer(numeric_file)

    # Lire les en-têtes
    headers = next(reader)
    writer_non_numeric.writerow(headers)
    writer_numeric.writerow(headers)

    # Trier les lignes
    for row in reader:
        id_value = row[0]  # ID se trouve dans la première colonne
        if is_numeric(id_value):
            writer_numeric.writerow(row)  # Écrire dans le fichier des IDs numériques
        else:
            writer_non_numeric.writerow(row)  # Écrire dans le fichier des IDs non numériques

print(f"Les lignes avec des IDs numériques ont été extraites vers {output_numeric}.")
print(f"Les lignes avec des IDs non numériques ont été extraites vers {output_non_numeric}.")
