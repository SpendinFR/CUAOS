"""
Keyboard Controller pour CUA Agent
Gère les touches P/C/Q pour contrôle manuel pendant l'exécution
"""
import keyboard


class CUAKeyboardController:
    """Contrôleur clavier pour intervention manuelle utilisateur"""
    
    def __init__(self):
        self.paused = False
        self.stop_requested = False
        self._setup_hotkeys()
    
    def _setup_hotkeys(self):
        """Configure les raccourcis clavier globaux"""
        try:
            keyboard.on_press_key('p', self._on_pause)
            keyboard.on_press_key('c', self._on_continue)
            keyboard.on_press_key('q', self._on_quit)
        except Exception as e:
            print(f"[KeyboardController] Erreur configuration touches: {e}")
    
    def _on_pause(self, event):
        """Utilisateur demande à prendre le contrôle (touche P)"""
        if not self.paused:
            print("\n⏸️  [P] PAUSE - Contrôle utilisateur activé")
            print("    Faites vos actions manuelles...")
            print("    Appuyez sur [C] pour redonner le contrôle au CUA")
            self.paused = True
    
    def _on_continue(self, event):
        """Utilisateur redonne le contrôle au CUA (touche C)"""
        if self.paused:
            print("\n▶️  [C] CONTINUE - CUA reprend le contrôle")
            self.paused = False
    
    def _on_quit(self, event):
        """Arrêt complet (touche Q)"""
        print("\n🛑 [Q] QUIT - Arrêt demandé par l'utilisateur")
        self.stop_requested = True
    
    def cleanup(self):
        """Nettoie les hooks clavier"""
        try:
            keyboard.unhook_all()
        except Exception as e:
            print(f"[KeyboardController] Erreur cleanup: {e}")
