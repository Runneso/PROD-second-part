from re import fullmatch
from hashlib import sha256
from string import ascii_lowercase, ascii_uppercase
from schemas import *


def validate_login(login: str) -> bool:
    if len(login) > 30 or len(login) == 0:
        return False
    if fullmatch(r'[a-zA-Z0-9-]+', login) is None:
        return False
    return True


def validate_password(password: str) -> bool:
    if len(password) > 100 or len(password) < 6:
        return False
    if not any(char.isdigit() for char in password):
        return False
    if not any(char in ascii_lowercase for char in password):
        return False
    if not any(char in ascii_uppercase for char in password):
        return False
    return True


def validate_email(email: str) -> bool:
    if len(email) > 50 or len(email) == 0:
        return False
    return True


def validate_countryCode(countryCode: str) -> bool:
    if len(countryCode) != 2:
        return False
    if fullmatch(r'[a-zA-Z]{2}', countryCode) is None:
        return False
    return True


def validate_phone(phone: str) -> bool:
    if not phone:
        return True
    if fullmatch(r'\+[\d]+', phone) is None:
        return False
    if len(phone) > 20:
        return False
    return True


def validate_image(image: str) -> bool:
    if not image:
        return True
    if len(image) > 200:
        return False
    return True


def validate_limit(limit: int) -> bool:
    if 0 <= limit <= 50:
        return True
    return False


def validate_offset(offset: int) -> bool:
    if offset < 0:
        return False
    return True


def validate_content(content: str) -> bool:
    if len(content) > 1_000 or len(content) == 0:
        return False
    return True


def validate_tags(tags: List[str]) -> bool:
    if any(len(tag) > 20 or len(tag) == 0 for tag in tags):
        return False
    return True


def validate_data(user_data: User) -> bool:
    if not validate_login(user_data.login):
        return False
    if not validate_email(user_data.email):
        return False
    if not validate_password(user_data.password):
        return False
    if not validate_countryCode(user_data.countryCode):
        return False
    if not validate_phone(user_data.phone):
        return False
    if not validate_image(user_data.image):
        return False
    return True


def validate_profile(user_data: User) -> Profile:
    if user_data.image is None and user_data.phone is None:
        return Profile(profile=UserProfileWithoutImageAndPhone(login=user_data.login, email=user_data.email,
                                                               countryCode=user_data.countryCode,
                                                               isPublic=user_data.isPublic))
    elif user_data.image is None:
        return Profile(profile=UserProfileWithoutImage(login=user_data.login, email=user_data.email,
                                                       countryCode=user_data.countryCode,
                                                       isPublic=user_data.isPublic, phone=user_data.phone))
    elif user_data.phone is None:
        return Profile(profile=UserProfileWithoutPhone(login=user_data.login, email=user_data.email,
                                                       countryCode=user_data.countryCode,
                                                       isPublic=user_data.isPublic, image=user_data.image))

    return Profile(profile=UserProfile(login=user_data.login, email=user_data.email, phone=user_data.phone,
                                       countryCode=user_data.countryCode, isPublic=user_data.isPublic,
                                       image=user_data.image))


def validate_user(user_data: User) -> Union[
    UserProfile, UserProfileWithoutImage, UserProfileWithoutPhone, UserProfileWithoutImageAndPhone]:
    if user_data.image is None and user_data.phone is None:
        return UserProfileWithoutImageAndPhone(login=user_data.login, email=user_data.email,
                                               countryCode=user_data.countryCode,
                                               isPublic=user_data.isPublic)
    elif user_data.image is None:
        return UserProfileWithoutImage(login=user_data.login, email=user_data.email,
                                       countryCode=user_data.countryCode,
                                       isPublic=user_data.isPublic, phone=user_data.phone)
    elif user_data.phone is None:
        return UserProfileWithoutPhone(login=user_data.login, email=user_data.email,
                                       countryCode=user_data.countryCode,
                                       isPublic=user_data.isPublic, image=user_data.image)

    return UserProfile(login=user_data.login, email=user_data.email, phone=user_data.phone,
                       countryCode=user_data.countryCode, isPublic=user_data.isPublic,
                       image=user_data.image)


def validate_update_profile(user_data: UpdateProfile) -> bool:
    if user_data.countryCode is not None and not validate_countryCode(user_data.countryCode):
        return False
    if user_data.phone is not None and not validate_phone(user_data.phone):
        return False
    if user_data.image is not None and not validate_image(user_data.image):
        return False
    return True


def get_hash(password: str) -> str:
    return sha256(bytes(password, encoding="utf-8")).hexdigest()
