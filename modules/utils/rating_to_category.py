def rating_to_category(number: int) -> str:
    if number < 1350:
        return "Любитель"
    elif number < 1450:
        return "3-ий юношеский разряд"
    elif number < 1650:
        return "2-ой юношеский разряд"
    elif number < 1850:
        return "1-ый юношеский разряд"
    elif number < 1950:
        return "3-ый взрослый разряд"
    elif number < 2050:
        return "2-ой взрослый разряд"
    elif number < 2350:
        return "1-ый взрослый разряд"
    elif number < 2650:
        return "Кандидат мастера спорта"
    return "Мастер спорта"


def rating_to_category_easy(number: int) -> str:
    if number < 1500:
        return "Новичок"
    elif number < 2300:
        return "Любитель"
    return "Профессионал"


def rating_to_number_easy(number: int) -> int:
    if number < 1400:
        return 0
    elif number < 1750:
        return 1
    return 2


def rating_to_number(number: int) -> int:
    if number < 1350:
        return 0
    elif number < 1450:
        return 1
    elif number < 1650:
        return 2
    elif number < 1850:
        return 3
    elif number < 1950:
        return 4
    elif number < 2050:
        return 5
    elif number < 2350:
        return 6
    elif number < 2650:
        return 7
    return 8
