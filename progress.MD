# fly_in — Progresso do Projeto

## Estado Atual

Fase 1 em progresso — `src/models/` completa, `src/parser/` por iniciar.

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
    name: str       # obrigatório — sem default
    x: int          # obrigatório — sem default
    y: int          # obrigatório — sem default
    zone_type: ZoneType = ZoneType.NORMAL  # com default — vem depois
    max_drones: int = 1
    color: Optional[str] = None
    is_start: bool = False
    is_end: bool = False

    def __hash__(self) -> int:
        return hash(self.name)  # name é único — garantido pelo parser

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Zone):
            return NotImplemented
        return self.name == other.name  # só o name importa
```

---

### connection.py ✓

**O que faz:** Representa uma aresta bidirecional do grafo — liga duas zonas.

**Porquê `frozenset` no `__hash__`:**
Uma connection é bidirecional — `hub→roof1` e `roof1→hub` são a mesma ligação. O hash tem de ser igual nos dois sentidos. Um `frozenset` não tem ordem — `frozenset({A,B}) == frozenset({B,A})`. É imutável (ao contrário de `set`), logo pode ser hasheado.

**Porquê `set` normal no `__eq__`:**
Dentro do `__eq__` só estamos a comparar dois sets entre si, não a hashear — por isso não precisamos de imutabilidade. `{A,B} == {B,A}` funciona com `set` normal.

**Porquê redefinir `__eq__`:**
O `@dataclass` gera um `__eq__` que compara campo a campo — `zone1 == zone1` e `zone2 == zone2`. Isso significa que `hub→roof1 ≠ roof1→hub`. Mas são a mesma ligação, logo temos de redefinir.

**Porquê `NotImplemented` em vez de `False`:**
Quando `other` não é uma `Connection`, retornar `NotImplemented` diz ao Python para tentar o outro lado da comparação — permite que subclasses funcionem corretamente. `False` terminaria a comparação imediatamente.

**Porquê o método `involves`:**
O engine precisa de saber se um drone está a atravessar uma connection específica para verificar `max_link_capacity`. O `involves` encapsula essa lógica dentro da classe — o engine não precisa de saber que existem `zone1` e `zone2`.

**Conceitos aprendidos:**
- `frozenset` vs `set` — imutabilidade e hashability
- `isinstance` para type checking seguro no `__eq__`
- `NotImplemented` vs `False` em comparações
- Bidirecionalidade e como representá-la

```python
# Decisões de design chave
def __hash__(self) -> int:
    return hash(frozenset({self.zone1.name, self.zone2.name}))
    # frozenset — sem ordem, imutável, pode ser hasheado

def __eq__(self, other: object) -> bool:
    if not isinstance(other, Connection):
        return NotImplemented  # não False — permite herança
    return (
        {self.zone1.name, self.zone2.name} ==
        {other.zone1.name, other.zone2.name}
    )  # set normal chega — só comparamos, não hasheamos
```

---

### drone.py ✓

**O que faz:** Representa um drone individual na simulação com o seu estado, posição e caminho.

**Porquê `Enum` para `DroneState`:**
Um drone só pode estar num estado de cada vez. Com booleanos separados (`is_moving`, `is_waiting`, etc.) seria possível ter estados contraditórios. Com `Enum` é impossível — um único atributo `state: DroneState`.

**Porquê `field(default_factory=list)` para `path`:**
Em Python, usar `path: List[Zone] = []` numa dataclass criaria uma única lista partilhada entre todos os objetos `Drone`. Todos os drones estariam a escrever no mesmo caminho — um bug catastrófico e difícil de encontrar. O `field(default_factory=list)` cria uma lista nova e independente para cada instância.

**Porquê `@property` para `label` e `has_arrived`:**
`@property` transforma um método num atributo calculado — chamas `drone.label` sem parênteses. Para `label` é conveniente porque o formato `"D1"` é derivado do `drone_id`. Para `has_arrived` torna o código do engine mais legível do que comparar `drone.state == DroneState.ARRIVED` diretamente.

**Porquê `transit_destination`:**
Quando um drone entra em `IN_TRANSIT` (a caminho de uma zona `restricted`), precisa de guardar para onde vai — no turno seguinte o engine usa esta informação para mover o drone para o destino. Volta a `None` quando chega.

**Conceitos aprendidos:**
- `Enum` para estados mutuamente exclusivos
- `field(default_factory=list)` para listas como defaults em dataclasses
- `@property` para atributos calculados
- `Optional[Zone]` para valores que podem ser `None`

```python
# Decisões de design chave
state: DroneState = DroneState.WAITING
# Enum — impossível ter dois estados ao mesmo tempo

