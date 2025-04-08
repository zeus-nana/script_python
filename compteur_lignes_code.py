import os
import fnmatch

# Configuration
TARGET_FOLDER = r"D:\Projet\2024\Transfin_260225"  # Dossier à analyser

# Extensions de fichiers à considérer comme du code
CODE_EXTENSIONS = [
    '*.py', '*.java', '*.js', '*.jsx', '*.ts', '*.tsx',
    '*.html', '*.css', '*.scss', '*.c', '*.cpp', '*.h',
    '*.cs', '*.php', '*.rb', '*.go', '*.rs', '*.swift',
    '*.kt', '*.kts', '*.scala', '*.sql', '*.sh', '*.ps1'
]

# Dossiers à ignorer
IGNORE_FOLDERS = [
    'node_modules', 'venv', 'env', '.git', '__pycache__',
    'build', 'dist', 'bin', 'obj', 'target'
]

def count_lines(file_path):
    """Compte le nombre de lignes dans un fichier."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            return len(file.readlines())
    except Exception as e:
        print(f"Erreur lors de la lecture de {file_path}: {e}")
        return 0

def is_code_file(filename):
    """Vérifie si un fichier correspond à une extension de code."""
    return any(fnmatch.fnmatch(filename, pattern) for pattern in CODE_EXTENSIONS)

def should_ignore_folder(folder_name):
    """Vérifie si un dossier doit être ignoré."""
    return any(ignore in folder_name for ignore in IGNORE_FOLDERS)

def analyze_directory():
    """Analyse tous les fichiers de code dans le dossier cible et ses sous-dossiers."""
    if not os.path.exists(TARGET_FOLDER):
        print(f"Le dossier {TARGET_FOLDER} n'existe pas.")
        return

    total_lines = 0
    code_file_count = 0
    total_file_count = 0
    stats_by_extension = {}

    print(f"Analyse du dossier: {TARGET_FOLDER}\n")

    for root, dirs, files in os.walk(TARGET_FOLDER):
        # Filtrer les dossiers à ignorer
        dirs[:] = [d for d in dirs if not should_ignore_folder(d)]

        # Compter le nombre total de fichiers explorés
        total_file_count += len(files)

        for file in files:
            if is_code_file(file):
                file_path = os.path.join(root, file)
                ext = os.path.splitext(file)[1].lower()

                # Ignorer les fichiers trop grands (option)
                if os.path.getsize(file_path) > 10 * 1024 * 1024:  # 10 Mo
                    print(f"Fichier ignoré (trop grand): {file_path}")
                    continue

                lines = count_lines(file_path)
                total_lines += lines
                code_file_count += 1

                # Statistiques par extension
                if ext not in stats_by_extension:
                    stats_by_extension[ext] = {'files': 0, 'lines': 0}

                stats_by_extension[ext]['files'] += 1
                stats_by_extension[ext]['lines'] += lines

                # Afficher la progression pour les gros projets
                if code_file_count % 100 == 0:
                    print(f"Fichiers de code analysés: {code_file_count}")

    # Afficher les résultats
    print("\n===== RÉSULTATS =====")
    print(f"Nombre total de fichiers explorés: {total_file_count}")
    print(f"Nombre de fichiers de code: {code_file_count}")
    print(f"Nombre total de lignes de code: {total_lines}")

    if stats_by_extension:
        print("\nStatistiques par extension:")
        for ext, stats in sorted(stats_by_extension.items(), key=lambda x: x[1]['lines'], reverse=True):
            print(f"{ext or 'Sans extension'}: {stats['lines']} lignes dans {stats['files']} fichiers")

if __name__ == "__main__":
    analyze_directory()