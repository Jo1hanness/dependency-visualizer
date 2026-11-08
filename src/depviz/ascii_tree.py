"""Вывод зависимостей в виде ASCII-дерева.

Каждый пакет раскрывается один раз; при повторной встрече он
помечается ``(*)`` и не раскрывается. Так дерево остаётся
конечным даже при циклических зависимостях.
"""

BRANCH = "├── "
LAST = "└── "
PIPE = "│   "
SPACE = "    "
REPEAT_MARK = " (*)"
MISSING_MARK = " (нет в репозитории)"


def render_tree(graph):
    """Вернуть список строк ASCII-дерева от корня графа."""
    lines = [graph.root]
    expanded = {graph.root}
    stack = []
    push_children(stack, graph.edges[graph.root], "")
    while stack:
        name, prefix, is_last = stack.pop()
        lines.append(prefix + (LAST if is_last else BRANCH)
                     + name + node_mark(graph, name, expanded))
        if name in expanded or name in graph.missing:
            continue
        expanded.add(name)
        child_prefix = prefix + (SPACE if is_last else PIPE)
        push_children(stack, graph.edges.get(name, []), child_prefix)
    return lines


def push_children(stack, children, prefix):
    """Положить детей в стек так, чтобы первый оказался сверху."""
    last_index = len(children) - 1
    for index in reversed(range(len(children))):
        stack.append((children[index], prefix, index == last_index))


def node_mark(graph, name, expanded):
    """Вернуть пометку вершины: повтор или отсутствие в репозитории."""
    if name in graph.missing:
        return MISSING_MARK
    if name in expanded:
        return REPEAT_MARK
    return ""
