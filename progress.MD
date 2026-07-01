# fly_in — Progresso do Projeto

## Estado Atual

Fase 1 completa — `src/models/` e `src/parser/` implementados e testados.

---

## src/models/ ✓ Completo

### zone.py ✓

**O que faz:** Define o tipo de zona (`ZoneType`) e a classe `Zone` que representa um nó do grafo.

**Porquê `Enum` para `ZoneType`:**
O subject define exatamente 4 tipos de zona possíveis. Usar um `Enum` em vez de strings soltas garante type safety — o mypy rejeita valores inválidos em tempo de compilação. Com strings, um typo como `"normall"` passaria despercebido até runtime.

**Porquê `@dataclass` para `Zone`:**
A `Zone` é essencialmente um contentor de dados — `name`, `x`, `y`, `zone_type`, etc. O `@dataclass` gera automaticamente o `__init__`, `__repr__` e `__eq__`, eliminando boilerplate sem perder controlo.

**Porquê `__hash__` baseado só no `name`:**
O `graph.py` usa `Dict[Zone, List[Zone]]` para a adjacency list — para ser chave de dicionário, o objeto precisa de ser hashável. O `@dataclass` remove o `__hash__` quando gera o `__eq__`, por isso temos de o redefinir manualmente. Usamos só o `name` porque o parser garante que cada zona tem um nome único no grafo.

**Porquê `__eq__` baseado só no `name`:**
O `__eq__` gerado pelo `@dataclass` compara todos os campos. Mas duas zonas com o mesmo nome são obrigatoriamente a mesma zona — o parser garante isso. Se não redefiníssemos, `drone.current_zone == graph.end_zone` podia falhar se algum campo menor fosse diferente.

**Porquê `__post_init__` em vez de validar no `__init__`:**
O `@dataclass` gera o `__init__` automaticamente. O `__post_init__` é o único ponto onde podemos adicionar lógica de validação após a criação — sem ter de escrever o `__init__` à mão.

**Conceitos aprendidos:**
- `Enum` e `@classmethod` para factory methods
- `@dataclass` e geração automática de métodos
- `__post_init__` para validações em dataclasses
- `__hash__` e `__eq__` — relação entre os dois e porque o `@dataclass` remove o hash
- `Optional[str]` e type hints com mypy
- Forward references com `"ZoneType"` entre aspas

```python
# Decisões de design chave
@dataclass
class Zone:
    name: str
    x: int
    y: int
    zone_type: ZoneType = ZoneType.NORMAL
    max_drones: int = 1
    color: Optional[str] = None
    is_start: bool = False
    is_end: bool = False

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Zone):
            return NotImplemented
        return self.name == other.name
```

---

### connection.py ✓

**O que faz:** Representa uma aresta bidirecional do grafo — liga duas zonas.

**Porquê `frozenset` no `__hash__`:**
Uma connection é bidirecional — `hub→roof1` e `roof1→hub` são a mesma ligação. O hash tem de ser igual nos dois sentidos. Um `frozenset` não tem ordem — `frozenset({A,B}) == frozenset({B,A})`. É imutável (ao contrário de `set`), logo pode ser hasheado.

**Porquê `set` normal no `__eq__`:**
Dentro do `__eq__` só estamos a comparar dois sets entre si, não a hashear — por isso não precisamos de imutabilidade. `{A,B} == {B,A}` funciona com `set` normal.

**Porquê redefinir `__eq__`:**
O `@dataclass` gera um `__eq__` que compara campo a campo. Isso significa que `hub→roof1 ≠ roof1→hub`. Mas são a mesma ligação, logo temos de redefinir.

**Porquê `NotImplemented` em vez de `False`:**
Quando `other` não é uma `Connection`, retornar `NotImplemented` diz ao Python para tentar o outro lado da comparação — permite que subclasses funcionem corretamente.

**Conceitos aprendidos:**
- `frozenset` vs `set` — imutabilidade e hashability
- `isinstance` para type checking seguro no `__eq__`
- `NotImplemented` vs `False` em comparações
- Bidirecionalidade e como representá-la

---

### drone.py ✓

**O que faz:** Representa um drone individual na simulação com o seu estado, posição e caminho.

**Porquê `Enum` para `DroneState`:**
Um drone só pode estar num estado de cada vez. Com booleanos separados seria possível ter estados contraditórios. Com `Enum` é impossível.

**Porquê `field(default_factory=list)` para `path`:**
Usar `path: List[Zone] = []` numa dataclass criaria uma única lista partilhada entre todos os objetos `Drone`. O `field(default_factory=list)` cria uma lista nova e independente para cada instância.

**Conceitos aprendidos:**
- `Enum` para estados mutuamente exclusivos
- `field(default_factory=list)` para listas como defaults em dataclasses
- `@property` para atributos calculados
- `Optional[Zone]` para valores que podem ser `None`

---

### graphs.py ✓

**O que faz:** Contentor da rede completa — zonas, ligações e adjacency list. Construído pelo parser e passado ao pathfinder e ao engine.

**Três estruturas internas:**
- `_zones: Dict[str, Zone]` — O(1) lookup por nome
- `_neighbours: Dict[Zone, List[Zone]]` — adjacency list para o pathfinder
- `_connections: Set[Connection]` — sem duplicatas automático

**Conceitos aprendidos:**
- Adjacency list como estrutura de grafo
- Atributos privados com underscore
- `@property` para acesso controlado com validação
- O(1) lookup com dicionários vs O(n) com listas

---

### src/models/__init__.py ✓

**O que faz:** Re-exporta todas as classes do package para que outros módulos possam importar de `src.models` diretamente.

