import pandas as pd
import os

def transform_french_numbers(csv_path):
    df = pd.read_csv(csv_path, dtype={'telephone1': str, 'telephone2': str})
    french_df = df[df['pays'] == 'FRANCE'].copy()

    def transform_number(phone):
        if pd.isna(phone):
            return phone

        phone = str(phone).strip()
        length = len(phone)

        if length == 10 and phone.startswith('0') and phone[1] in '123456789':
            return '33' + phone[1:]
        elif length == 9 and phone[0] in '123456789':
            return '33' + phone
        elif length == 13 and phone.startswith('0033'):
            return '33' + phone[4:]
        elif length == 14 and phone.startswith('0033'):
            temp = phone[4:]
            if len(temp) == 10 and temp.startswith('0') and temp[1] in '123456789':
                return '33' + temp[1:]
        elif length == 12 and phone.startswith('+33'):
            return '33' + phone[3:]

        return phone

    french_df['telephone2'] = french_df['telephone2'].apply(transform_number)

    output_path = os.path.join(os.path.dirname(csv_path), 'numeros_france_transformes_tel_02.csv')
    french_df.to_csv(output_path, index=False)
    print(f"Transformation terminée. Fichier créé: {output_path}")

if __name__ == "__main__":
    transform_french_numbers(r"d:/code/numeros_france_transformes.csv")