import csv

# Chemins des fichiers
input_file = r"d:/code/numeric_ids.csv"
output_gda_risk = r"d:/code/statut_gda_risque_potentiel.csv"
output_ppe_risk = r"d:/code/statut_ppe_risque_potentiel.csv"
output_unfiltered = r"d:/code/non_filtered.csv"

# Indices des colonnes
COLUMN_STATUT_GDA = "Statut GDA"
COLUMN_STATUT_PPE = "Statut PPE"
CONDITION_VALUE = "Risque potentiel"

# Lire et traiter le fichier
with open(input_file, mode='r', encoding='utf-8') as infile, \
        open(output_gda_risk, mode='w', newline='', encoding='utf-8') as gda_file, \
        open(output_ppe_risk, mode='w', newline='', encoding='utf-8') as ppe_file, \
        open(output_unfiltered, mode='w', newline='', encoding='utf-8') as unfiltered_file:

    reader = csv.DictReader(infile)
    headers = reader.fieldnames  # Obtenir les en-têtes du fichier
    writer_gda = csv.DictWriter(gda_file, fieldnames=headers)
    writer_ppe = csv.DictWriter(ppe_file, fieldnames=headers)
    writer_unfiltered = csv.DictWriter(unfiltered_file, fieldnames=headers)

    # Écrire les en-têtes dans les fichiers de sortie
    writer_gda.writeheader()
    writer_ppe.writeheader()
    writer_unfiltered.writeheader()

    # Variable pour compter les lignes apparaissant dans les deux fichiers
    both_conditions_count = 0

    # Trier les lignes
    for row in reader:
        gda_condition = row[COLUMN_STATUT_GDA] == CONDITION_VALUE
        ppe_condition = row[COLUMN_STATUT_PPE] == CONDITION_VALUE

        # Écrire dans les fichiers correspondants
        if gda_condition:
            writer_gda.writerow(row)
        if ppe_condition:
            writer_ppe.writerow(row)

        # Vérifier si la ligne répond aux deux conditions
        if gda_condition and ppe_condition:
            both_conditions_count += 1
            print(f"Ligne apparaissant dans les deux fichiers : {row}")

        # Écrire dans le fichier des lignes non triées si aucune condition n'est remplie
        if not gda_condition and not ppe_condition:
            writer_unfiltered.writerow(row)

    # Résumé
    print(f"Nombre total de lignes apparaissant dans les deux fichiers : {both_conditions_count}")
print(f"Les lignes avec 'Statut GDA = Risque potentiel' ont été extraites vers {output_gda_risk}.")
print(f"Les lignes avec 'Statut PPE = Risque potentiel' ont été extraites vers {output_ppe_risk}.")
print(f"Les lignes non triées ont été extraites vers {output_unfiltered}.")
