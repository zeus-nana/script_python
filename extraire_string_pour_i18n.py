#!/usr/bin/env python3
import os
import json
import re
from typing import Set, List, Dict
from pathlib import Path

def extract_strings_from_file(file_path: str) -> Set[str]:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Regex pour trouver les chaînes entre guillemets
        single_quotes = re.findall(r"'([^']*)'", content)
        double_quotes = re.findall(r'"([^"]*)"', content)
        template_literals = re.findall(r'`([^`]*)`', content)

        strings = set()
        for s in single_quotes + double_quotes + template_literals:
            s = s.strip()
            if len(s) > 1 and not s.startswith(('http', 'www', '/', '.', '@')):
                strings.add(s)

        return strings
    except Exception as e:
        print(f"Erreur lors de l'analyse de {file_path}: {str(e)}")
        return set()

def find_files(directory: str, extensions: List[str]) -> List[str]:
    files = []
    for root, _, filenames in os.walk(directory):
        for filename in filenames:
            if any(filename.endswith(ext) for ext in extensions):
                files.append(os.path.join(root, filename))
    return files

def generate_key(text: str) -> str:
    return (text.lower()
            .replace(' ', '_')
            .replace('-', '_')
            .replace("'", '')
            .replace('"', '')
            .replace('/', '_')
            .strip('_'))

def generate_translation_file(strings: Set[str], output_path: str) -> None:
    translations = {
        'fr': {},
        'en': {}
    }

    for string in sorted(strings):
        key = generate_key(string)
        translations['fr'][key] = string
        translations['en'][key] = ''

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(translations, f, ensure_ascii=False, indent=2)

def main():
    project_dir = r"C:\Users\fnana\IdeaProjects\projet_cera\frontend"
    output_file = r"C:\Users\fnana\Documents\translations.json"
    extensions = ['.js', '.jsx', '.tsx', '.ts']

    files = find_files(project_dir, extensions)
    all_strings = set()

    for file in files:
        strings = extract_strings_from_file(file)
        all_strings.update(strings)

    generate_translation_file(all_strings, output_file)
    print(f"Extraction terminée ! {len(all_strings)} chaînes trouvées.")

if __name__ == '__main__':
    main()