import json

def update_json_file(file_path, montant, formule):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    update_count = 0
    montant_lower = montant.lower()

    for operation_type in data:
        for operation in data[operation_type]:
            for compte in operation['comptes']:
                if compte.get('montant') is not None and compte['montant'].lower() == montant_lower:
                    compte['formule'] = formule
                    update_count += 1

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return update_count

file_path = r"C:\Users\fnana\Downloads\compta.json"
montant = "cssion part ttc"
formule = "L06"

try:
    updates = update_json_file(file_path, montant, formule)
    print(f"Mise à jour effectuée: {updates} entrées modifiées avec formule '{formule}'")
except Exception as e:
    print(f"Error: {e}")