import json
import math
from pathlib import Path

import pygame


SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
FPS = 60
TILE = 32
APP_DIR = Path(__file__).resolve().parent
PROFILE_FILE = APP_DIR / "profiles.json"


COLORS = {
    "bg": (15, 18, 28),
    "panel": (28, 35, 48),
    "panel_2": (40, 52, 70),
    "text": (234, 242, 250),
    "muted": (160, 176, 190),
    "accent": (80, 210, 190),
    "accent_2": (238, 180, 76),
    "danger": (220, 84, 88),
    "wall": (56, 68, 84),
    "wall_top": (80, 94, 112),
    "door_closed": (126, 76, 45),
    "door_open": (54, 160, 112),
    "player": (255, 221, 135),
    "shadow": (5, 8, 12),
}


TOPICS = {
    "Haandtering af sundhedsdata": (
        "I 2050 kan Sundhedsstyrelsen bruge sundhedsdata til at opdage sygdom tidligere "
        "og planlaegge bedre forebyggelse. Teknologien er vigtig, men data skal indsamles "
        "med samtykke, klart formaal og staerk sikkerhed, saa borgernes privatliv bevares."
    ),
    "Genetisk screening": (
        "Genetisk screening kan vise risiko for sygdom, foer symptomer opstaar. Det kan "
        "give tidlig forebyggelse og personlig medicin, men det rejser dilemmaer om "
        "bekymring, diskrimination og hvem der maa kende ens genetiske oplysninger."
    ),
    "Adgang til behandling": (
        "Digitale systemer kan hjaelpe med at prioritere behandling, naar ressourcerne er "
        "pressede. Det kan skabe mere retfaerdige beslutninger, men systemet skal kunne "
        "forklares og maa ikke overse mennesker, der ikke passer ind i dataenes moenstre."
    ),
    "Overvaagning af borgere": (
        "Sensorer og digitale sundhedsloesninger kan advare om sygdomsudbrud og farlige "
        "moenstre. De kan beskytte folkesundheden, men de kan ogsaa foeles som kontrol, "
        "hvis borgerne ikke har indsigt, valgmuligheder og rettigheder."
    ),
    "Personlig medicin": (
        "Personlig medicin bruger gener, livsstil og sundhedsdata til at vaelge behandling "
        "til den enkelte. Det kan give bedre virkning og faerre bivirkninger, men kraever "
        "ansvarlig brug af meget foelsomme data."
    ),
    "Bioteknologiske dilemmaer": (
        "Bioteknologi giver nye muligheder for forebyggelse og behandling, men hver ny "
        "mulighed skaber ogsaa valg: Hvem faar adgang? Hvem bestemmer? Og hvor meget "
        "data maa samfundet bruge for at beskytte sundheden?"
    ),
}


def draw_text(surface, text, font, color, rect, line_spacing=4, center=False):
    """Draw wrapped text inside rect and return the next y position."""
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = f"{current} {word}".strip()
        if font.size(test)[0] <= rect.width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)

    total_h = len(lines) * font.get_height() + max(0, len(lines) - 1) * line_spacing
    y = rect.y + (rect.height - total_h) // 2 if center else rect.y
    for line in lines:
        rendered = font.render(line, False, color)
        x = rect.centerx - rendered.get_width() // 2 if center else rect.x
        surface.blit(rendered, (x, y))
        y += font.get_height() + line_spacing
    return y


class UserProfile:
    last_error = ""

    def __init__(self, name, data=None):
        self.name = name.strip()
        data = data or {}
        self.current_room = data.get("current_room", 0)
        self.selected_topic = data.get("selected_topic")
        self.knowledge_pieces = data.get("knowledge_pieces", [])
        self.solved = data.get("solved", {})
        self.completed = data.get("completed", False)

    def to_dict(self):
        return {
            "current_room": self.current_room,
            "selected_topic": self.selected_topic,
            "knowledge_pieces": self.knowledge_pieces,
            "solved": self.solved,
            "completed": self.completed,
        }

    @staticmethod
    def load_all():
        UserProfile.last_error = ""
        if not PROFILE_FILE.exists():
            return {}
        try:
            return json.loads(PROFILE_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}

    @staticmethod
    def save_all(profiles):
        UserProfile.last_error = ""
        try:
            PROFILE_FILE.parent.mkdir(parents=True, exist_ok=True)
            PROFILE_FILE.write_text(json.dumps(profiles, indent=2, ensure_ascii=False), encoding="utf-8")
        except OSError as exc:
            UserProfile.last_error = f"Kunne ikke gemme profil i {PROFILE_FILE}: {exc}"

    @classmethod
    def load(cls, name):
        profiles = cls.load_all()
        return cls(name, profiles.get(name, {}))

    def save(self):
        profiles = self.load_all()
        profiles[self.name] = self.to_dict()
        self.save_all(profiles)


class Button:
    def __init__(self, rect, text, action):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.action = action

    def draw(self, surface, font):
        mouse = pygame.mouse.get_pos()
        hover = self.rect.collidepoint(mouse)
        color = COLORS["accent"] if hover else COLORS["panel_2"]
        pygame.draw.rect(surface, color, self.rect, border_radius=4)
        pygame.draw.rect(surface, (110, 130, 150), self.rect, 2, border_radius=4)
        label = font.render(self.text, False, COLORS["text"])
        surface.blit(label, label.get_rect(center=self.rect.center))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos):
            self.action()


