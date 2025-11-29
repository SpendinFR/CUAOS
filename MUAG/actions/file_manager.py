"""
File Manager - Gestion de fichiers et dossiers
"""
import os
import shutil
from pathlib import Path
import subprocess
import json


class FileManager:
    def __init__(self):
        self.current_dir = Path.cwd()
    
    # ============================================
    # OPÉRATIONS DE BASE
    # ============================================
    
    def create_file(self, filepath, content=""):
        """Crée un fichier"""
        try:
            filepath = Path(filepath)
            filepath.parent.mkdir(parents=True, exist_ok=True)
            filepath.write_text(content, encoding='utf-8')
            print(f"[OK] Fichier cree: {filepath}")
            return True
        except Exception as e:
            print(f"[ERROR] Erreur creation fichier: {e}")
            return False
    
    def read_file(self, filepath):
        """Lit un fichier"""
        try:
            filepath = Path(filepath)
            content = filepath.read_text(encoding='utf-8')
            print(f"[OK] Fichier lu: {filepath} ({len(content)} chars)")
            return content
        except Exception as e:
            print(f"[ERROR] Erreur lecture fichier: {e}")
            return None
    
    def write_file(self, filepath, content):
        """Écrit dans un fichier (écrasement)"""
        try:
            filepath = Path(filepath)
            filepath.write_text(content, encoding='utf-8')
            print(f"[OK] Fichier ecrit: {filepath}")
            return True
        except Exception as e:
            print(f"[ERROR] Erreur ecriture fichier: {e}")
            return False
    
    def append_file(self, filepath, content):
        """Ajoute du contenu à un fichier"""
        try:
            filepath = Path(filepath)
            with open(filepath, 'a', encoding='utf-8') as f:
                f.write(content)
            print(f"[OK] Contenu ajoute: {filepath}")
            return True
        except Exception as e:
            print(f"[ERROR] Erreur append fichier: {e}")
            return False
    
    def delete_file(self, filepath, confirm=True):
        """Supprime un fichier"""
        try:
            filepath = Path(filepath)
            if not filepath.exists():
                print(f"[ERROR] Fichier inexistant: {filepath}")
                return False
            
            if confirm:
                from utils.interaction_utilisateur import InterfaceUtilisateur
                interface = InterfaceUtilisateur()
                if not interface.demander_confirmation(f"⚠️  Confirmer suppression de '{filepath}' ?"):
                    print("[SÉCURITÉ] Suppression annulée")
                    return False
            
            filepath.unlink()
            print(f" Fichier supprimé: {filepath}")
            return True
        except Exception as e:
            print(f"[ERROR] Erreur suppression fichier: {e}")
            return False
    
    def copy_file(self, src, dest):
        """Copie un fichier"""
        try:
            src = Path(src)
            dest = Path(dest)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            print(f" Fichier copie: {src} → {dest}")
            return True
        except Exception as e:
            print(f"[ERROR] Erreur copie fichier: {e}")
            return False
    
    def move_file(self, src, dest):
        """Déplace un fichier"""
        try:
            src = Path(src)
            dest = Path(dest)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(src, dest)
            print(f" Fichier deplace: {src} → {dest}")
            return True
        except Exception as e:
            print(f"[ERROR] Erreur deplacement fichier: {e}")
            return False
    
    def rename_file(self, filepath, new_name):
        """Renomme un fichier"""
        try:
            filepath = Path(filepath)
            new_path = filepath.parent / new_name
            filepath.rename(new_path)
            print(f" Fichier renommé: {filepath.name} → {new_name}")
            return True
        except Exception as e:
            print(f"[ERROR] Erreur renommage: {e}")
            return False
    
    # ============================================
    # DOSSIERS
    # ============================================
    
    def create_directory(self, dirpath):
        """Crée un dossier"""
        try:
            dirpath = Path(dirpath)
            dirpath.mkdir(parents=True, exist_ok=True)
            print(f" Dossier cree: {dirpath}")
            return True
        except Exception as e:
            print(f"[ERROR] Erreur creation dossier: {e}")
            return False
    
    def delete_directory(self, dirpath, confirm=True):
        """Supprime un dossier"""
        try:
            dirpath = Path(dirpath)
            if not dirpath.exists():
                print(f"[ERROR] Dossier inexistant: {dirpath}")
                return False
            
            if confirm:
                from utils.interaction_utilisateur import InterfaceUtilisateur
                interface = InterfaceUtilisateur()
                if not interface.demander_confirmation(f"⚠️  Confirmer suppression du dossier '{dirpath}' et tout son contenu ?"):
                    print("[SÉCURITÉ] Suppression annulée")
                    return False
            
            shutil.rmtree(dirpath)
            print(f" Dossier supprimé: {dirpath}")
            return True
        except Exception as e:
            print(f"[ERROR] Erreur suppression dossier: {e}")
            return False
    
    def list_directory(self, dirpath=None):
        """Liste le contenu d'un dossier"""
        try:
            dirpath = Path(dirpath) if dirpath else self.current_dir
            items = list(dirpath.iterdir())
            print(f" {dirpath}: {len(items)} éléments")
            return [str(item) for item in items]
        except Exception as e:
            print(f" Erreur listage dossier: {e}")
            return []
    
    # ============================================
    # RECHERCHE
    # ============================================
    
    def find_files(self, pattern, directory=None, recursive=True):
        """
        Cherche des fichiers par pattern
        Args:
            pattern: glob pattern (ex: "*.txt", "**/*.py")
            directory: dossier de recherche
            recursive: recherche récursive
        """
        try:
            directory = Path(directory) if directory else self.current_dir
            
            if recursive:
                files = list(directory.rglob(pattern))
            else:
                files = list(directory.glob(pattern))
            
            print(f"Trouvé {len(files)} fichiers pour '{pattern}'")
            return [str(f) for f in files]
        except Exception as e:
            print(f"[ERROR] Erreur recherche: {e}")
            return []
    
    def search_in_files(self, text, directory=None, extensions=None):
        """
        Cherche du texte dans les fichiers
        Args:
            text: texte à chercher
            directory: dossier de recherche
            extensions: liste d'extensions (ex: ['.txt', '.py'])
        """
        try:
            directory = Path(directory) if directory else self.current_dir
            results = []
            
            for file in directory.rglob('*'):
                if not file.is_file():
                    continue
                
                if extensions and file.suffix not in extensions:
                    continue
                
                try:
                    content = file.read_text(encoding='utf-8', errors='ignore')
                    if text.lower() in content.lower():
                        results.append(str(file))
                except:
                    continue
            
            print(f"Trouvé '{text}' dans {len(results)} fichiers")
            return results
        except Exception as e:
            print(f"[ERROR] Erreur recherche texte: {e}")
            return []
    
    # ============================================
    # INFORMATIONS
    # ============================================
    
    def get_file_info(self, filepath):
        """Obtient les infos d'un fichier"""
        try:
            filepath = Path(filepath)
            if not filepath.exists():
                return None
            
            stats = filepath.stat()
            info = {
                'name': filepath.name,
                'path': str(filepath.absolute()),
                'size': stats.st_size,
                'created': stats.st_ctime,
                'modified': stats.st_mtime,
                'is_file': filepath.is_file(),
                'is_dir': filepath.is_dir(),
                'extension': filepath.suffix
            }
            return info
        except Exception as e:
            print(f"[ERROR] Erreur info fichier: {e}")
            return None
    
    def file_exists(self, filepath):
        """Vérifie si un fichier existe"""
        return Path(filepath).exists()
    
    def get_file_size(self, filepath):
        """Obtient la taille d'un fichier"""
        try:
            return Path(filepath).stat().st_size
        except:
            return 0
    
    # ============================================
    # OUVERTURE FICHIERS
    # ============================================
    
    def open_file(self, filepath):
        """Ouvre un fichier avec application par défaut"""
        try:
            filepath = Path(filepath)
            if not filepath.exists():
                print(f"[ERROR] Fichier inexistant: {filepath}")
                return False
            
            os.startfile(str(filepath))
            print(f" Fichier ouvert: {filepath}")
            return True
        except Exception as e:
            print(f"[ERROR] Erreur ouverture: {e}")
            return False
    
    def open_directory(self, dirpath):
        """Ouvre un dossier dans l'explorateur"""
        try:
            dirpath = Path(dirpath)
            if not dirpath.exists():
                print(f" Dossier inexistant: {dirpath}")
                return False
            
            os.startfile(str(dirpath))
            print(f" Dossier ouvert: {dirpath}")
            return True
        except Exception as e:
            print(f"[ERROR] Erreur ouverture: {e}")
            return False
    
    # ============================================
    # CHEMINS SPÉCIAUX
    # ============================================
    
    def get_desktop_path(self):
        """Obtient le chemin du bureau"""
        return str(Path.home() / "Desktop")
    
    def get_documents_path(self):
        """Obtient le chemin des documents"""
        return str(Path.home() / "Documents")
    
    def get_downloads_path(self):
        """Obtient le chemin des téléchargements"""
        return str(Path.home() / "Downloads")
    
    def get_home_path(self):
        """Obtient le chemin du répertoire utilisateur"""
        return str(Path.home())
