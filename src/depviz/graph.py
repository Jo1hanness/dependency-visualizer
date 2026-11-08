"""Построение графа зависимостей и операции над ним."""

from collections import deque
from dataclasses import dataclass, field

from depviz.apt_repo import RepositoryError

WHITE, GRAY, BLACK = 0, 1, 2


@dataclass
class DependencyGraph:
    """Граф зависимостей: корень, рёбра, порядок обхода."""

    root: str
    edges: dict = field(default_factory=dict)
    order: list = field(default_factory=list)
    missing: set = field(default_factory=set)

    def nodes(self):
        """Вернуть все вершины графа в порядке обхода."""
        return list(self.order)


def build_graph(repo, root, version=None):
    """Построить граф транзитивных зависимостей обходом BFS без рекурсии.

    Каждый пакет посещается один раз, поэтому циклические
    зависимости не приводят к зацикливанию. Версия учитывается
    только для корневого пакета.
    """
    start = repo.resolve(root)
    if start is None:
        raise RepositoryError(f"пакет {root} не найден в репозитории")
    graph = DependencyGraph(root=start)
    queue = deque([start])
    visited = {start}
    while queue:
        name = queue.popleft()
        graph.order.append(name)
        node_version = version if name == start else None
        deps = []
        for dep in repo.direct_dependencies(name, node_version):
            real = repo.resolve(dep)
            if real is None:
                graph.missing.add(dep)
                real = dep
            elif real not in visited:
                visited.add(real)
                queue.append(real)
            deps.append(real)
        graph.edges[name] = deps
    return graph


def find_cycle(edges, start):
    """Найти один цикл, достижимый из start (итеративный DFS).

    Возвращает список вершин цикла (первая повторена в конце)
    или пустой список, если циклов нет.
    """
    color = {start: GRAY}
    path = [start]
    stack = [iter(edges.get(start, []))]
    while stack:
        nxt = next(stack[-1], None)
        if nxt is None:
            color[path.pop()] = BLACK
            stack.pop()
            continue
        state = color.get(nxt, WHITE)
        if state == GRAY:
            return path[path.index(nxt):] + [nxt]
        if state == WHITE:
            color[nxt] = GRAY
            path.append(nxt)
            stack.append(iter(edges.get(nxt, [])))
    return []


def build_reverse_index(repo):
    """Построить словарь пакет -> пакеты, которые от него зависят."""
    reverse = {}
    for name in repo.all_packages():
        for dep in repo.direct_dependencies(name):
            real = repo.resolve(dep) or dep
            users = reverse.setdefault(real, [])
            if name not in users:
                users.append(name)
    return reverse


def reverse_dependencies(repo, target):
    """Найти все пакеты, зависящие от target (BFS без рекурсии).

    Используется тот же обход в ширину, что и для прямых
    зависимостей, но по обратным рёбрам.
    """
    start = repo.resolve(target) or target
    reverse = build_reverse_index(repo)
    if start not in reverse and repo.resolve(target) is None:
        raise RepositoryError(f"пакет {target} не найден в репозитории")
    graph = DependencyGraph(root=start)
    queue = deque([start])
    visited = {start}
    while queue:
        name = queue.popleft()
        graph.order.append(name)
        users = reverse.get(name, [])
        graph.edges[name] = list(users)
        for user in users:
            if user not in visited:
                visited.add(user)
                queue.append(user)
    return graph
