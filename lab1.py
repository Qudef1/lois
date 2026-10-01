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

def implication(set1, set2):
    '''
    Импликация Гёделя
    a ~> b =b if a>b else 1
    :param set1:
    :param set2:
    :return:
    '''
    result = []
    for a in set1:
        for b in set2:
            impl_result = (a[0], b[0], b[1] if a[1] > b[1] else 1.0)
            result.append(impl_result)
    return result

#min
def composition(set1, impl_matrix):
    result = {}
    for a in set1:
        for cell in impl_matrix:
            if a[0] == cell[0]:
                mu = min(a[1], cell[2])
                if cell[1] not in result or mu > result[cell[1]]:
                    result[cell[1]] = mu
    return list(result.items())


def fill_missing_elements(set1, reference_set):
    set_values = dict(set1)
    reference_elements = {element for element, _ in reference_set}
    extra_elements = set(set_values) - reference_elements

    if extra_elements:
        names = ", ".join(sorted(extra_elements))
        raise ValueError(
            f"Элементы {names} отсутствуют в области определения правила"
        )

    return [
        (element, set_values.get(element, 0.0))
        for element, _ in reference_set
    ]


def inference(set1, set2, set3):
    set3 = fill_missing_elements(set3, set1)
    impl_matrix = implication(set1, set2)
    result = composition(set3, impl_matrix)
    return result


def set_to_str(set):
    pairs = []
    for pair in set:
        pairs.append(f"<{pair[0]}, {pair[1]}>")
    return "{" + ",".join(pairs) + "}"


def parse_inputs(filename):
    sets = {}
    rules = []
    requests = []

    set_pattern = re.compile(r"^(\w+)\s*=\s*\{([^}]+)\}\s*$")
    rule_pattern = re.compile(
        r"^(\w+)\s*\([^)]*\)\s*~>\s*(\w+)\s*\([^)]*\)\s*$"
    )
    request_pattern = re.compile(
        r"^\(\s*(\w+)\s*\([^)]*\)\s*,\s*"
        r"(\w+)\s*\([^)]*\)\s*~>\s*(\w+)\s*\([^)]*\)\s*\)\s*$"
    )

    with open(filename, "r", encoding="utf-8") as f:
        for line_number, source_line in enumerate(f, start=1):
            line = source_line.strip()
            if not line or line.startswith("#"):
                continue

            match = set_pattern.fullmatch(line)
            if match:
                name = match.group(1)
                elements = re.findall(
                    r"<([^,>]+),\s*([\d.]+)>", match.group(2)
                )
                sets[name] = [(x.strip(), float(mu)) for x, mu in elements]
                continue

            match = request_pattern.fullmatch(line)
            if match:
                requests.append(
                    (match.group(1), (match.group(2), match.group(3)))
                )
                continue

            match = rule_pattern.fullmatch(line)
            if match:
                rules.append((match.group(1), match.group(2)))
                continue

            raise ValueError(
                f"Не удалось распознать строку {line_number}: {line}"
            )

    return sets, rules, requests


if __name__ == "__main__":
    sets, rules, requests = parse_inputs("input.txt")

    for number, (fact_name, rule) in enumerate(requests, start=1):
        request = f"{{{fact_name}, {rule[0]}(x)~>{rule[1]}(y)}}"

        try:
            if fact_name not in sets:
                raise ValueError(f"множество {fact_name} не определено")
            if rule not in rules:
                raise ValueError(
                    f"правило {rule[0]}(x) ~> {rule[1]}(y) не объявлено"
                )
            if rule[0] not in sets or rule[1] not in sets:
                raise ValueError(
                    f"для правила {rule[0]} ~> {rule[1]} "
                    "не определены множества"
                )

            result = inference(
                sets[rule[0]], sets[rule[1]], sets[fact_name]
            )
        except ValueError as error:
            print(f"{request} |~ вывод сделать нельзя: {error}")
            continue

        print(f"{request} |~ {number} = {set_to_str(result)}")
