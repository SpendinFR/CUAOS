"""
App Launcher - Lanceur et contrôleur d'applications
"""
import subprocess
import os
from pathlib import Path
import json
import psutil


class AppLauncher:
    def __init__(self):
        # Base de données d'applications communes
        self.app_database = {
            "chrome": "chrome.exe",
            "google chrome": "chrome.exe",
            "firefox": "firefox.exe",
            "edge": "msedge.exe",
            "notepad": "notepad.exe",
            "bloc-notes": "notepad.exe",
            "calculatrice": "calc.exe",
            "calculator": "calc.exe",
            "explorer": "explorer.exe",
            "explorateur": "explorer.exe",
            "cmd": "cmd.exe",
            "powershell": "powershell.exe",
            "paint": "mspaint.exe",
            "word": "WINWORD.EXE",
            "excel": "EXCEL.EXE",
            "powerpoint": "POWERPNT.EXE",
            "outlook": "OUTLOOK.EXE",
            "vscode": "Code.exe",
            "visual studio code": "Code.exe",
            "spotify": "Spotify.exe",
            "steam": "steam.exe",
            "discord": "Discord.exe",
            "slack": "slack.exe",
            "zoom": "Zoom.exe",
            "teams": "Teams.exe",
            "vlc": "vlc.exe",
        }
        
        self.running_apps = {}
    def scan_installed_apps(self) -> dict:
        """
        Scanne les applications installées sur Windows
        Retourne: {nom_affiché: chemin_exe}
        """
        apps_found = {}
        
        # 1. Applications du Menu Démarrer
        start_menu_paths = [
            os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs"),
            os.path.expandvars(r"%ProgramData%\Microsoft\Windows\Start Menu\Programs"),
        ]
        
        for start_path in start_menu_paths:
            if os.path.exists(start_path):
                for root, dirs, files in os.walk(start_path):
                    for file in files:
                        if file.endswith('.lnk'):
                            # Nom sans .lnk
                            app_name = file[:-4].lower()
                            apps_found[app_name] = file
        
        # 2. Ajouter la database existante
        for name, exe in self.app_database.items():
            apps_found[name] = exe
        
        print(f"[AppLauncher] {len(apps_found)} applications détectées")
        return apps_found

    def find_best_app_match(self, app_name: str, available_apps: dict) -> tuple:
        """
        Trouve la meilleure correspondance pour un nom d'app
        Retourne: (app_name_matched, executable, score)
        """
        app_name_lower = app_name.lower().strip()
        
        # 1. Match exact
        if app_name_lower in available_apps:
            return (app_name_lower, available_apps[app_name_lower], 100)
        
        # 2. Match partial (contient)
        candidates = []
        for name, exe in available_apps.items():
            if app_name_lower in name or name in app_name_lower:
                # Score: longueur du match / longueur totale
                ratio = len(app_name_lower) / max(len(name), len(app_name_lower))
                score = int(ratio * 90)
                candidates.append((name, exe, score))
        
        if candidates:
            # Trier par score décroissant
            candidates.sort(key=lambda x: x[2], reverse=True)
            return candidates[0]
        
        # 3. Match par mots
        app_words = set(app_name_lower.split())
        for name, exe in available_apps.items():
            name_words = set(name.split())
            common = app_words & name_words
            if common:
                score = int((len(common) / len(app_words)) * 70)
                candidates.append((name, exe, score))
        
        if candidates:
            candidates.sort(key=lambda x: x[2], reverse=True)
            return candidates[0]
        
        return (None, None, 0)
    
    def launch_app(self, app_name, args=None):
        """
        Lance une application avec scan et matching intelligent
        """
        print(f"[AppLauncher] Recherche: '{app_name}'")
        
        # 1. Scanner les apps disponibles
        available_apps = self.scan_installed_apps()
        
        # 2. Matching intelligent
        matched_name, executable, score = self.find_best_app_match(app_name, available_apps)
        
        if not matched_name or score < 50:
            print(f"❌ Application '{app_name}' non trouvée")
            return {
                "success": False,
                "error": f"Application '{app_name}' non trouvée",
                "app": app_name
            }
        
        print(f"✅ Match trouvé: '{matched_name}' (score: {score})")
        
        try:
            # Construire la commande
            cmd = [executable]
            if args:
                cmd.extend(args if isinstance(args, list) else [args])
            
            # Lancer l'application
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True
            )
            
            self.running_apps[app_name] = process
            print(f"🚀 Application lancée: {matched_name} (PID: {process.pid})")
            
            return {
                "success": True,
                "app": matched_name,
                "original_query": app_name,
                "pid": process.pid,
                "match_score": score,
                "command": ' '.join(cmd)
            }
            
        except Exception as e:
            print(f"❌ Erreur lancement {matched_name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "app": app_name
            }
    
    def launch_with_file(self, filepath):
        """Lance l'application par défaut pour un fichier"""
        try:
            os.startfile(filepath)
            print(f"📂 Fichier ouvert: {filepath}")
            return True
        except Exception as e:
            print(f"❌ Erreur ouverture: {e}")
            return False
    
    def launch_url(self, url, browser="chrome"):
        """Lance une URL dans Chrome en mode debug pour Playwright"""
        import time
        import os
        from config import CHROME_DEBUG_PORT
        
        try:
            # Trouver Chrome
            chrome_paths = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe")
            ]
            
            chrome_path = None
            for path in chrome_paths:
                if os.path.exists(path):
                    chrome_path = path
                    break
            
            if not chrome_path:
                # Fallback: utiliser start
                subprocess.Popen(f'start chrome "{url}"', shell=True)
                print(f"🌐 URL ouverte: {url}")
                time.sleep(3)
                return True
            
            # Lancer Chrome en mode debug
            cmd = [
                chrome_path,
                f"--remote-debugging-port={CHROME_DEBUG_PORT}",
                "--user-data-dir=C:\\chrome-debug-profile",
                url
            ]
            
            subprocess.Popen(cmd)
            print(f"🌐 URL ouverte (mode debug port {CHROME_DEBUG_PORT}): {url}")
            time.sleep(3)
            return True
            
        except Exception as e:
            print(f"❌ Erreur ouverture URL: {e}")
            return False
    
    def is_running(self, app_name):
        """Vérifie si une application est en cours d'exécution"""
        try:
            app_name_lower = app_name.lower()
            
            # Obtenir l'exe de l'app
            if app_name_lower in self.app_database:
                exe_name = self.app_database[app_name_lower].lower()
            else:
                exe_name = app_name.lower()
                if not exe_name.endswith('.exe'):
                    exe_name += '.exe'
            
            # Chercher dans les processus
            for proc in psutil.process_iter(['name']):
                try:
                    if proc.info['name'].lower() == exe_name:
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return False
        except Exception as e:
            print(f"⚠️ Erreur vérification: {e}")
            return False
    
    def close_app(self, app_name):
        """Ferme une application"""
        try:
            # D'abord essayer de fermer via notre registry
            if app_name in self.running_apps:
                process = self.running_apps[app_name]
                process.terminate()
                process.wait(timeout=5)
                del self.running_apps[app_name]
                print(f"✅ Application fermée: {app_name}")
                return True
            
            # Sinon, chercher et tuer le processus
            app_name_lower = app_name.lower()
            if app_name_lower in self.app_database:
                exe_name = self.app_database[app_name_lower].lower()
            else:
                exe_name = app_name.lower()
                if not exe_name.endswith('.exe'):
                    exe_name += '.exe'
            
            killed = False
            for proc in psutil.process_iter(['name']):
                try:
                    if proc.info['name'].lower() == exe_name:
                        proc.terminate()
                        proc.wait(timeout=5)
                        killed = True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if killed:
                print(f"✅ Application fermée: {app_name}")
                return True
            else:
                print(f"⚠️ Application non trouvée: {app_name}")
                return False
                
        except Exception as e:
            print(f"❌ Erreur fermeture: {e}")
            return False
    
    def list_running_apps(self):
        """Liste les applications en cours d'exécution"""
        try:
            apps = set()
            for proc in psutil.process_iter(['name']):
                try:
                    apps.add(proc.info['name'])
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return sorted(list(apps))
        except Exception as e:
            print(f"❌ Erreur listage: {e}")
            return []
    
    def add_app_to_database(self, name, executable):
        """Ajoute une application à la base de données"""
        self.app_database[name.lower()] = executable
        print(f"✅ Application ajoutée: {name} → {executable}")
    
    def get_app_info(self, app_name):
        """Obtient les infos d'une application en cours"""
        try:
            app_name_lower = app_name.lower()
            if app_name_lower in self.app_database:
                exe_name = self.app_database[app_name_lower].lower()
            else:
                exe_name = app_name.lower()
                if not exe_name.endswith('.exe'):
                    exe_name += '.exe'
            
            for proc in psutil.process_iter(['name', 'pid', 'cpu_percent', 'memory_info']):
                try:
                    if proc.info['name'].lower() == exe_name:
                        return {
                            'name': proc.info['name'],
                            'pid': proc.info['pid'],
                            'cpu': proc.info['cpu_percent'],
                            'memory': proc.info['memory_info'].rss / 1024 / 1024  # MB
                        }
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return None
        except Exception as e:
            print(f"❌ Erreur info app: {e}")
            return None
