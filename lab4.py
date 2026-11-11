# Лабораторная работа №4 (индивидуальная практическая работа 2), ЛОИС.
# Выполнена студентами группы 421702 БГУИР:
# Сайковский А. В., Мяло В. В., Вашкевич М. В.
# Обратный max-min вывод: все посылки, дающие известное следствие.
# Версия 2.0, 12.11.2026: один файл и прямое использование первой лабы.
# Источники: авторы lab1.py; Голенков В. В. и др., «ЛОИС. Практикум», 2011;
# E. Sanchez, https://doi.org/10.1016/S0019-9958(76)90446-0;
# Python Software Foundation, https://docs.python.org/3/library/.

import sys
from pathlib import Path

from lab1 import (
    FACT_PATTERN, RULE_PATTERN, read_knowledge_base, build_godel_relation,
    max_min_composition, format_fuzzy_set,
)


def read_problem(filename):
    """C - известное следствие; одно правило или факты-строки матрицы."""
    content = Path(filename).read_text(encoding="utf-8")
    for line in content.splitlines():
        if line.strip() and not line.lstrip().startswith("#"):
            if not (FACT_PATTERN.fullmatch(line) or RULE_PATTERN.fullmatch(line)):
                raise ValueError(f"Неверная строка: {line}")
    facts, rules = read_knowledge_base(filename)
    if "C" not in facts or len(rules) > 1:
        raise ValueError("Нужен факт C и не более одного правила")
    if len(list(FACT_PATTERN.finditer(content))) != len(facts):
        raise ValueError("Имена фактов не должны повторяться")
    if any(len(dict(pairs)) != len(pairs) or not pairs for pairs in facts.values()):
        raise ValueError("Нужны непустые множества без повторов элементов")
    if rules:
        left, right = rules[0]
        if left not in facts or right not in facts or "C" in (left, right):
            raise ValueError("Правило должно ссылаться на факты, отличные от C")
        relation = build_godel_relation(facts[left], facts[right])
    else:
        relation = [(x, y, r) for x, row in facts.items() if x != "C" for y, r in row]
    if not relation:
        raise ValueError("Отношение не задано")
    domain = set(dict(facts["C"]))
    for x in dict.fromkeys(x for x, _, _ in relation):
        if {y for source, y, _ in relation if source == x} != domain:
            raise ValueError("Каждая строка отношения должна иметь тот же универсум, что C")
    return relation, facts["C"]


def find_minimal_solutions(relation, conclusion, upper):
    """Выбрать свидетелей максимумов и оставить минимальные нижние границы."""
    names = list(upper)
    lower_bounds = {(0.0,) * len(names)}
    for y, target in conclusion:
        if target == 0:
            continue
        witnesses = [names.index(x) for x, column, r in relation
                     if column == y and r >= target and upper[x] >= target]
        candidates = set()
        for lower in lower_bounds:
            for i in witnesses:
                raised = list(lower)
                raised[i] = max(raised[i], target)
                candidates.add(tuple(raised))
                if len(candidates) > 10000:
                    raise ValueError("Слишком много вариантов; полное множество не вычислено")
        lower_bounds = {a for a in candidates if not any(
            other != a and all(v <= w for v, w in zip(other, a))
            for other in candidates
        )}
    return sorted(lower_bounds)


def inverse_fuzzy_inference(relation, conclusion):
    """Вернуть верхнюю границу и все минимальные решения, либо None."""
    targets = dict(conclusion)
    upper = dict.fromkeys((x for x, _, _ in relation), 1.0)
    for x, y, r in relation:
        if r > targets[y]:
            upper[x] = min(upper[x], targets[y])
    # Проверка существования решения - прямой вывод из первой лабы.
    restored = max_min_composition(list(upper.items()), relation)
    if dict(restored) != targets:
        return upper, None
    return upper, find_minimal_solutions(relation, conclusion, upper)


def format_result(relation, conclusion, upper, minima):
    """S - объединение областей [минимальное решение, верхняя граница]."""
    lines = ["Порядок координат: " + ", ".join(upper),
             "Следствие C = " + format_fuzzy_set(conclusion),
             "Верхняя граница = " + format_fuzzy_set(upper.items()),
             "Проверка = " + format_fuzzy_set(max_min_composition(list(upper.items()), relation))]
    if minima is None:
        return "\n".join(lines + ["Решений нет."])
    lines.append("Минимальные решения: " + str(minima))
    lines.append("S =")
    for index, lower in enumerate(minima):
        box = " x ".join(f"[{lo}, {hi}]" for lo, hi in zip(lower, upper.values()))
        lines.append(("  " if index == 0 else "  UNION ") + box)
    lines.append("Декартово произведение: " + ("да" if len(minima) == 1 else "нет"))
    return "\n".join(lines)


def main():
    filename = sys.argv[1] if len(sys.argv) > 1 else Path(__file__).with_name("lab4") / "input.txt"
    relation, conclusion = read_problem(filename)
    upper, minima = inverse_fuzzy_inference(relation, conclusion)
    print(format_result(relation, conclusion, upper, minima))


if __name__ == "__main__":
    # Одинаковая кодировка консоли, перенаправления вывода и файлов отчёта.
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    try:
        main()
    except (ValueError, OSError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        raise SystemExit(2)
