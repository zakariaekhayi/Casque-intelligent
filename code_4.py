import pygame
import pygame_gui
import speech_recognition as sr
from threading import Thread, Lock
import time
from PIL import Image, ImageDraw
import numpy as np

class MapDisplay:
    def __init__(self, width=800, height=600):
        pygame.init()
        self.width = width
        self.height = height
        self.window = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Carte Interactive")
        
        # Interface utilisateur
        self.ui_manager = pygame_gui.UIManager((width, height))
        self.clock = pygame.time.Clock()
        
        # État de la carte
        self.is_visible = False
        self.map_surface = self.create_dummy_map()

    def create_dummy_map(self):
        """Créer une carte de test basique"""
        # Créer une image de base
        img = Image.new('RGB', (self.width, self.height), color='lightblue')
        draw = ImageDraw.Draw(img)
        
        # Dessiner une grille simple
        for x in range(0, self.width, 50):
            draw.line([(x, 0), (x, self.height)], fill='white', width=1)
        for y in range(0, self.height, 50):
            draw.line([(0, y), (self.width, y)], fill='white', width=1)
        
        # Dessiner quelques "routes"
        draw.line([(200, 100), (600, 500)], fill='yellow', width=5)
        draw.line([(100, 300), (700, 300)], fill='yellow', width=5)
        
        # Convertir en surface PyGame
        return pygame.image.fromstring(img.tobytes(), img.size, img.mode)

    def show_map(self):
        """Afficher la carte"""
        print("Affichage de la carte...")
        self.is_visible = True

    def hide_map(self):
        """Masquer la carte"""
        print("Masquage de la carte...")
        self.is_visible = False
        self.window.fill((0, 0, 0))
        pygame.display.flip()

    def draw(self):
        """Dessiner la fenêtre"""
        self.window.fill((0, 0, 0))
        
        if self.is_visible:
            # Afficher la carte
            self.window.blit(self.map_surface, (0, 0))
            
            # Dessiner un marqueur pour la position actuelle
            pygame.draw.circle(self.window, (255, 0, 0), 
                             (self.width//2, self.height//2), 8)
            
            # Ajouter un texte d'information
            font = pygame.font.Font(None, 36)
            text = font.render("Carte active", True, (255, 255, 255))
            self.window.blit(text, (10, 10))
        
        self.ui_manager.draw_ui(self.window)
        pygame.display.flip()

class VoiceCommandManager:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.command_lock = Lock()
        self.current_command = None
        self.running = True
        
        # Commandes vocales
        self.commands = {
            "afficher la carte": "show_map",
            "éteindre la carte": "hide_map"
        }

    def start_listening(self):
        """Démarrer l'écoute en arrière-plan"""
        Thread(target=self._listen_loop, daemon=True).start()

    def _listen_loop(self):
        """Boucle d'écoute continue"""
        while self.running:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source)
                try:
                    audio = self.recognizer.listen(source, timeout=1)
                    text = self.recognizer.recognize_google(audio, language="fr-FR").lower()
                    print(f"Commande détectée: {text}")
                    
                    for command_text, command_action in self.commands.items():
                        if command_text in text:
                            with self.command_lock:
                                self.current_command = command_action
                                print(f"Commande enregistrée: {command_action}")
                except sr.WaitTimeoutError:
                    pass
                except sr.UnknownValueError:
                    pass
                except sr.RequestError:
                    print("Erreur de service de reconnaissance vocale")
                except Exception as e:
                    print(f"Erreur: {str(e)}")

    def get_command(self):
        """Récupérer la dernière commande"""
        with self.command_lock:
            command = self.current_command
            self.current_command = None
            return command

def main():
    try:
        # Initialisation
        map_display = MapDisplay()
        voice_manager = VoiceCommandManager()
        voice_manager.start_listening()
        
        print("Application démarrée. Commandes vocales disponibles:")
        print("- 'afficher la carte' : affiche la carte")
        print("- 'éteindre la carte' : masque la carte")
        print("Appuyez sur Échap pour quitter")

        running = True
        while running:
            time_delta = map_display.clock.tick(60)/1000.0

            # Gestion des événements
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    # Test des commandes avec les touches
                    elif event.key == pygame.K_SPACE:
                        map_display.show_map()
                    elif event.key == pygame.K_h:
                        map_display.hide_map()
                
                map_display.ui_manager.process_events(event)

            # Traitement des commandes vocales
            command = voice_manager.get_command()
            if command:
                print(f"Exécution de la commande: {command}")
                if command == "show_map":
                    map_display.show_map()
                elif command == "hide_map":
                    map_display.hide_map()

            # Mise à jour et dessin
            map_display.ui_manager.update(time_delta)
            map_display.draw()

    except Exception as e:
        print(f"Erreur principale: {str(e)}")
    finally:
        pygame.quit()

if __name__ == "__main__":
    main()