path: List[Zone] = field(default_factory=list)
# default_factory — lista independente por instância

@property
def label(self) -> str:
    return f"D{self.drone_id}"
# property — parece atributo, é código calculado
```

---

### graph.py ✓

**O que faz:** Contentor da rede completa — zonas, ligações e adjacency list. Construído pelo parser e passado ao pathfinder e ao engine.

**Porquê três estruturas internas:**
- `_zones: Dict[str, Zone]` — encontrar uma zona pelo nome em O(1). O parser precisa disto quando lê `connection: hub-roof1` — tem de encontrar os objetos `Zone` rapidamente.
- `_neighbours: Dict[Zone, List[Zone]]` — a adjacency list. O pathfinder chama `get_neighbors` a cada passo do algoritmo — tem de ser rápido.
- `_connections: Set[Connection]` — todas as ligações. O `set` usa `__hash__` e `__eq__` do `Connection` para detetar duplicatas automaticamente. O engine percorre isto para verificar `max_link_capacity`.

**Porquê atributos privados com `_`:**
Os atributos internos só devem ser modificados pelos métodos `add_zone` e `add_connection`, que têm validações. Se fossem públicos, código externo podia modificá-los sem validação. O underscore é uma convenção — não é privacidade forçada, mas sinaliza a intenção.

**Porquê `Optional[Zone]` para `_start_zone` e `_end_zone`:**
Quando o `Graph` é criado está vazio — o parser define estas zonas depois. Antes de serem definidas o valor é `None`. As properties `start_zone` e `end_zone` protegem o acesso — lançam `ValueError` se forem acedidas antes de estarem definidas.

**Porquê verificar `is_accessible()` em `add_connection`:**
A adjacency list só deve conter zonas acessíveis como vizinhos. Se uma zona `BLOCKED` fosse adicionada como vizinho, o pathfinder teria de a filtrar em cada passo. É mais eficiente filtrar uma vez em `add_connection`.

**Conceitos aprendidos:**
- Adjacency list como estrutura de grafo
- Atributos privados com underscore
- `@property` para acesso controlado com validação
- O(1) lookup com dicionários vs O(n) com listas

```python
# Estruturas internas — decisão de design central
self._zones: Dict[str, Zone] = {}             # O(1) lookup por nome
self._neighbours: Dict[Zone, List[Zone]] = {} # adjacency list
self._connections: Set[Connection] = set()    # sem duplicatas automático
self._start_zone: Optional[Zone] = None       # definida pelo parser
self._end_zone: Optional[Zone] = None         # definida pelo parser
```

---

## Passos Seguintes

### Fase 1 — Em curso

#### src/parser/ ← próximo
```
src/parser/
├── __init__.py
├── map_parser.py   ← lê o ficheiro e constrói o Graph
└── validators.py   ← validações isoladas reutilizáveis
```

O `map_parser.py` vai:
1. Abrir o ficheiro com context manager (`with open(...)`)
2. Ler linha a linha, ignorar comentários (`#`) e linhas vazias
3. Identificar o tipo de cada linha pelo prefixo (`nb_drones:`, `start_hub:`, `hub:`, `connection:`)
4. Extrair nome, coordenadas e metadados de cada zona
5. Criar objetos `Zone` e `Connection` e adicioná-los ao `Graph`
6. Lançar `ParseError` com número de linha e causa em caso de erro

---

### Fase 2 — Por iniciar

```
src/pathfinding/
├── __init__.py
├── dijkstra.py     ← algoritmo base de pathfinding
├── k_paths.py      ← K shortest paths (Yen's algorithm)
└── router.py       ← distribui drones por múltiplos caminhos
```

O Dijkstra vai usar `graph.get_neighbors()` e `zone.zone_type.movement_cost()` para encontrar o caminho de menor custo. O router vai usar K paths para distribuir drones em paralelo e minimizar turnos.

---

### Fase 3 — Por iniciar

```
src/simulation/
├── __init__.py
├── engine.py       ← motor de turnos
├── turn.py         ← representa um turno com os movimentos
├── scheduler.py    ← resolve conflitos de capacidade
└── output.py       ← formata "D1-roof1 D2-corridorA"
```

O engine vai criar um `Drone` por cada drone do mapa, atribuir caminhos via router, e simular turno a turno respeitando `max_drones` e `max_link_capacity`.

---

### Fase 4 — Por iniciar

```
src/renderer/
├── __init__.py
├── base_renderer.py      ← ABC com interface comum
├── terminal_renderer.py  ← colorama/rich
└── graphic_renderer.py   ← pygame/tkinter (opcional)
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