**Decisões de design:**
- Imports relativos com `.` — importa do mesmo package
- `__all__` como lista de strings — define a interface pública do módulo

```python
from .connection import Connection
from .drone import Drone, DroneState
from .graphs import Graph
from .zone import Zone, ZoneType

__all__ = [
    "Connection",
    "Drone",
    "DroneState",
    "Graph",
    "Zone",
    "ZoneType"
]
```

---

## src/parser/ ✓ Completo

### map_parser.py ✓

**O que faz:** Lê um ficheiro de mapa linha a linha, valida o conteúdo, constrói e devolve um `Graph` populado e o número de drones.

**Interface pública:**
```python
MapParser.parse(path: str) -> tuple[Graph, int]
```

**Estrutura interna:**
- `parse()` — orquestra a leitura e devolve `(graph, nb_drones)`
- `_parse_nb_drones()` — extrai e valida o número de drones
- `_parse_zone()` — cria objetos `Zone` e adiciona ao grafo
- `_parse_connection()` — cria objetos `Connection` e adiciona ao grafo
- `_parse_meta_data()` — extrai pares `key=value` dos blocos `[...]`
- `ParseError` — exceção com número de linha e causa

**Decisões de design:**
- `@staticmethod` em todos os métodos — o parser não tem estado próprio
- `MapParser.parse()` constrói e devolve o `Graph` diretamente — a `main` só orquestra
- Defaults inicializados antes do `if "[" in value` — evita `NameError` quando não há metadata
- `try/except ValueError` para aceder a `graph.start_zone` e `graph.end_zone` — as properties lançam exceção se não definidas
- `ZoneType.from_string()` para converter strings do ficheiro para o Enum antes de criar a `Zone`
- `graph.get_connection()` para verificar duplicados antes de adicionar

**Validações implementadas:**
- `nb_drones` ausente, não inteiro, ou não positivo
- `start_hub` ou `end_hub` ausentes
- Prefixo desconhecido
- Nome de zona com `-` ou espaço
- Coordenadas não inteiras
- `zone_type` inválido
- `max_drones` não positivo
- Zona duplicada
- Zona desconhecida numa connection
- Connection duplicada
- `max_link_capacity` não positivo
- Metadata mal formada (par sem `=`)

**Conceitos aprendidos:**
- `enumerate(f, start=1)` para iterar com número de linha
- `not line` para verificar string vazia (mais idiomático que `len(line) == 0`)
- `split(":", 1)` — split com limite para não partir valores que contenham `:`
- `dict.get(key, default)` para valores opcionais com default
- Imports relativos com `..` para subir um nível no package
- `super().__init__()` em exceções customizadas para propagar a mensagem
- `if __name__ == "__main__"` para evitar execução ao importar

**Casos de erro testados:**
- `nb_drones` negativo → `Error on line 1: the value of nb_drones needs to be positive`
- Ficheiro válido → parser constrói grafo corretamente com todas as zonas e tipos

---

## Passos Seguintes

### Fase 2 — Pathfinding ← próximo

```
src/pathfinding/
├── __init__.py
├── dijkstra.py     ← algoritmo base de pathfinding
├── k_paths.py      ← K shortest paths (Yen's algorithm)
└── router.py       ← distribui drones por múltiplos caminhos
```

**O que implementar:**

`dijkstra.py` — encontra o caminho de menor custo entre `start_zone` e `end_zone`:
- Usa `graph.get_neighbors()` para explorar vizinhos
- Usa `zone.zone_type.movement_cost()` para o custo de cada passo
- Ignora zonas `BLOCKED`
- Devolve a lista de zonas do caminho mais curto

`k_paths.py` — Yen's algorithm para encontrar os K caminhos mais curtos:
- Necessário para distribuir drones por múltiplos caminhos em paralelo
- Baseia-se no Dijkstra como subrotina

`router.py` — distribui drones pelos K caminhos:
- Atribui um caminho a cada drone
- Objetivo: minimizar o número de turnos totais

**Questões de design a decidir antes de implementar:**
- O Dijkstra devolve `List[Zone]` ou um objeto `Path`?
- Como representar o custo de zonas `restricted` (2 turnos)?
- O router atribui caminhos estaticamente (antes da simulação) ou dinamicamente (turno a turno)?

---

### Fase 3 — Simulação ← por iniciar

```
src/simulation/
├── __init__.py
├── engine.py
├── turn.py
├── scheduler.py
└── output.py
```

---

### Fase 4 — Renderer ← por iniciar

```
src/renderer/
├── __init__.py
├── base_renderer.py
├── terminal_renderer.py
└── graphic_renderer.py
```

---

## Relação entre os Módulos

```
Zone ←──────── Connection (tem zone1 e zone2)
 ↑                  ↑
 └────── Graph ─────┘ ← construído pelo MapParser
          ↑
        Drone (current_zone: Zone, path: List[Zone])
          ↑
       TurnEngine (usa Graph + Drones + Pathfinder)
          ↑
       OutputFormatter + Renderer
```

---

## Benchmarks Alvo

| Mapa | Drones | Target |
|------|--------|--------|
| Easy — linear | 2 | ≤ 6 turnos |
| Easy — fork | 4 | ≤ 8 turnos |
| Easy — capacity | 4 | ≤ 6 turnos |
| Medium — dead end | 5 | ≤ 12 turnos |
| Medium — loop | 6 | ≤ 15 turnos |
| Medium — priority | 5 | ≤ 12 turnos |
| Hard — maze | 8 | ≤ 30 turnos |
| Hard — capacity | 12 | ≤ 35 turnos |
| Hard — ultimate | 15 | ≤ 45 turnos |
| Challenger (bónus) | 25 | ≤ 45 turnos |