import pandas as pd
import os

def validate_number(phone):
    if pd.isna(phone):
        return False
    phone = str(phone)
    return (len(phone) == 11 and
            phone.startswith('33') and
            phone[2] in '123456789')

def process_phone_numbers(csv_path):
    df = pd.read_csv(csv_path, dtype={'telephone1': str, 'telephone2': str})
    result_rows = []

    for _, row in df.iterrows():
        if validate_number(row['telephone1']):
            result_rows.append(row)
        elif validate_number(row['telephone2']):
            row['telephone1'] = row['telephone2']
            result_rows.append(row)

    if result_rows:
        output_path = os.path.join(os.path.dirname(csv_path), 'numeros_valides.csv')
        result_df = pd.DataFrame(result_rows)
        result_df.to_csv(output_path, index=False)
        print(f"Fichier créé: {output_path}")

if __name__ == "__main__":
    process_phone_numbers(r"d:/code/numeros_france_transformes.csv")