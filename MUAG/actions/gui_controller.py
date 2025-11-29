"""
GUI Controller - Contrôle de l'interface graphique via PyAutoGUI
"""
import pyautogui
import time
from pathlib import Path
import cv2
import numpy as np
from PIL import Image
from config import (
    PYAUTOGUI_PAUSE,
    PYAUTOGUI_FAILSAFE,
    WEB_SCREENSHOTS_DIR
)


class GUIController:
    def __init__(self):
        # Configuration PyAutoGUI
        pyautogui.PAUSE = PYAUTOGUI_PAUSE
        pyautogui.FAILSAFE = PYAUTOGUI_FAILSAFE
        
        self.screenshots_dir = Path(WEB_SCREENSHOTS_DIR)
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
    
    # ============================================
    # SOURIS
    # ============================================
    
    def get_mouse_position(self):
        """Obtient la position actuelle de la souris"""
        return pyautogui.position()
    
    def move_mouse(self, x, y, duration=0.5):
        """Déplace la souris à une position"""
        try:
            pyautogui.moveTo(x, y, duration=duration)
            return True
        except Exception as e:
            print(f"❌ Erreur déplacement souris: {e}")
            return False
    
    def click(self, x=None, y=None, clicks=1, button='left', duration=0.3):
        """
        Clique à une position
        Args:
            x, y: position (None = position actuelle)
            clicks: nombre de clics
            button: 'left', 'right', 'middle'
            duration: durée du mouvement de souris (0 = instantané)
        """
        try:
            if x is not None and y is not None:
                # Déplacer visuellement la souris AVANT de cliquer
                pyautogui.moveTo(x, y, duration=duration)
                pyautogui.click(clicks=clicks, button=button)
            else:
                pyautogui.click(clicks=clicks, button=button)
            print(f"🖱️ Clic {button} effectué")
            return True
        except Exception as e:
            print(f"❌ Erreur clic: {e}")
            return False
    
    def double_click(self, x=None, y=None):
        """Double-clic"""
        return self.click(x, y, clicks=2)
    
    def right_click(self, x=None, y=None):
        """Clic droit"""
        return self.click(x, y, button='right')
    
    def drag(self, x1, y1, x2, y2, duration=1.0):
        """Glisser-déposer"""
        try:
            pyautogui.moveTo(x1, y1)
            pyautogui.drag(x2 - x1, y2 - y1, duration=duration)
            print(f"🖱️ Drag de ({x1},{y1}) à ({x2},{y2})")
            return True
        except Exception as e:
            print(f"❌ Erreur drag: {e}")
            return False
    
    def scroll(self, clicks, x=None, y=None):
        """
        Scroll
        Args:
            clicks: nombre de clics (positif = haut, négatif = bas)
        """
        try:
            if x is not None and y is not None:
                pyautogui.moveTo(x, y)
            pyautogui.scroll(clicks)
            print(f"🔄 Scroll: {clicks}")
            return True
        except Exception as e:
            print(f"❌ Erreur scroll: {e}")
            return False
    
    # ============================================
    # CLAVIER
    # ============================================
    
    def type_text(self, text, interval=0.05):
        """Tape du texte"""
        import pyperclip
        try:
            # Pour les caractères non-ASCII, utiliser le presse-papier
            if any(ord(c) > 127 for c in text):
                # Méthode presse-papier pour caractères spéciaux
                pyperclip.copy(text)
                pyautogui.hotkey('ctrl', 'v')
                print(f"⌨️ Texte collé: {text[:50]}...")
            else:
                # Méthode standard pour ASCII
                pyautogui.write(text, interval=interval)
                print(f"⌨️ Texte tapé: {text[:50]}...")
            return True
        except Exception as e:
            print(f"❌ Erreur frappe: {e}")
            return False
    
    def press_key(self, key):
        """Appuie sur une touche"""
        try:
            pyautogui.press(key)
            print(f"⌨️ Touche: {key}")
            return True
        except Exception as e:
            print(f"❌ Erreur touche: {e}")
            return False
    
    def hotkey(self, *keys):
        """Raccourci clavier (ex: ctrl+c)"""
        try:
            pyautogui.hotkey(*keys)
            print(f"⌨️ Raccourci: {'+'.join(keys)}")
            return True
        except Exception as e:
            print(f"❌ Erreur raccourci: {e}")
            return False
    
    def key_down(self, key):
        """Maintient une touche enfoncée"""
        try:
            pyautogui.keyDown(key)
            return True
        except Exception as e:
            print(f"❌ Erreur key_down: {e}")
            return False
    
    def key_up(self, key):
        """Relâche une touche"""
        try:
            pyautogui.keyUp(key)
            return True
        except Exception as e:
            print(f"❌ Erreur key_up: {e}")
            return False
    
    # ============================================
    # RECONNAISSANCE VISUELLE
    # ============================================
    
    def take_screenshot(self, filename=None, region=None):
        """
        Prend un screenshot
        Args:
            filename: nom du fichier (auto si None)
            region: (x, y, width, height) ou None pour tout l'écran
        Returns:
            Path: chemin du screenshot
        """
        try:
            if filename is None:
                filename = f"screenshot_{int(time.time())}.png"
            
            screenshot_path = self.screenshots_dir / filename
            
            if region:
                screenshot = pyautogui.screenshot(region=region)
            else:
                screenshot = pyautogui.screenshot()
            
            screenshot.save(screenshot_path)
            print(f"📸 Screenshot: {screenshot_path}")
            return screenshot_path
            
        except Exception as e:
            print(f"❌ Erreur screenshot: {e}")
            return None
    
    def locate_on_screen(self, image_path, confidence=0.8):
        """
        Trouve une image à l'écran
        Returns:
            tuple: (x, y, width, height) ou None
        """
        try:
            location = pyautogui.locateOnScreen(str(image_path), confidence=confidence)
            if location:
                print(f"🔍 Image trouvée: {location}")
            return location
        except Exception as e:
            print(f"❌ Erreur locate: {e}")
            return None
    
    def locate_center(self, image_path, confidence=0.8):
        """
        Trouve le centre d'une image à l'écran
        Returns:
            tuple: (x, y) ou None
        """
        try:
            center = pyautogui.locateCenterOnScreen(str(image_path), confidence=confidence)
            if center:
                print(f"🔍 Centre trouvé: {center}")
            return center
        except Exception as e:
            print(f"❌ Erreur locate_center: {e}")
            return None
    
    def click_on_image(self, image_path, confidence=0.8):
        """Clique sur une image si trouvée"""
        center = self.locate_center(image_path, confidence)
        if center:
            return self.click(center[0], center[1])
        return False
    
    # ============================================
    # INFO ÉCRAN
    # ============================================
    
    def get_screen_size(self):
        """Obtient la taille de l'écran"""
        return pyautogui.size()
    
    def get_pixel_color(self, x, y):
        """Obtient la couleur d'un pixel"""
        try:
            return pyautogui.pixel(x, y)
        except Exception as e:
            print(f"❌ Erreur pixel: {e}")
            return None
    
    # ============================================
    # ACTIONS COMPLEXES
    # ============================================
    
    def copy_to_clipboard(self):
        """Copie (Ctrl+C)"""
        return self.hotkey('ctrl', 'c')
    
    def paste_from_clipboard(self):
        """Colle (Ctrl+V)"""
        return self.hotkey('ctrl', 'v')
    
    def select_all(self):
        """Sélectionne tout (Ctrl+A)"""
        return self.hotkey('ctrl', 'a')
    
    def undo(self):
        """Annuler (Ctrl+Z)"""
        return self.hotkey('ctrl', 'z')
    
    def save(self):
        """Sauvegarder (Ctrl+S)"""
        return self.hotkey('ctrl', 's')
    
    def close_window(self):
        """Fermer fenêtre (Alt+F4)"""
        return self.hotkey('alt', 'F4')
    
    def switch_window(self):
        """Changer de fenêtre (Alt+Tab)"""
        return self.hotkey('alt', 'tab')
    
    def minimize_window(self):
        """Minimiser (Win+Down)"""
        return self.hotkey('win', 'down')
    
    def maximize_window(self):
        """Maximiser (Win+Up)"""
        return self.hotkey('win', 'up')
    
    # ============================================
    # UTILITAIRES
    # ============================================
    
    def wait(self, seconds):
        """Attendre"""
        time.sleep(seconds)
        return True
    
    def get_active_window_title(self):
        """Obtient le titre de la fenêtre active (Windows)"""
        try:
            import win32gui
            window = win32gui.GetForegroundWindow()
            return win32gui.GetWindowText(window)
        except Exception as e:
            print(f"⚠️ Impossible d'obtenir le titre: {e}")
            return None