class Door:
    def __init__(self, door_id, room_a, room_b, x, y, orientation, quiz_id, label):
        self.door_id = door_id
        self.room_a = room_a
        self.room_b = room_b
        self.x = x
        self.y = y
        self.orientation = orientation
        self.quiz_id = quiz_id
        self.label = label
        self.open = False
        self.length = 116
        self.thickness = 24

    @property
    def gate_rect(self):
        if self.orientation == "vertical":
            return pygame.Rect(self.x - self.thickness // 2, self.y - self.length // 2, self.thickness, self.length)
        return pygame.Rect(self.x - self.length // 2, self.y - self.thickness // 2, self.length, self.thickness)

    @property
    def passage_rect(self):
        if self.orientation == "vertical":
            return self.gate_rect.inflate(112, 28)
        return self.gate_rect.inflate(28, 112)

    def draw(self, surface, camera):
        rect = self.gate_rect.move(-camera.x, -camera.y)
        passage = self.passage_rect.move(-camera.x, -camera.y)
        if self.open:
            pygame.draw.rect(surface, (38, 58, 54), passage)
            pygame.draw.rect(surface, (78, 130, 105), passage, 2)
        color = COLORS["door_open"] if self.open else COLORS["door_closed"]
        pygame.draw.rect(surface, color, rect)
        edge = (190, 230, 200) if self.open else (76, 45, 28)
        pygame.draw.rect(surface, edge, rect, 3)
        if not self.open:
            lock_rect = pygame.Rect(0, 0, 14, 18)
            lock_rect.center = rect.center
            pygame.draw.rect(surface, COLORS["accent_2"], lock_rect)
            pygame.draw.rect(surface, (60, 44, 30), lock_rect, 2)
            pygame.draw.rect(surface, (60, 44, 30), (lock_rect.x + 3, lock_rect.y - 8, 8, 10), 2)
        else:
            light = pygame.Rect(0, 0, 10, 10)
            light.center = rect.center
            pygame.draw.rect(surface, (145, 255, 190), light)

        if self.open:
            for i in range(3):
                if self.orientation == "vertical":
                    pygame.draw.line(surface, (120, 245, 190), (rect.x + 4, rect.y + 18 + i * 28), (rect.right - 4, rect.y + 10 + i * 28), 2)
                else:
                    pygame.draw.line(surface, (120, 245, 190), (rect.x + 18 + i * 28, rect.y + 4), (rect.x + 10 + i * 28, rect.bottom - 4), 2)

    def connects(self, room_a, room_b):
        return {self.room_a, self.room_b} == {room_a, room_b}

    def can_cross(self, point):
        if not self.open:
            return False
        if self.orientation == "vertical":
            return abs(point[1] - self.y) <= self.length // 2 - 8
        return abs(point[0] - self.x) <= self.length // 2 - 8


class Interactable:
    def __init__(self, name, rect, prompt, text, kind="info", quiz=None, color=(70, 120, 150), symbol=""):
        self.name = name
        self.rect = pygame.Rect(rect)
        self.prompt = prompt
        self.text = text
        self.kind = kind
        self.quiz = quiz
        self.color = color
        self.symbol = symbol
        self.used = False

    def draw(self, surface, camera, font):
        rect = self.rect.move(-camera.x, -camera.y)
        dark = tuple(max(0, c - 36) for c in self.color)
        light = tuple(min(255, c + 42) for c in self.color)
        pygame.draw.rect(surface, dark, rect)
        pygame.draw.rect(surface, self.color, rect.inflate(-6, -6))
        pygame.draw.rect(surface, light, (rect.x + 5, rect.y + 5, max(4, rect.width - 16), 5))
        pygame.draw.rect(surface, (22, 28, 38), rect, 3)
        self.draw_pixel_details(surface, rect)

    def is_near(self, player_rect):
        reach = self.rect.inflate(52, 52)
        return reach.colliderect(player_rect)

    def draw_pixel_details(self, surface, rect):
        key = f"{self.name} {self.symbol}".lower()
        if "behandlingsskab" in key or "vaccinekoeler" in key:
            for i, color in enumerate([(80, 210, 190), (238, 180, 76), (220, 84, 88)]):
                shelf = pygame.Rect(rect.x + 16, rect.y + 18 + i * 22, rect.width - 32, 14)
                pygame.draw.rect(surface, (30, 38, 48), shelf)
                pygame.draw.rect(surface, color, (shelf.x + 8, shelf.y + 3, shelf.width - 16, 8))
            pygame.draw.rect(surface, (220, 235, 240), (rect.right - 26, rect.y + 14, 10, rect.height - 28))
        elif "overvagningsnotat" in key or "overvaagningsnotat" in key:
            paper = pygame.Rect(rect.x + 16, rect.y + 12, rect.width - 32, rect.height - 24)
            pygame.draw.rect(surface, (220, 226, 206), paper)
            pygame.draw.rect(surface, (70, 78, 70), paper, 2)
            for i in range(3):
                pygame.draw.circle(surface, (80, 210, 190), (paper.x + 20 + i * 34, paper.y + 22), 7)
                pygame.draw.line(surface, (80, 210, 190), (paper.x + 20 + i * 34, paper.y + 29), (paper.x + 20 + i * 34, paper.y + 48), 2)
            pygame.draw.rect(surface, (220, 84, 88), (paper.right - 32, paper.bottom - 22, 18, 10))
        elif "sensorvaeg" in key:
            for i in range(4):
                x = rect.x + 22 + i * 34
                pygame.draw.circle(surface, (80, 210, 190), (x, rect.y + 35), 10)
                pygame.draw.line(surface, (80, 210, 190), (x, rect.y + 45), (rect.centerx, rect.bottom - 24), 2)
            pygame.draw.rect(surface, (12, 18, 26), (rect.centerx - 28, rect.bottom - 42, 56, 24))
            pygame.draw.rect(surface, COLORS["accent_2"], (rect.centerx - 18, rect.bottom - 34, 36, 8))
        elif "samtykkeskab" in key:
            pygame.draw.rect(surface, (36, 44, 54), (rect.x + 14, rect.y + 14, rect.width - 28, rect.height - 28))
            for i, color in enumerate([COLORS["accent"], COLORS["accent_2"], (160, 190, 230)]):
                card = pygame.Rect(rect.x + 24 + i * 34, rect.y + 28, 24, 38)
                pygame.draw.rect(surface, (230, 235, 220), card)
                pygame.draw.rect(surface, color, (card.x + 5, card.y + 8, 14, 5))
                pygame.draw.rect(surface, color, (card.x + 5, card.y + 20, 14, 5))
        elif "behandlingsmodel" in key or "prioriteringstavle" in key:
            pygame.draw.rect(surface, (10, 18, 28), (rect.x + 12, rect.y + 14, rect.width - 24, rect.height - 28))
            bars = [(COLORS["accent"], 70), (COLORS["accent_2"], 48), ((220, 84, 88), 34)]
            for i, (color, width) in enumerate(bars):
                pygame.draw.rect(surface, color, (rect.x + 28, rect.y + 28 + i * 20, width, 8))
                pygame.draw.rect(surface, (210, 220, 225), (rect.right - 54, rect.y + 24 + i * 20, 18, 18), 2)
        elif "data-dashboard" in key or "serverrack" in key:
            pygame.draw.rect(surface, (10, 18, 28), (rect.x + 14, rect.y + 14, rect.width - 28, rect.height - 28))
            for i in range(4):
                pygame.draw.rect(surface, COLORS["accent"], (rect.x + 26, rect.y + 26 + i * 16, 34 + i * 12, 6))
            for i in range(3):
                pygame.draw.rect(surface, COLORS["accent_2"], (rect.right - 42, rect.y + 26 + i * 20, 14, 10))
        elif "screening" in key or "dna" in key:
            for i in range(0, rect.width - 24, 20):
                y1 = rect.y + 16 + (i // 20 % 2) * 24
                y2 = rect.bottom - 18 - (i // 20 % 2) * 24
                pygame.draw.line(surface, (165, 235, 220), (rect.x + 12 + i, y1), (rect.x + 24 + i, y2), 3)
                pygame.draw.rect(surface, COLORS["accent_2"], (rect.x + 14 + i, (y1 + y2) // 2, 12, 4))
        elif "velkomst" in key or "terminal" in key or "skaerm" in key or "ai" in key or "visitation" in key:
            pygame.draw.rect(surface, (10, 18, 28), (rect.x + 12, rect.y + 14, rect.width - 24, max(20, rect.height // 2)))
            for i in range(4):
                pygame.draw.rect(surface, COLORS["accent"], (rect.x + 20 + i * 18, rect.y + 22 + (i % 2) * 10, 12, 4))
            pygame.draw.rect(surface, (38, 45, 58), (rect.centerx - 18, rect.bottom - 22, 36, 8))
        elif "plakat" in key or "note" in key:
            paper = pygame.Rect(rect.x + 16, rect.y + 12, rect.width - 32, rect.height - 24)
            pygame.draw.rect(surface, (224, 214, 172), paper)
            pygame.draw.rect(surface, (80, 70, 48), paper, 2)
            for i in range(4):
                pygame.draw.rect(surface, (120, 105, 76), (paper.x + 10, paper.y + 10 + i * 13, paper.width - 20, 4))
            if "antibiotika" in key:
                pygame.draw.rect(surface, (185, 70, 74), (paper.centerx - 18, paper.bottom - 24, 36, 8))
                pygame.draw.rect(surface, (185, 70, 74), (paper.centerx - 4, paper.bottom - 38, 8, 36))
        elif "ur" in key:
            face = pygame.Rect(rect.centerx - 28, rect.centery - 24, 56, 42)
            pygame.draw.rect(surface, (12, 22, 26), face)
            for i in range(4):
                pygame.draw.rect(surface, COLORS["accent"], (face.x + 8 + i * 11, face.y + 12, 7, 18))
            pygame.draw.rect(surface, (45, 60, 65), (rect.centerx - 34, rect.bottom - 16, 68, 8))
        elif "wearable" in key:
            for i in range(3):
                x = rect.x + 18 + i * 35
                pygame.draw.rect(surface, (25, 32, 42), (x, rect.y + 22, 24, 48))
                pygame.draw.rect(surface, COLORS["accent"], (x + 5, rect.y + 34, 14, 14))
                pygame.draw.rect(surface, (90, 105, 118), (x + 7, rect.y + 12, 10, 12))
                pygame.draw.rect(surface, (90, 105, 118), (x + 7, rect.y + 70, 10, 12))
        elif self.kind == "quiz" or "tastatur" in key or "quiz" in key or "panel" in key:
            pygame.draw.rect(surface, (12, 18, 26), (rect.x + 10, rect.y + 10, rect.width - 20, max(14, rect.height // 3)))
            for i in range(3):
                for j in range(2):
                    pygame.draw.rect(surface, COLORS["accent_2"], (rect.x + 12 + i * 14, rect.bottom - 28 + j * 10, 8, 6))
        elif "dna" in key:
            for i in range(0, rect.width - 18, 18):
                y1 = rect.y + 14 + (i // 18 % 2) * 16
                y2 = rect.bottom - 18 - (i // 18 % 2) * 16
                pygame.draw.line(surface, (165, 235, 220), (rect.x + 10 + i, y1), (rect.x + 18 + i, y2), 3)
                pygame.draw.rect(surface, (238, 180, 76), (rect.x + 11 + i, (y1 + y2) // 2, 10, 4))
        elif "plante" in key or self.symbol == "PL":
            pygame.draw.rect(surface, (88, 58, 38), (rect.centerx - 10, rect.bottom - 20, 20, 14))
            for dx, dy in [(-12, -38), (4, -44), (14, -31), (-2, -28)]:
                pygame.draw.rect(surface, (82, 180, 92), (rect.centerx + dx, rect.bottom + dy, 14, 18))
        elif "mikroskop" in key or self.symbol == "MIC":
            pygame.draw.rect(surface, (34, 42, 54), (rect.centerx - 6, rect.y + 18, 12, 34))
            pygame.draw.rect(surface, (190, 210, 220), (rect.centerx + 4, rect.y + 10, 18, 10))
            pygame.draw.rect(surface, (34, 42, 54), (rect.centerx - 22, rect.bottom - 16, 44, 8))
        elif "kaffe" in key or "kop" in key:
            pygame.draw.rect(surface, (238, 220, 175), (rect.centerx - 12, rect.centery - 8, 20, 18))
            pygame.draw.rect(surface, (70, 42, 28), (rect.centerx - 8, rect.centery - 5, 12, 5))
            pygame.draw.rect(surface, (238, 220, 175), (rect.centerx + 9, rect.centery - 3, 7, 9), 2)
        elif "robot" in key or self.symbol == "ARM":
            pygame.draw.rect(surface, (190, 200, 210), (rect.x + 14, rect.y + 16, 18, 12))
            pygame.draw.rect(surface, (170, 180, 190), (rect.x + 30, rect.y + 28, 28, 12))
            pygame.draw.rect(surface, (215, 225, 230), (rect.x + 52, rect.y + 38, 12, 24))
        elif "vaccine" in key or self.symbol == "VAC":
            for i in range(3):
                pygame.draw.rect(surface, (205, 235, 245), (rect.x + 22 + i * 34, rect.y + 18, 14, 46))
                pygame.draw.rect(surface, (85, 170, 210), (rect.x + 24 + i * 34, rect.y + 42, 10, 16))
        elif "batter" in key or self.symbol == "BAT":
            for i in range(3):
                pygame.draw.rect(surface, (45, 52, 60), (rect.x + 12 + i * 26, rect.centery - 10, 18, 22))
                pygame.draw.rect(surface, COLORS["accent"], (rect.x + 27 + i * 26, rect.centery - 4, 4, 10))
        elif "ventestole" in key:
            for i in range(3):
                x = rect.x + 16 + i * 42
                pygame.draw.rect(surface, (55, 60, 82), (x, rect.y + 14, 30, 24))
                pygame.draw.rect(surface, (42, 45, 62), (x, rect.y + 38, 30, 12))
                pygame.draw.rect(surface, (30, 34, 44), (x + 4, rect.y + 50, 5, 8))
                pygame.draw.rect(surface, (30, 34, 44), (x + 22, rect.y + 50, 5, 8))
        elif "haandvask" in key:
            pygame.draw.rect(surface, (200, 225, 225), (rect.centerx - 25, rect.centery - 8, 50, 22))
            pygame.draw.rect(surface, (70, 95, 105), (rect.centerx - 6, rect.y + 12, 12, 22))
            pygame.draw.rect(surface, COLORS["accent"], (rect.centerx + 10, rect.centery + 2, 8, 8))
        elif "arkivkasser" in key:
            for i in range(3):
                box = pygame.Rect(rect.x + 12 + i * 44, rect.y + 16 + (i % 2) * 8, 36, 30)
                pygame.draw.rect(surface, (150, 112, 70), box)
                pygame.draw.rect(surface, (76, 54, 34), box, 2)
                pygame.draw.rect(surface, (222, 205, 155), (box.x + 10, box.y + 8, 16, 5))
        elif "lampe" in key:
            pygame.draw.rect(surface, (60, 52, 35), (rect.centerx - 4, rect.y + 18, 8, 38))
            pygame.draw.rect(surface, (235, 205, 92), (rect.centerx - 18, rect.y + 10, 36, 18))
            pygame.draw.rect(surface, (245, 225, 120), (rect.centerx - 24, rect.y + 28, 48, 8))
        elif "printer" in key:
            pygame.draw.rect(surface, (210, 216, 220), (rect.x + 18, rect.y + 22, rect.width - 36, 28))
            pygame.draw.rect(surface, (35, 42, 52), (rect.x + 28, rect.y + 12, rect.width - 56, 16))
            pygame.draw.rect(surface, (238, 238, 220), (rect.x + 32, rect.y + 48, rect.width - 64, 18))
        elif "lysvaeg" in key:
            colors = [(80, 210, 190), (238, 180, 76), (120, 150, 230), (220, 84, 88)]
            for y in range(2):
                for x in range(5):
                    pygame.draw.rect(surface, colors[(x + y) % len(colors)], (rect.x + 12 + x * 22, rect.y + 14 + y * 20, 16, 14))
        else:
            highlight = tuple(min(255, c + 48) for c in self.color)
            for i in range(3):
                pygame.draw.rect(surface, highlight, (rect.x + 14 + i * 18, rect.y + 18 + (i % 2) * 14, 10, 10))


class Quiz:
    def __init__(self, quiz_id, title, question, options, correct, reward_piece=None, code_answer=None, puzzle_type="choice", input_hint="Skriv svar..."):
        self.quiz_id = quiz_id
        self.title = title
        self.question = question
        self.options = options
        self.correct = correct
        self.reward_piece = reward_piece
        self.code_answer = code_answer
        self.puzzle_type = puzzle_type
        self.input_hint = input_hint
        self.input_text = ""
        self.feedback = ""

    def answer(self, value):
        if self.code_answer is not None:
            ok = value.strip().lower() == self.code_answer.lower()
        else:
            ok = value == self.correct
        self.feedback = "Korrekt! Doeren aabner, og du fik en vidensbrik." if ok else "Ikke helt. Kig paa ledetraden og proev igen."
        return ok


class Room:
    def __init__(self, index, name, rect, floor_color, wall_color, intro):
        self.index = index
        self.name = name
        self.rect = pygame.Rect(rect)
        self.floor_color = floor_color
        self.wall_color = wall_color
        self.intro = intro
        self.interactables = []
        self.doors = []

    def add(self, interactable):
        self.interactables.append(interactable)

    def add_door(self, door):
        self.doors.append(door)

    def draw_floor(self, surface, camera):
        r = self.rect.move(-camera.x, -camera.y)
        pygame.draw.rect(surface, self.floor_color, r)
        for y in range(r.y, r.bottom, TILE):
            offset = ((y // TILE) % 2) * 8
            pygame.draw.line(surface, tuple(max(0, c - 18) for c in self.floor_color), (r.x + offset, y), (r.right, y - 18), 1)
        pygame.draw.rect(surface, self.wall_color, (r.x, r.y, r.width, 28))
        pygame.draw.rect(surface, COLORS["wall_top"], (r.x, r.y, r.width, 12))
        pygame.draw.rect(surface, self.wall_color, (r.x, r.bottom - 28, r.width, 28))
        pygame.draw.rect(surface, self.wall_color, (r.x, r.y, 28, r.height))
        pygame.draw.rect(surface, self.wall_color, (r.right - 28, r.y, 28, r.height))

    def draw_objects(self, surface, camera, font):
        for item in self.interactables:
            item.draw(surface, camera, font)


class Player:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 28, 34)
        self.speed = 3.4
        self.facing = pygame.Vector2(0, 1)

    def move(self, keys, rooms, doors):
        dx = dy = 0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= self.speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += self.speed
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy -= self.speed
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy += self.speed

        if dx and dy:
            dx *= 0.7071
            dy *= 0.7071
        if dx or dy:
            self.facing = pygame.Vector2(dx, dy)

        self.try_move(dx, 0, rooms, doors)
        self.try_move(0, dy, rooms, doors)

    def try_move(self, dx, dy, rooms, doors):
        new_rect = self.rect.move(dx, dy)
        old_room = room_at_point(rooms, self.rect.center)
        new_room = room_at_point(rooms, new_rect.center)
        if new_room is None:
            return
        if old_room and new_room.index != old_room.index:
            door = self.find_crossing_door(old_room.index, new_room.index, doors)
            if not door or not door.can_cross(new_rect.center):
                return
        wall_margin = 32
        inner = new_room.rect.inflate(-wall_margin * 2, -wall_margin * 2)
        if inner.contains(new_rect) or self.in_open_door_corridor(new_rect, doors) or (old_room and new_room.index != old_room.index):
            self.rect = new_rect

    def find_crossing_door(self, old_room_index, new_room_index, doors):
        for door in doors:
            if door.connects(old_room_index, new_room_index):
                return door
        return None

    def in_open_door_corridor(self, rect, doors):
        for door in doors:
            if door.open and door.passage_rect.colliderect(rect):
                return True
        return False

    def draw(self, surface, camera):
        x = self.rect.x - camera.x
        y = self.rect.y - camera.y
        pygame.draw.ellipse(surface, COLORS["shadow"], (x - 2, y + 24, 32, 12))
        pygame.draw.rect(surface, (58, 110, 165), (x + 6, y + 14, 16, 18))
        pygame.draw.rect(surface, COLORS["player"], (x + 5, y + 3, 18, 17))
        pygame.draw.rect(surface, (36, 45, 58), (x + 4, y, 20, 7))
        pygame.draw.rect(surface, (28, 34, 46), (x + 8, y + 31, 5, 6))
        pygame.draw.rect(surface, (28, 34, 46), (x + 17, y + 31, 5, 6))


def room_at_point(rooms, point):
    for room in rooms:
        if room.rect.collidepoint(point):
            return room
    return None


class Game:
    def __init__(self):
        global SCREEN_WIDTH, SCREEN_HEIGHT
        pygame.init()
        pygame.display.set_caption("Sundhedsstyrelsen 2050")
        display_info = pygame.display.Info()
        SCREEN_WIDTH = max(900, display_info.current_w)
        SCREEN_HEIGHT = max(650, display_info.current_h)
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 20)
        self.small_font = pygame.font.SysFont("consolas", 16)
        self.big_font = pygame.font.SysFont("consolas", 44, bold=True)
        self.mid_font = pygame.font.SysFont("consolas", 26, bold=True)
        self.state = "menu"
        self.running = True
        self.profile = None
        self.profile_name_input = ""
        self.message = ""
        self.active_text = None
        self.active_quiz = None
        self.topic_buttons = []
        self.buttons = []
        self.rooms = self.create_rooms()
        self.doors = []
        for room in self.rooms:
            for door in room.doors:
                if door not in self.doors:
                    self.doors.append(door)
        self.player = Player(self.rooms[0].rect.x + 110, self.rooms[0].rect.y + 260)
        self.camera = pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
        self.refresh_menu_buttons()

    def create_rooms(self):
        rooms = []
        names = [
            ("Briefingrum 2050", (38, 58, 68), (60, 78, 92), "Sundhedsstyrelsen beder dig vaelge en vej gennem fremtidens sundhedsdilemmaer."),
            ("Digital visitation", (36, 70, 82), (54, 82, 96), "Her vaelger du mellem genetisk screening og behandling/overvaagning."),
            ("Genetisk screening", (54, 62, 82), (72, 78, 105), "Et bioteknologisk rum om DNA, risiko og retten til ikke at vide alt."),
            ("Screening-slutrum", (68, 54, 86), (90, 76, 110), "Enden paa screening-ruten: genetiske data og personlig medicin."),
            ("Borgerdata-arkiv", (52, 66, 58), (72, 88, 78), "En rute om sundhedsdata, samtykke og digital identitet."),
            ("Behandlingsraadet", (72, 58, 62), (94, 76, 82), "Et rum om prioritering, adgang til behandling og borgerovervaagning."),
            ("Data-slutrum", (46, 70, 62), (66, 92, 78), "Enden paa data-ruten: ansvarlig haandtering af sundhedsdata."),
            ("Behandling-slutrum", (38, 62, 86), (58, 84, 108), "Enden paa behandlings-ruten: retfaerdig adgang og AI-stoette."),
            ("Overvaagnings-slutrum", (78, 58, 58), (104, 78, 78), "Enden paa overvaagnings-ruten: folkesundhed, sensorer og frihed."),
        ]
        positions = [
            (0, 70),
            (720, 70),
            (720, 590),
            (720, 1110),
            (0, 590),
            (1440, 70),
            (0, 1110),
            (2160, 70),
            (1440, 590),
        ]
        for i, (name, floor, wall, intro) in enumerate(names):
            rect = pygame.Rect(positions[i][0], positions[i][1], 720, 520)
            room = Room(i, name, rect, floor, wall, intro)
            rooms.append(room)

        def add_door(door_id, a, b, edge, offset, quiz_id, label):
            ra = rooms[a].rect
            if edge == "east":
                x, y, orientation = ra.right, ra.y + offset, "vertical"
            elif edge == "south":
                x, y, orientation = ra.x + offset, ra.bottom, "horizontal"
            else:
                raise ValueError("Door edge must be east or south")
            door = Door(door_id, a, b, x, y, orientation, quiz_id, label)
            rooms[a].add_door(door)
            rooms[b].add_door(door)
            return door

        add_door("door_intro_health", 0, 1, "east", 230, "intro_code", "2050")
        add_door("door_intro_data", 0, 4, "south", 360, "intro_data_code", "DATA")
        add_door("door_health_bio", 1, 2, "south", 375, "screening_quiz", "DNA")
        add_door("door_health_clinic", 1, 5, "east", 250, "visitation_quiz", "RET")
        add_door("door_data_end", 4, 6, "south", 360, "data_privacy_quiz", "SAMTYKKE")
        add_door("door_bio_end", 2, 3, "south", 360, "bio_sequence", "DNA")
        add_door("door_clinic_ai_end", 5, 7, "east", 250, "treatment_quiz", "RET")
        add_door("door_clinic_immun_end", 5, 8, "south", 360, "monitoring_quiz", "SENSOR")

        rooms[0].add(Interactable(
            "Velkomstskaerm",
            (135, 155, 160, 90),
            "Tryk E: laes mission",
            "Aar 2050: Sundhedsstyrelsen tester et undervisningssystem om bioteknologiske dilemmaer. Vælg en rute og vurder muligheder og risici.",
            color=(42, 116, 145),
            symbol="LAB",
        ))
        rooms[0].add(Interactable(
            "Kodeplakat",
            (415, 135, 150, 100),
            "Tryk E: undersoeg plakat",
            "Plakaten viser tidslinjen 2020 -> 2035 -> 2050. Kun det sidste aar er markeret som fremtidsscenariet.",
            color=(136, 105, 58),
            symbol="2042",
        ))
        rooms[0].add(Interactable(
            "Data-ur",
            (305, 390, 120, 70),
            "Tryk E: se ur",
            "Uret blinker fire symboler: Data, Etik, Lighed og Test. Startbogstaverne danner koden til arkivruten.",
            color=(70, 120, 98),
            symbol="DATA",
        ))
        rooms[0].add(Interactable(
            "Oestligt tastatur",
            (605, 260, 70, 70),
            "Tryk E: laas oestdoer",
            "Panelet vil have aarstallet for fremtidsscenariet.",
            kind="quiz",
            quiz=Quiz("intro_code", "Fremtidskode", "Hvilket aar foregaar Sundhedsstyrelsens escape room i?", [], 0, "Briefing", code_answer="2050"),
            color=(72, 92, 112),
            symbol="#",
        ))
        rooms[0].add(Interactable(
            "Sydligt tastatur",
            (395, 485, 70, 58),
            "Tryk E: laas syddoer",
            "Panelet vil have fire bogstaver fra urets dilemma-symboler.",
            kind="quiz",
            quiz=Quiz("intro_data_code", "Arkivkode", "Skriv startbogstaverne fra Data, Etik, Lighed og Test.", [], 0, "Data-rute", code_answer="delt"),
            color=(72, 92, 112),
            symbol=">",
        ))
        rooms[0].add(Interactable("Kaffekop", (80, 430, 42, 42), "Tryk E: kig", "En halvkold kop kakao staar ved arbejdsbordet. Nogen har haft en lang laboratoriedag.", color=(110, 86, 62), symbol="KOP"))
        rooms[0].add(Interactable("Plante", (545, 130, 50, 70), "Tryk E: kig", "En robust plante vokser under kunstigt lys ved siden af en lille sensor.", color=(60, 125, 72), symbol="PL"))

        base_x = 720
        rooms[1].add(Interactable(
            "Wearable-station",
            (base_x + 95, 155, 135, 95),
            "Tryk E: scan udstyr",
            "Stationen viser en borger med mange maalinger: puls, soevn, medicin og transport. Systemet foreslaar forebyggelse, men dataene er meget private.",
            color=(58, 135, 120),
            symbol="HR",
        ))
        rooms[1].add(Interactable(
            "AI-skaerm",
            (base_x + 355, 120, 185, 92),
            "Tryk E: laes AI-note",
            "AI-noten viser en venteliste. Modellen foreslaar prioritet ud fra risiko, effekt og ventetid, men borgeren skal kunne forstaa beslutningen.",
            color=(52, 88, 155),
            symbol="AI",
        ))
        rooms[1].add(Interactable(
            "Triage-note",
            (base_x + 325, 315, 155, 72),
            "Tryk E: laes note",
            "Noten siger: Adgang til behandling maa ikke kun afhaenge af, hvem der har mest data. Systemet skal ogsaa opdage skaeve data.",
            color=(92, 104, 138),
            symbol="TRI",
        ))
        rooms[1].add(Interactable(
            "Screening-panel",
            (base_x + 395, 485, 85, 58),
            "Tryk E: aabn syddoer",
            "Byg den ansvarlige screening-proces.",
            kind="quiz",
            quiz=Quiz(
                "screening_quiz",
                "Screening-proces",
                "Genetisk screening maa ikke starte med et svar uden kontekst. Skriv kortenes ansvarlige raekkefoelge.",
                ["Informeret valg", "Genetisk test", "Raadgivning", "Del offentligt"],
                0,
                "Genetisk screening",
                code_answer="1-2-3",
                puzzle_type="sequence",
                input_hint="fx 1-2-3",
            ),
            color=(95, 115, 150),
            symbol="?",
        ))
        rooms[1].add(Interactable(
            "Visitationstavle",
            (base_x + 590, 275, 85, 80),
            "Tryk E: aabn oestdoer",
            "Vurder hvad en retfaerdig digital visitation skal bygge paa.",
            kind="quiz",
            quiz=Quiz(
                "visitation_quiz",
                "Visitation",
                "Ventelisten skal sorteres. Vaelg den raekkefoelge, der giver en mere retfaerdig beslutning.",
                [
                    "Tjek datakvalitet",
                    "Beregn risiko og effekt",
                    "Fagperson forklarer beslutning",
                    "Prioriter dem med flest wearables",
                ],
                0,
                "Adgang til behandling",
                code_answer="1-2-3",
                puzzle_type="sequence",
                input_hint="trin 1-2-3",
            ),
            color=(85, 108, 155),
            symbol="AI?",
        ))
        rooms[1].add(Interactable("Reservebatterier", (base_x + 115, 420, 95, 55), "Tryk E: kig", "En kasse med batterier til sensorer, smartwatches og mobile maaleenheder.", color=(126, 112, 62), symbol="BAT"))
        rooms[1].add(Interactable("Robotarm", (base_x + 535, 145, 80, 75), "Tryk E: kig", "Robotarmen flytter proever langsomt og praecist mellem to stationer.", color=(116, 118, 128), symbol="ARM"))

        base_x = 1440
        rooms[5].add(Interactable(
            "Vaccinekoeler",
            (base_x + 95, 145, 150, 90),
            "Tryk E: undersoeg behandlingsskab",
            "Skabet viser tre behandlinger med forskellig effekt, pris og ventetid. Ressourcerne raekker ikke til alle samme dag.",
            color=(76, 132, 150),
            symbol="VAC",
        ))
        rooms[5].add(Interactable(
            "Antibiotika-plakat",
            (base_x + 350, 130, 160, 100),
            "Tryk E: laes overvagningsnotat",
            "Notatet beskriver sensorer i hjemmet, der kan advare om sygdomsudbrud. Det virker bedst med mange data, men kan foeles som konstant kontrol.",
            color=(142, 88, 82),
            symbol="AB",
        ))
        rooms[5].add(Interactable(
            "Overvaagnings-panel",
            (base_x + 390, 485, 85, 58),
            "Tryk E: aabn syddoer",
            "Vurder graensen mellem folkesundhed og privatliv.",
            kind="quiz",
            quiz=Quiz(
                "monitoring_quiz",
                "Borgerovervaagning",
                "Sundhedsstyrelsen vil opdage sygdom tidligt med sensorer i hjemmet. Hvilken loesning balancerer bedst folkesundhed og privatliv?",
                [
                    "Sensorer samler data uden at borgeren faar besked",
                    "Data bruges med klart formaal, indsigt og mulighed for fravalg",
                    "Alle data offentliggoeres, saa forskere kan bruge dem frit",
                    "Kun borgere med dyre enheder faar adgang til forebyggelse",
                ],
                1,
                "Overvaagning",
            ),
            color=(130, 90, 96),
            symbol="V?",
        ))
        rooms[5].add(Interactable(
            "Behandlings-panel",
            (base_x + 590, 285, 85, 80),
            "Tryk E: aabn oestdoer",
            "Vurder prioritering af behandling.",
            kind="quiz",
            quiz=Quiz(
                "treatment_quiz",
                "Adgang til behandling",
                "Tre patienter venter, og systemet foreslaar en prioritering. Hvilket princip er mest retfaerdigt?",
                [
                    "Den med flest sundhedsapps kommer foerst",
                    "Medicinsk behov, forventet effekt og gennemsigtig begrundelse indgaar",
                    "Den der skriver mest overbevisende i profilen kommer foerst",
                    "Systemet skjuler forklaringen for at undgaa debat",
                ],
                1,
                "Adgang til behandling",
            ),
            color=(84, 108, 150),
            symbol="AI",
        ))
        rooms[5].add(Interactable("Ventestole", (base_x + 105, 365, 150, 60), "Tryk E: kig", "Tre stole med slidte puder staar ved en stille ventesektion.", color=(88, 90, 118), symbol="|||"))
        rooms[5].add(Interactable("Haandvask", (base_x + 565, 165, 80, 55), "Tryk E: kig", "En haandvask med sensor blinker kort, naar du kommer taet paa.", color=(105, 136, 145), symbol="VAND"))

        base_x = 720
        base_y = 590
        rooms[2].add(Interactable(
            "DNA-bord",
            (base_x + 95, base_y + 245, 200, 82),
            "Tryk E: undersoeg DNA",
            "DNA-bordet viser fire kort: samtykke, proeve, analyse og raadgivning. Kortene ligger ikke i den rigtige raekkefoelge.",
            color=(105, 85, 145),
            symbol="DNA",
        ))
        rooms[2].add(Interactable(
            "Steril baenk",
            (base_x + 405, base_y + 115, 155, 95),
            "Tryk E: laes labregel",
            "Labreglen siger: Foerst skal borgeren forstaa valget. Derefter kan proeven tages, analyseres og forklares.",
            color=(84, 126, 130),
            symbol="CELL",
        ))
        rooms[2].add(Interactable(
            "DNA-proces",
            (base_x + 590, base_y + 255, 85, 80),
            "Tryk E: aabn oestdoer",
            "Panelet accepterer kun en proces, der passer med kortene og labreglen.",
            kind="quiz",
            quiz=Quiz(
                "bio_sequence",
                "DNA-kort",
                "Fire proceskort ligger paa bordet. Skriv numrene i den raekkefoelge, der passer til ansvarlig genetisk screening.",
                [
                    "Informeret samtykke",
                    "Tag genetisk proeve",
                    "Analyser risiko",
                    "Giv raadgivning",
                ],
                0,
                "Genetisk screening",
                code_answer="1-2-3-4",
                puzzle_type="sequence",
                input_hint="kort 1-2-3-4",
            ),
            color=(118, 92, 150),
            symbol="1-2",
        ))
        rooms[2].add(Interactable("Mikroskop", (base_x + 135, base_y + 115, 70, 70), "Tryk E: kig", "Mikroskopet viser en uskarp celleprove med smaa lysende prikker.", color=(98, 102, 112), symbol="MIC"))
        rooms[2].add(Interactable("Farvebakke", (base_x + 320, base_y + 390, 110, 50), "Tryk E: kig", "Farvede reagenser staar i smaa glas med etiketter og maerker.", color=(125, 92, 118), symbol="RGB"))

        base_x = 0
        base_y = 590
        rooms[4].add(Interactable(
            "Samtykke-skaerm",
            (base_x + 90, base_y + 135, 165, 95),
            "Tryk E: laes skaerm",
            "Skaermen viser en datapakke med tre stempler: formaal, accept og adgangskontrol. Uden alle tre bliver pakken afvist.",
            color=(68, 128, 105),
            symbol="JA",
        ))
        rooms[4].add(Interactable(
            "Krypteringsnote",
            (base_x + 355, base_y + 130, 180, 90),
            "Tryk E: laes note",
            "Noten viser data som laast tekst. Kun den rette noegle kan goere oplysningerne laesbare igen.",
            color=(95, 118, 92),
            symbol="LOCK",
        ))
        rooms[4].add(Interactable(
            "Privatlivs-quiz",
            (base_x + 590, base_y + 255, 85, 80),
            "Tryk E: aabn oestdoer",
            "Brug ledetraade om samtykke og kryptering.",
            kind="quiz",
            quiz=Quiz(
                "data_privacy_quiz",
                "Datapakke",
                "Datapakken har fire stempler. Vaelg de tre stempler, der skal sidde paa pakken, foer den sendes videre.",
                [
                    "Klart formaal",
                    "Samtykke",
                    "Krypteret adgang",
                    "Offentlig deling",
                ],
                0,
                "Datasikkerhed",
                code_answer="1-2-3",
                puzzle_type="build",
                input_hint="stempler 1-2-3",
            ),
            color=(90, 126, 94),
            symbol="?",
        ))
        rooms[4].add(Interactable("Arkivkasser", (base_x + 110, base_y + 360, 150, 65), "Tryk E: kig", "Gamle papirkasser. De minder om, at sundhedsdata ogsaa fandtes foer apps.", color=(118, 96, 66), symbol="BOX"))
        rooms[4].add(Interactable("Gul lampe", (base_x + 500, base_y + 380, 60, 80), "Tryk E: kig", "En gul lampe summer svagt over mapperne i arkivet.", color=(150, 132, 64), symbol="LUX"))

        base_x = 720
        base_y = 1110
        rooms[3].add(Interactable(
            "CRISPR-opsamling",
            (base_x + 90, base_y + 145, 155, 100),
            "Tryk E: se rute",
            "Du valgte screening-ruten. Her samles din viden om genetiske data, risiko og personlig medicin.",
            color=(120, 120, 78),
            symbol="BITS",
        ))
        rooms[3].add(Interactable(
            "Screening-terminal",
            (base_x + 465, base_y + 260, 175, 105),
            "Tryk E: afslut screening-rute",
            "Afslut screening-ruten.",
            kind="ending",
            quiz="Genetisk screening",
            color=(56, 132, 132),
            symbol="END",
        ))
        rooms[3].add(Interactable("Diplomprinter", (base_x + 110, base_y + 385, 130, 70), "Tryk E: kig", "Printeren summer og holder et halvt udskrevet diplom klar.", color=(110, 112, 118), symbol="PRINT"))
        rooms[3].add(Interactable("Lysvaeg", (base_x + 330, base_y + 130, 130, 65), "Tryk E: kig", "En vaeg med rolige farver. Den fejrer, at du fandt en vej gennem labbet.", color=(70, 120, 150), symbol="***"))

        base_x = 0
        base_y = 1110
        rooms[6].add(Interactable("Data-dashboard", (base_x + 120, base_y + 145, 180, 110), "Tryk E: se dashboard", "Du valgte data-ruten. Her handler slutningen om samtykke, kryptering og ansvarlig haandtering af sundhedsdata.", color=(64, 132, 116), symbol="DATA"))
        rooms[6].add(Interactable("Data-terminal", (base_x + 455, base_y + 260, 175, 105), "Tryk E: afslut data-rute", "Afslut data-ruten.", kind="ending", quiz="Haandtering af sundhedsdata", color=(70, 140, 120), symbol="END"))
        rooms[6].add(Interactable("Serverrack", (base_x + 365, base_y + 130, 95, 150), "Tryk E: kig", "Servere summer i baggrunden. Data skal opbevares sikkert.", color=(62, 76, 82), symbol="LOCK"))
        rooms[6].add(Interactable("Privatlivsplakat", (base_x + 110, base_y + 365, 150, 90), "Tryk E: kig", "Plakaten minder om: Sporg foerst, forklar formaal, beskyt data.", color=(120, 112, 78), symbol="JA"))

        base_x = 2160
        base_y = 70
        rooms[7].add(Interactable("Behandlingsmodel", (base_x + 110, base_y + 135, 190, 120), "Tryk E: se model", "Du valgte behandlings-ruten. Her handler slutningen om retfaerdig adgang, ventelister og forklarlige prioriteringer.", color=(58, 92, 150), symbol="AI"))
        rooms[7].add(Interactable("Behandlings-terminal", (base_x + 455, base_y + 250, 175, 105), "Tryk E: afslut behandlings-rute", "Afslut behandlings-ruten.", kind="ending", quiz="Adgang til behandling", color=(70, 108, 160), symbol="END"))
        rooms[7].add(Interactable("Prioriteringstavle", (base_x + 370, base_y + 125, 120, 95), "Tryk E: kig", "Tavlen viser behov, effekt og ventetid som tre forskellige dataspor.", color=(82, 102, 140), symbol="SCAN"))
        rooms[7].add(Interactable("Kabelgulv", (base_x + 110, base_y + 380, 170, 55), "Tryk E: kig", "Kablerne er ordnet naesten paent. Naesten.", color=(68, 72, 90), symbol="***"))

        base_x = 1440
        base_y = 590
        rooms[8].add(Interactable("Sensorvaeg", (base_x + 110, base_y + 145, 180, 105), "Tryk E: se sensorer", "Du valgte overvaagnings-ruten. Her handler slutningen om sensorer, sygdomsudbrud og borgernes frihed.", color=(142, 82, 90), symbol="VAC"))
        rooms[8].add(Interactable("Overvaagnings-terminal", (base_x + 455, base_y + 260, 175, 105), "Tryk E: afslut overvaagnings-rute", "Afslut overvaagnings-ruten.", kind="ending", quiz="Overvaagning af borgere", color=(150, 86, 96), symbol="END"))
        rooms[8].add(Interactable("Samtykkeskab", (base_x + 350, base_y + 130, 135, 90), "Tryk E: kig", "Smaa symboler viser samtykke, indsigt og fravalg.", color=(130, 98, 108), symbol="AB"))
        rooms[8].add(Interactable("Kliniklampe", (base_x + 115, base_y + 375, 90, 80), "Tryk E: kig", "En kraftig lampe lyser over en stille beslutningsstation.", color=(150, 130, 80), symbol="LUX"))
        return rooms

    def apply_profile_progress(self):
        solved = self.profile.solved if self.profile else {}
        for door in self.doors:
            door.open = solved.get(door.quiz_id, False)
        idx = max(0, min(self.profile.current_room, len(self.rooms) - 1))
        self.player.rect.center = (self.rooms[idx].rect.x + 120, self.rooms[idx].rect.centery)

    def refresh_menu_buttons(self):
        x = SCREEN_WIDTH // 2 - 110
        self.buttons = [
            Button((x, 300, 220, 48), "Start spil", lambda: self.set_state("profile")),
            Button((x, 365, 220, 48), "Instruktioner", lambda: self.set_state("instructions")),
            Button((x, 430, 220, 48), "Afslut", self.quit),
        ]

    def set_state(self, state):
        self.state = state
        self.message = ""
        if state == "menu":
            self.refresh_menu_buttons()

    def quit(self):
        self.running = False

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS)
            self.handle_events()
            self.update(dt)
            self.draw()
        pygame.quit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_p and self.profile:
                self.unlock_nearest_locked_door()
            elif self.state == "menu":
                for button in self.buttons:
                    button.handle_event(event)
            elif self.state == "instructions":
                if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                    self.set_state("menu")
            elif self.state == "profile":
                self.handle_profile_event(event)
            elif self.state == "playing":
                self.handle_play_event(event)
            elif self.state == "dialog":
                if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_ESCAPE, pygame.K_e):
                    self.state = "playing"
            elif self.state == "quiz":
                self.handle_quiz_event(event)
            elif self.state == "topic":
                self.handle_topic_event(event)
            elif self.state == "ending":
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.set_state("menu")

    def handle_profile_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.set_state("menu")
            elif event.key == pygame.K_RETURN:
                name = self.profile_name_input.strip()
                if len(name) >= 2:
                    self.profile = UserProfile.load(name)
                    self.profile.save()
                    if UserProfile.last_error:
                        self.message = UserProfile.last_error
                    else:
                        self.apply_profile_progress()
                        self.state = "playing"
                else:
                    self.message = "Skriv mindst 2 tegn."
            elif event.key == pygame.K_BACKSPACE:
                self.profile_name_input = self.profile_name_input[:-1]
            elif len(self.profile_name_input) < 16 and event.unicode and event.unicode.isprintable():
                self.profile_name_input += event.unicode
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            profiles = list(UserProfile.load_all().keys())[:6]
            panel = pygame.Rect(SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 250, 400, 500)
            for i, name in enumerate(profiles):
                rect = pygame.Rect(panel.x + 90, panel.y + 300 + i * 38, 220, 30)
                if rect.collidepoint(event.pos):
                    self.profile_name_input = name
                    self.profile = UserProfile.load(name)
                    self.apply_profile_progress()
                    self.state = "playing"

    def handle_play_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.save_progress()
                self.set_state("menu")
            elif event.key == pygame.K_e:
                item = self.nearest_interactable()
                if item:
                    if item.kind == "quiz":
                        self.active_quiz = item.quiz
                        self.active_quiz.feedback = ""
                        self.active_quiz.input_text = ""
                        self.state = "quiz"
                    elif item.kind == "topic":
                        if len(self.profile.knowledge_pieces) >= 3:
                            self.state = "topic"
                        else:
                            self.active_text = "Du mangler stadig vidensbrikker. Los gaaderne i de tidligere rum foerst."
                            self.state = "dialog"
                    elif item.kind == "ending":
                        self.profile.selected_topic = item.quiz
                        self.profile.completed = True
                        self.save_progress()
                        self.state = "ending"
                    else:
                        self.active_text = item.text
                        self.state = "dialog"

    def handle_quiz_event(self, event):
        quiz = self.active_quiz
        if not quiz:
            self.state = "playing"
            return
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.state = "playing"
            elif quiz.code_answer is not None:
                if event.key == pygame.K_RETURN:
                    if quiz.answer(quiz.input_text):
                        self.solve_quiz(quiz)
                elif event.key == pygame.K_BACKSPACE:
                    quiz.input_text = quiz.input_text[:-1]
                elif len(quiz.input_text) < 18 and event.unicode and event.unicode.isprintable():
                    quiz.input_text += event.unicode
            elif pygame.K_1 <= event.key <= pygame.K_9:
                choice = event.key - pygame.K_1
                if 0 <= choice < len(quiz.options) and quiz.answer(choice):
                    self.solve_quiz(quiz)

    def handle_topic_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.state = "playing"
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for rect, topic in self.topic_buttons:
                if rect.collidepoint(event.pos):
                    self.profile.selected_topic = topic
                    self.profile.completed = True
                    self.save_progress()
                    self.state = "ending"

    def solve_quiz(self, quiz):
        self.profile.solved[quiz.quiz_id] = True
        if quiz.reward_piece and quiz.reward_piece not in self.profile.knowledge_pieces:
            self.profile.knowledge_pieces.append(quiz.reward_piece)
        for door in self.doors:
            if door.quiz_id == quiz.quiz_id:
                door.open = True
        self.save_progress()

    def unlock_nearest_locked_door(self):
        locked = [door for door in self.doors if not door.open]
        if not locked:
            self.active_text = "Alle doere er allerede aabne."
            self.state = "dialog"
            return
        nearest = min(locked, key=lambda door: self.distance_to(door.gate_rect.center))
        nearest.open = True
        self.profile.solved[nearest.quiz_id] = True
        self.save_progress()
        self.active_text = "Udviklertilstand: Den naermeste laaste doer er aabnet."
        self.state = "dialog"

    def save_progress(self):
        if not self.profile:
            return
        room = room_at_point(self.rooms, self.player.rect.center)
        if room:
            self.profile.current_room = room.index
        self.profile.save()

    def nearest_interactable(self):
        room = room_at_point(self.rooms, self.player.rect.center)
        if not room:
            return None
        near = [item for item in room.interactables if item.is_near(self.player.rect)]
        if not near:
            return None
        return min(near, key=lambda item: self.distance_to(item.rect.center))

    def distance_to(self, point):
        dx = self.player.rect.centerx - point[0]
        dy = self.player.rect.centery - point[1]
        return math.hypot(dx, dy)

    def update(self, dt):
        if self.state == "playing":
            keys = pygame.key.get_pressed()
            self.player.move(keys, self.rooms, self.doors)
            self.save_progress()
        self.update_camera()

    def update_camera(self):
        room = room_at_point(self.rooms, self.player.rect.center) or self.rooms[0]
        target_x = self.player.rect.centerx - SCREEN_WIDTH // 2
        target_y = self.player.rect.centery - SCREEN_HEIGHT // 2
        self.camera.x = max(room.rect.x - 60, min(target_x, room.rect.right - SCREEN_WIDTH + 60))
        self.camera.y = max(room.rect.y - 60, min(target_y, room.rect.bottom - SCREEN_HEIGHT + 120))

    def draw(self):
        self.screen.fill(COLORS["bg"])
        if self.state == "menu":
            self.draw_menu()
        elif self.state == "instructions":
            self.draw_instructions()
        elif self.state == "profile":
            self.draw_profile()
        else:
            self.draw_world()
            if self.state == "dialog":
                self.draw_dialog(self.active_text, "Tekstboks")
            elif self.state == "quiz":
                self.draw_quiz()
            elif self.state == "topic":
                self.draw_topic_select()
            elif self.state == "ending":
                self.draw_ending()
        pygame.display.flip()

    def draw_menu(self):
        self.draw_pixel_background()
        title = self.big_font.render("Sundhedsstyrelsen 2050", False, COLORS["text"])
        self.screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 185)))
        subtitle = self.font.render("Escape-room om bioteknologiske dilemmaer og digital sundhed", False, COLORS["muted"])
        self.screen.blit(subtitle, subtitle.get_rect(center=(SCREEN_WIDTH // 2, 235)))
        for button in self.buttons:
            button.draw(self.screen, self.font)

    def draw_pixel_background(self):
        for y in range(0, SCREEN_HEIGHT, 40):
            for x in range(0, SCREEN_WIDTH, 40):
                color = (18 + (x // 40 + y // 40) % 2 * 5, 24, 36)
                pygame.draw.rect(self.screen, color, (x, y, 40, 40))
        for x, y, w, h, color in [
            (90, 110, 190, 70, (42, 116, 145)),
            (720, 115, 150, 90, (100, 80, 145)),
            (105, 510, 160, 60, (58, 135, 120)),
            (730, 500, 185, 70, (136, 105, 58)),
        ]:
            pygame.draw.rect(self.screen, color, (x, y, w, h))
            pygame.draw.rect(self.screen, COLORS["wall_top"], (x, y, w, 8))

    def draw_instructions(self):
        self.draw_pixel_background()
        panel = pygame.Rect(SCREEN_WIDTH // 2 - 340, SCREEN_HEIGHT // 2 - 230, 680, 460)
        pygame.draw.rect(self.screen, COLORS["panel"], panel, border_radius=4)
        pygame.draw.rect(self.screen, COLORS["accent"], panel, 2, border_radius=4)
        title = self.mid_font.render("Instruktioner", False, COLORS["text"])
        self.screen.blit(title, (panel.x + 35, panel.y + 30))
        text = (
            "Bevaeg dig med WASD eller piletaster. Tryk E ved skaerme, plakater, borde og terminaler. "
            "Laes korte forklaringer, loes dilemmaer, byg processer og aabn doere. Naar en doer er aaben, gaar du selv gennem den. "
            "Hver vej ender i et slutrum om en problemstilling fra Sundhedsstyrelsens fremtidsscenarie. Tryk en tast for at gaa tilbage."
        )
        draw_text(self.screen, text, self.font, COLORS["text"], pygame.Rect(panel.x + 35, panel.y + 90, panel.width - 70, 260), 8)

    def draw_profile(self):
        self.draw_pixel_background()
        panel = pygame.Rect(SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 250, 400, 500)
        pygame.draw.rect(self.screen, COLORS["panel"], panel, border_radius=4)
        pygame.draw.rect(self.screen, COLORS["accent"], panel, 2, border_radius=4)
        title = self.mid_font.render("Brugerprofil", False, COLORS["text"])
        self.screen.blit(title, (panel.x + 40, panel.y + 35))
        draw_text(self.screen, "Skriv dit navn og tryk Enter, eller vaelg en gemt bruger.", self.font, COLORS["muted"], pygame.Rect(panel.x + 40, panel.y + 85, 320, 70))
        input_rect = pygame.Rect(panel.x + 40, panel.y + 165, 320, 42)
        pygame.draw.rect(self.screen, (14, 18, 26), input_rect)
        pygame.draw.rect(self.screen, COLORS["accent"], input_rect, 2)
        name = self.profile_name_input or "Navn..."
        color = COLORS["text"] if self.profile_name_input else COLORS["muted"]
        self.screen.blit(self.font.render(name, False, color), (input_rect.x + 12, input_rect.y + 11))

        label = self.font.render("Gemte brugere", False, COLORS["text"])
        self.screen.blit(label, (panel.x + 40, panel.y + 250))
        profiles = list(UserProfile.load_all().keys())[:6]
        for i, name in enumerate(profiles):
            rect = pygame.Rect(panel.x + 90, panel.y + 300 + i * 38, 220, 30)
            pygame.draw.rect(self.screen, COLORS["panel_2"], rect, border_radius=4)
            self.screen.blit(self.small_font.render(name, False, COLORS["text"]), (rect.x + 10, rect.y + 7))
        if self.message:
            self.screen.blit(self.small_font.render(self.message, False, COLORS["danger"]), (panel.x + 40, panel.bottom - 40))

    def draw_world(self):
        for room in self.rooms:
            if self.room_is_visible(room):
                room.draw_floor(self.screen, self.camera)
        for room in self.rooms:
            if self.room_is_visible(room):
                room.draw_objects(self.screen, self.camera, self.small_font)
        for door in self.doors:
            if door.gate_rect.colliderect(self.camera.inflate(180, 180)):
                door.draw(self.screen, self.camera)
        self.player.draw(self.screen, self.camera)
        self.draw_hud()
        self.draw_prompt()

    def room_is_visible(self, room):
        return room.rect.colliderect(self.camera.inflate(220, 220))

    def draw_hud(self):
        room = room_at_point(self.rooms, self.player.rect.center) or self.rooms[0]
        bar = pygame.Rect(0, 0, SCREEN_WIDTH, 58)
        pygame.draw.rect(self.screen, (10, 14, 22), bar)
        name = self.profile.name if self.profile else "Gæst"
        title = f"{name} | {room.name} | Vidensbrikker: {len(self.profile.knowledge_pieces) if self.profile else 0}/3"
        self.screen.blit(self.font.render(title, False, COLORS["text"]), (18, 18))
        self.screen.blit(self.small_font.render(room.intro, False, COLORS["muted"]), (18, 40))

    def draw_prompt(self):
        item = self.nearest_interactable()
        if not item or self.state != "playing":
            return
        prompt = self.font.render(item.prompt, False, COLORS["text"])
        bg = prompt.get_rect(midbottom=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 24)).inflate(24, 12)
        pygame.draw.rect(self.screen, (12, 18, 26), bg, border_radius=4)
        pygame.draw.rect(self.screen, COLORS["accent"], bg, 2, border_radius=4)
        self.screen.blit(prompt, prompt.get_rect(center=bg.center))

    def draw_dialog(self, text, title):
        panel = pygame.Rect(SCREEN_WIDTH // 2 - 360, SCREEN_HEIGHT - 245, 720, 165)
        pygame.draw.rect(self.screen, COLORS["panel"], panel, border_radius=4)
        pygame.draw.rect(self.screen, COLORS["accent"], panel, 2, border_radius=4)
        self.screen.blit(self.mid_font.render(title, False, COLORS["text"]), (panel.x + 24, panel.y + 18))
        draw_text(self.screen, text, self.font, COLORS["text"], pygame.Rect(panel.x + 24, panel.y + 58, panel.width - 48, 70), 6)
        self.screen.blit(self.small_font.render("Enter/Esc: luk", False, COLORS["muted"]), (panel.x + 24, panel.bottom - 28))

    def draw_quiz(self):
        quiz = self.active_quiz
        panel = pygame.Rect(SCREEN_WIDTH // 2 - 350, SCREEN_HEIGHT // 2 - 225, 700, 450)
        pygame.draw.rect(self.screen, COLORS["panel"], panel, border_radius=4)
        pygame.draw.rect(self.screen, COLORS["accent_2"], panel, 2, border_radius=4)
        self.screen.blit(self.mid_font.render(quiz.title, False, COLORS["text"]), (panel.x + 28, panel.y + 28))
        draw_text(self.screen, quiz.question, self.font, COLORS["text"], pygame.Rect(panel.x + 28, panel.y + 80, panel.width - 56, 90), 6)

        if quiz.code_answer is not None:
            if quiz.options:
                for i, option in enumerate(quiz.options):
                    col = i % 2
                    row = i // 2
                    rect = pygame.Rect(panel.x + 28 + col * 320, panel.y + 172 + row * 58, 300, 44)
                    pygame.draw.rect(self.screen, COLORS["panel_2"], rect, border_radius=4)
                    pygame.draw.rect(self.screen, (86, 104, 124), rect, 1, border_radius=4)
                    self.screen.blit(self.font.render(f"{i + 1}", False, COLORS["accent_2"]), (rect.x + 12, rect.y + 11))
                    draw_text(self.screen, option, self.small_font, COLORS["text"], pygame.Rect(rect.x + 42, rect.y + 8, rect.width - 52, rect.height - 12), 2)
                input_y = panel.y + 315
            else:
                input_y = panel.y + 190
            input_rect = pygame.Rect(panel.x + 28, input_y, 280, 44)
            pygame.draw.rect(self.screen, (10, 14, 22), input_rect)
            pygame.draw.rect(self.screen, COLORS["accent_2"], input_rect, 2)
            self.screen.blit(self.font.render(quiz.input_text or quiz.input_hint, False, COLORS["text"] if quiz.input_text else COLORS["muted"]), (input_rect.x + 12, input_rect.y + 12))
            if quiz.puzzle_type == "sequence":
                helper = "Saet raekkefoelgen med bindestreger | Enter: test | Esc: tilbage"
            elif quiz.puzzle_type == "build":
                helper = "Skriv de valgte numre med bindestreger | Enter: test | Esc: tilbage"
            elif quiz.options:
                helper = "Skriv numre med bindestreger | Enter: test | Esc: tilbage"
            else:
                helper = "Enter: svar | Esc: tilbage"
            self.screen.blit(self.small_font.render(helper, False, COLORS["muted"]), (panel.x + 28, input_rect.bottom + 14))
        else:
            for i, option in enumerate(quiz.options):
                rect = pygame.Rect(panel.x + 28, panel.y + 180 + i * 54, panel.width - 56, 42)
                pygame.draw.rect(self.screen, COLORS["panel_2"], rect, border_radius=4)
                pygame.draw.rect(self.screen, (86, 104, 124), rect, 1, border_radius=4)
                self.screen.blit(self.font.render(f"{i + 1}. {option}", False, COLORS["text"]), (rect.x + 14, rect.y + 11))
            self.screen.blit(self.small_font.render("Multiple choice: Tryk 1-4 | Esc: tilbage", False, COLORS["muted"]), (panel.x + 28, panel.bottom - 42))

        if quiz.feedback:
            color = COLORS["accent"] if "Korrekt" in quiz.feedback else COLORS["danger"]
            draw_text(self.screen, quiz.feedback, self.font, color, pygame.Rect(panel.x + 28, panel.bottom - 92, panel.width - 56, 48))

    def draw_topic_select(self):
        panel = pygame.Rect(SCREEN_WIDTH // 2 - 385, SCREEN_HEIGHT // 2 - 260, 770, 520)
        pygame.draw.rect(self.screen, COLORS["panel"], panel, border_radius=4)
        pygame.draw.rect(self.screen, COLORS["accent"], panel, 2, border_radius=4)
        self.screen.blit(self.mid_font.render("Vaelg dit slutemne", False, COLORS["text"]), (panel.x + 30, panel.y + 26))
        draw_text(self.screen, "Hvilket emne vil du laere mere om? Valget gemmes paa din profil og bestemmer slutningen.", self.font, COLORS["muted"], pygame.Rect(panel.x + 30, panel.y + 70, panel.width - 60, 60))
        self.topic_buttons = []
        topics = list(TOPICS.keys())
        for i, topic in enumerate(topics):
            col = i % 2
            row = i // 2
            rect = pygame.Rect(panel.x + 30 + col * 365, panel.y + 160 + row * 84, 340, 58)
            self.topic_buttons.append((rect, topic))
            pygame.draw.rect(self.screen, COLORS["panel_2"], rect, border_radius=4)
            pygame.draw.rect(self.screen, (95, 118, 138), rect, 1, border_radius=4)
            draw_text(self.screen, topic, self.font, COLORS["text"], rect.inflate(-24, -12), center=True)
        self.screen.blit(self.small_font.render("Esc: tilbage", False, COLORS["muted"]), (panel.x + 30, panel.bottom - 34))

    def draw_ending(self):
        topic = self.profile.selected_topic or "Fremtidens sundhed"
        text = TOPICS.get(topic, "Du har gennemfoert labbet og samlet viden om fremtidens sundhed.")
        panel = pygame.Rect(SCREEN_WIDTH // 2 - 370, SCREEN_HEIGHT // 2 - 260, 740, 520)
        pygame.draw.rect(self.screen, COLORS["panel"], panel, border_radius=4)
        pygame.draw.rect(self.screen, COLORS["accent"], panel, 2, border_radius=4)
        self.screen.blit(self.mid_font.render("Escape-room gennemfoert", False, COLORS["text"]), (panel.x + 30, panel.y + 28))
        self.screen.blit(self.font.render(f"Dit valgte emne: {topic}", False, COLORS["accent_2"]), (panel.x + 30, panel.y + 86))
        draw_text(self.screen, text, self.font, COLORS["text"], pygame.Rect(panel.x + 30, panel.y + 135, panel.width - 60, 155), 8)
        pieces = ", ".join(self.profile.knowledge_pieces)
        draw_text(self.screen, f"Du samlede vidensbrikkerne: {pieces}. De viser, at sundhed i fremtiden handler om data, biologi, teknologi og ansvarlige valg.", self.font, COLORS["muted"], pygame.Rect(panel.x + 30, panel.y + 315, panel.width - 60, 100), 8)
        self.screen.blit(self.small_font.render("Esc: tilbage til menu", False, COLORS["muted"]), (panel.x + 30, panel.bottom - 45))


if __name__ == "__main__":
    Game().run()
