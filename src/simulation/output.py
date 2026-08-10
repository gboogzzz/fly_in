from typing import Dict, List
from ..models import Drone


class OutputFormatter:
    @staticmethod
    def format_turns(turns_log: List[Dict[Drone, str]]) -> List[str]:
        lines: List[str] = []

        for movements in turns_log:
            sorted_drones = sorted(movements.keys(), key=lambda d: d.drone_id)
            parts: List[str] = []
            for drone in sorted_drones:
                destiny = movements[drone]
                parts.append(f"{drone.label}-{destiny}")
            line = " ".join(parts)
            lines.append(line)
            
        return lines
        

