#   Лабораторная работа №1 по дисциплине ЛОИС
#   Задача: реализовать прямой нечеткий логический вывод
#   Вариант: 1. Реализовать прямой нечеткий логический вывод, используя
#   треугольную норму min и нечеткую импликацию Гёделя
#   Авторы: Мяло В.В.
#           Сайковский А.В.
#           Вашкевич М.В.
#   Группа: 421702
#
#   Используемые источники:
#   1.https://libeldoc.bsuir.by/bitstream/123456789/992/2/Log_Osn.pdf
#   2.Липский Р.В. https://github.com/rastsislaux,
#   3.https://habr.com/ru/articles/111187("Прямой нечеткий логический вывод")

import re
from pathlib import Path


NAME_PATTERN = r"[A-Za-z][A-Za-z0-9]?"
FACT_PATTERN = re.compile(
    rf"^[ \t]*({NAME_PATTERN})[ \t]*=[ \t]*\{{([^}}\r\n]+)\}}[ \t]*\r?$",
    re.MULTILINE,
)
PAIR_PATTERN = re.compile(r"<([^,>]+),\s*((?:0|1(?:\.0+)?|0?\.\d+))>")
RULE_PATTERN = re.compile(
    rf"^[ \t]*({NAME_PATTERN})(?:\([^()\r\n]*\))?[ \t]*~>[ \t]*"
    rf"({NAME_PATTERN})(?:\([^()\r\n]*\))?[ \t]*\r?$",
    re.MULTILINE,
)


def build_godel_relation(antecedent, consequent):
    """Построить R(x, y) = I_G(A(x), B(y))."""
    relation = []
    for x, a_degree in antecedent:
        for y, b_degree in consequent:
            implication_degree = b_degree if a_degree > b_degree else 1.0
            relation.append((x, y, implication_degree))
    return relation


def max_min_composition(observation, relation):
    """Вычислить B'(y) = max_x min(A'(x), R(x, y))."""
    output_degrees = {}
    for x, observed_degree in observation:
        for source_x, y, relation_degree in relation:
            if x != source_x:
                continue
            candidate_degree = min(observed_degree, relation_degree)
            if y not in output_degrees or candidate_degree > output_degrees[y]:
                output_degrees[y] = candidate_degree
    return list(output_degrees.items())


def apply_fuzzy_rule(antecedent, consequent, observation):
    """Один шаг обобщённого modus ponens."""
    relation = build_godel_relation(antecedent, consequent)
    return max_min_composition(observation, relation)


def find_compatible_facts(antecedent, facts):
    """Факты, определённые на том же наборе элементов, что и посылка."""
    antecedent_domain = {element for element, _ in antecedent}
    compatible = {}
    for fact_name, memberships in facts.items():
        fact_domain = {element for element, _ in memberships}
        if fact_domain == antecedent_domain:
            compatible[fact_name] = memberships
    return compatible


def format_fuzzy_set(memberships):
    """Сохранить первоначальный формат печати результата."""
    return "{" + ",".join(f"<{element}, {degree}>" for element, degree in memberships) + "}"


def forward_fuzzy_inference(rules, facts):
    """Применять правила, пока база фактов не перестанет расширяться."""
    derivation_lines = []
    already_reported = []

    while True:
        facts_before_pass = len(facts)
        for antecedent_name, consequent_name in rules:
            antecedent = facts[antecedent_name]
            consequent = facts[consequent_name]
            suitable_observations = find_compatible_facts(antecedent, facts)

            for observed_name, observation in suitable_observations.items():
                derived_fact = apply_fuzzy_rule(antecedent, consequent, observation)
                derived_name = f"_{len(derivation_lines) + 1}"
                line = (
                    f"{{{observed_name}, {antecedent_name}(x)~>{consequent_name}(y)}} "
                    f"|~ {derived_name} = {format_fuzzy_set(derived_fact)}"
                )

                # Повтор уже известного исходного факта показываем один раз.
                if derived_fact in facts.values():
                    if derived_fact not in already_reported:
                        derivation_lines.append(line)
                        already_reported.append(derived_fact)
                    continue

                derivation_lines.append(line)
                facts[derived_name] = derived_fact
                already_reported.append(derived_fact)

        if len(facts) == facts_before_pass:
            break

    return "\n".join(derivation_lines)


def read_knowledge_base(filename):
    """Прочитать факты и правила из текстовой базы знаний."""
    content = Path(filename).read_text(encoding="utf-8")
    facts = {}
    rules = []

    for match in FACT_PATTERN.finditer(content):
        fact_name = match.group(1)
        body = match.group(2)
        elements = PAIR_PATTERN.findall(body)
        if body.count("<") != len(elements):
            raise ValueError(
                f"Степени принадлежности в факте {fact_name} "
                f"должны быть в диапазоне [0.0, 1.0]: {match.group(0).strip()}"
            )
        facts[fact_name] = [(item.strip(), float(degree)) for item, degree in elements]

    for match in RULE_PATTERN.finditer(content):
        rules.append((match.group(1), match.group(2)))

    return facts, rules


def main():
    facts, rules = read_knowledge_base(Path(__file__).with_name("input.txt"))
    print(forward_fuzzy_inference(rules, facts))


if __name__ == "__main__":
    main()
