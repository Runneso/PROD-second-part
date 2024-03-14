from functools import lru_cache


class Reasons:
    invalid_token = "Переданный токен не существует либо некорректен."
    invalid_login_password = "Пользователь с указанным логином и паролем не найден."
    invalid_data = "Регистрационные данные не соответствуют ожидаемому формату и требованиям."
    invalid_unique = "Нарушено требование на уникальность авторизационных данных пользователей."
    invalid_alpha2 = "Страна с указанным кодом не найдена."


@lru_cache
def get_reasons():
    return Reasons
