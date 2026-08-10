from typing import Dict, List, Optional, Tuple
import pygame

from ..models import Graph, Drone, Zone, ZoneType


class GraphicRenderer:
    """Renderer gráfico básico, feito com pygame, para visualizar a
    simulação turno a turno. Avança automaticamente, com a opção de
    recuar/avançar manualmente um turno (setas esquerda/direita).
    Fecha a janela ou prime ESC/Q para sair.
    """

    _WIDTH = 900
    _HEIGHT = 650
    _MARGIN = 80
    _ZONE_RADIUS = 22
    _DRONE_RADIUS = 7

    _BG_COLOR = (18, 18, 24)
    _EDGE_COLOR = (90, 90, 100)
    _TEXT_COLOR = (230, 230, 230)
    _DRONE_COLOR = (255, 255, 255)

    _TYPE_COLORS = {
        ZoneType.NORMAL: (70, 130, 220),
        ZoneType.PRIORITY: (70, 200, 110),
        ZoneType.RESTRICTED: (220, 70, 70),
        ZoneType.BLOCKED: (100, 100, 100),
    }

    _NAMED_COLORS = {
        "red": (220, 70, 70),
        "green": (70, 200, 110),
        "yellow": (230, 210, 70),
        "blue": (70, 130, 220),
        "gray": (130, 130, 130),
        "grey": (130, 130, 130),
        "cyan": (70, 200, 210),
        "magenta": (200, 90, 200),
    }

    _ANIMATION_DURATION = 0.4      # segundos
    _AUTO_ADVANCE_INTERVAL = 1.5   # segundos
    _DRONE_IMAGE_SIZE = (30, 30)

    def __init__(
        self,
        graph: Graph,
        turns_log: List[Dict[Drone, str]],
        background_path: Optional[str] = None,
        drone_image_path: Optional[str] = None,
    ) -> None:
        self.graph: Graph = graph
        self.turns_log: List[Dict[Drone, str]] = turns_log
        self.positions: Dict[str, Tuple[int, int]] = (
            self._compute_positions()
        )

        self.background: Optional[pygame.Surface] = self._load_image(
            background_path, (self._WIDTH, self._HEIGHT)
        )
        self.drone_image: Optional[pygame.Surface] = self._load_image(
            drone_image_path, self._DRONE_IMAGE_SIZE
        )

        self.snapshots: List[Dict[Drone, Tuple[float, float]]] = (
            self._compute_all_snapshots()
        )
        self.current_turn: int = 0
        self.anim_progress: float = 1.0
        self.anim_from: Dict[Drone, Tuple[float, float]] = self.snapshots[0]
        self.anim_to: Dict[Drone, Tuple[float, float]] = self.snapshots[0]
        self.time_since_last_advance: float = 0.0

        pygame.init()
        self.screen = pygame.display.set_mode((self._WIDTH, self._HEIGHT))
        pygame.display.set_caption("fly_in - simulation viewer")
        self.font = pygame.font.SysFont("consolas", 16)
        self.big_font = pygame.font.SysFont("consolas", 22, bold=True)
        self.clock = pygame.time.Clock()

    def _load_image(
        self, path: Optional[str], size: Tuple[int, int]
    ) -> Optional[pygame.Surface]:
        if path is None:
            return None
        try:
            image = pygame.image.load(path)
            return pygame.transform.smoothscale(image, size)
        except (FileNotFoundError, pygame.error):
            return None

    def _compute_positions(self) -> Dict[str, Tuple[int, int]]:
        zones = self.graph.zones
        xs = [zone.x for zone in zones]
        ys = [zone.y for zone in zones]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        span_x = max(max_x - min_x, 1)
        span_y = max(max_y - min_y, 1)
        usable_w = self._WIDTH - 2 * self._MARGIN
        usable_h = self._HEIGHT - 2 * self._MARGIN
        positions: Dict[str, Tuple[int, int]] = {}

        for zone in zones:
            px = self._MARGIN + int((zone.x - min_x) / span_x * usable_w)
            py = self._MARGIN + int((zone.y - min_y) / span_y * usable_h)
            positions[zone.name] = (px, py)

        return positions

    def _compute_all_snapshots(
        self,
    ) -> List[Dict[Drone, Tuple[float, float]]]:
        start_pos = self.positions[self.graph.start_zone.name]
        all_drones = {
            drone for movements in self.turns_log for drone in movements
        }
        current: Dict[Drone, Tuple[float, float]] = {
            drone: start_pos for drone in all_drones
        }
        snapshots: List[Dict[Drone, Tuple[float, float]]] = [dict(current)]

        for movements in self.turns_log:
            for drone, destination in movements.items():
                current[drone] = self._resolve_position(destination)
            snapshots.append(dict(current))

        return snapshots

    def _resolve_position(self, destination: str) -> Tuple[float, float]:
        try:
            zone = self.graph.get_zone(destination)
            return self.positions[zone.name]
        except Exception:
            parts = destination.split("-")
            if len(parts) == 2:
                try:
                    z1 = self.graph.get_zone(parts[0])
                    z2 = self.graph.get_zone(parts[1])
                    x1, y1 = self.positions[z1.name]
                    x2, y2 = self.positions[z2.name]
                    return ((x1 + x2) / 2, (y1 + y2) / 2)
                except Exception:
                    pass
            return self.positions[self.graph.start_zone.name]

    def _zone_color(self, zone: Zone) -> Tuple[int, int, int]:
        if zone.color and zone.color in self._NAMED_COLORS:
            return self._NAMED_COLORS[zone.color]
        return self._TYPE_COLORS.get(zone.zone_type, (150, 150, 150))

    def _advance_turn(self) -> None:
        if self.current_turn >= len(self.turns_log):
            return
        self.anim_from = self.snapshots[self.current_turn]
        self.current_turn += 1
        self.anim_to = self.snapshots[self.current_turn]
        self.anim_progress = 0.0
        self.time_since_last_advance = 0.0

    def _rewind_turn(self) -> None:
        if self.current_turn <= 0:
            return
        self.anim_from = self.snapshots[self.current_turn]
        self.current_turn -= 1
        self.anim_to = self.snapshots[self.current_turn]
        self.anim_progress = 0.0
        self.time_since_last_advance = 0.0

    def _update(self, dt: float) -> None:
        if self.anim_progress < 1.0:
            self.anim_progress = min(
                self.anim_progress + dt / self._ANIMATION_DURATION, 1.0
            )
        self.time_since_last_advance += dt
        if self.time_since_last_advance >= self._AUTO_ADVANCE_INTERVAL:
            self._advance_turn()

    def _draw_background(self) -> None:
        if self.background:
            self.screen.blit(self.background, (0, 0))
        else:
            self.screen.fill(self._BG_COLOR)

    def _draw_graph(self) -> None:
        for connection in self.graph.connections:
            x1, y1 = self.positions[connection.zone1.name]
            x2, y2 = self.positions[connection.zone2.name]
            pygame.draw.line(
                self.screen, self._EDGE_COLOR, (x1, y1), (x2, y2), 2
            )

        for zone in self.graph.zones:
            x, y = self.positions[zone.name]
            color = self._zone_color(zone)
            pygame.draw.circle(self.screen, color, (x, y), self._ZONE_RADIUS)
            pygame.draw.circle(
                self.screen, (0, 0, 0), (x, y), self._ZONE_RADIUS, 2
            )
            label = self.font.render(zone.name, True, self._TEXT_COLOR)
            self.screen.blit(
                label, (x - label.get_width() // 2, y + self._ZONE_RADIUS + 4)
            )

    def _draw_drones(self) -> None:
        for drone in self.anim_to:
            from_pos = self.anim_from.get(drone, self.anim_to[drone])
            to_pos = self.anim_to[drone]
            t = self.anim_progress
            x = from_pos[0] + (to_pos[0] - from_pos[0]) * t
            y = from_pos[1] + (to_pos[1] - from_pos[1]) * t

            if self.drone_image:
                rect = self.drone_image.get_rect(center=(x, y))
                self.screen.blit(self.drone_image, rect)
            else:
                pygame.draw.circle(
                    self.screen,
                    self._DRONE_COLOR,
                    (int(x), int(y)),
                    self._DRONE_RADIUS,
                )
                label = self.font.render(drone.label, True, (255, 255, 0))
                self.screen.blit(label, (x + 8, y - 8))

    def _draw_header(self) -> None:
        total = len(self.turns_log)
        text = (
            f"Turn {self.current_turn}/{total}  "
            "(SPACE/-> next, <- prev, ESC/Q quit)"
        )
        header = self.big_font.render(text, True, self._TEXT_COLOR)
        self.screen.blit(header, (10, 10))

    def run(self) -> None:
        running = True
        while running:
            dt = self.clock.tick(60) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_ESCAPE, pygame.K_q):
                        running = False
                    if event.key == pygame.K_RIGHT:
                        self._advance_turn()
                    if event.key == pygame.K_LEFT:
                        self._rewind_turn()

            self._update(dt)
            self._draw_background()
            self._draw_graph()
            self._draw_drones()
            self._draw_header()
            pygame.display.flip()

        pygame.quit()
