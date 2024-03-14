import uvicorn
from fastapi import FastAPI, APIRouter, status, Query, Response, Header, Depends, Request
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import sessionmaker
from starlette.responses import JSONResponse
from settings import get_settings
from reasons import get_reasons
from crud import CRUD
from datetime import datetime
from uuid import uuid4
from time import time
from models import *
from schemas import *
from validators import *
from typing import *
from const import *

api = FastAPI()
countries = APIRouter()
auth = APIRouter()
me = APIRouter()
profiles = APIRouter()
friends = APIRouter()
posts = APIRouter()
routers = [countries, auth, me, profiles, friends, posts]

reasons = get_reasons()
settings = get_settings()

session_maker = sessionmaker(bind=engine)
db = CRUD()


def get_session():
    with session_maker() as session:
        yield session


version = "v1"
prefix = "/api/"


@api.get(prefix + "ping", status_code=200)
async def ping():
    return Status(status=OK)


@countries.get(prefix + "countries", status_code=200)
async def get_list_countries(response: Response, region: List[str] = Query(None), session=Depends(get_session)):
    array_countries = db.get_countries(session)
    array_countries = list(array_countries)

    if region is None or region == [""]:
        array_countries = [Country(name=country.name, alpha2=country.alpha2,
                                   alpha3=country.alpha3, region=country.region) for country in array_countries]
        return array_countries
    elif any(item not in ENUM for item in region):
        response.status_code = status.HTTP_400_BAD_REQUEST
        return ErrorResponse(reason=reasons.invalid_data)
    else:
        array_countries = [country for country in array_countries if country.region in region]
        array_countries = [Country(name=country.name, alpha2=country.alpha2,
                                   alpha3=country.alpha3, region=country.region) for country in array_countries]
        return array_countries


@countries.get(prefix + "countries/{alpha2}", status_code=200)
async def get_country(alpha2: str, response: Response, session=Depends(get_session)):
    if not validate_countryCode(alpha2):
        response.status_code = status.HTTP_400_BAD_REQUEST
        return ErrorResponse(reason=reasons.invalid_data)

    country = db.get_country_by_alpha2(session, alpha2)
    country = country.one_or_none()

    if country is None:
        response.status_code = status.HTTP_404_NOT_FOUND
        return ErrorResponse(reason=reasons.invalid_alpha2)
    return Country(name=country.name, alpha2=country.alpha2,
                   alpha3=country.alpha3, region=country.region)


@auth.post(prefix + "auth/register", status_code=201)
async def post_register_a_user(user_data: User, response: Response, session=Depends(get_session)):
    array_users = db.get_users(session)
    array_users = list(array_users)

    for user in array_users:
        if user_data.login == user.login or user_data.email == user.email or (
                user_data.phone == user.phone and user_data.phone is not None):
            response.status_code = status.HTTP_409_CONFLICT
            return ErrorResponse(reason=reasons.invalid_unique)

    if not validate_data(user_data):
        response.status_code = status.HTTP_400_BAD_REQUEST
        return ErrorResponse(reason=reasons.invalid_data)

    new_user = Users(login=user_data.login, password=get_hash(user_data.password), email=user_data.email,
                     phone=user_data.phone,
                     countryCode=user_data.countryCode, isPublic=user_data.isPublic, image=user_data.image)

    db.post_create_user(session, new_user)

    return validate_profile(user_data)


@auth.post(prefix + "auth/sign-in", status_code=200)
async def post_sing_in(user_data: SingInUser, response: Response, session=Depends(get_session)):
    user = (db.get_user_by_login(session, user_data.login)).one_or_none()

    if user is None:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return ErrorResponse(reason=reasons.invalid_login_password)

    if not validate_password(user_data.password):
        response.status_code = status.HTTP_400_BAD_REQUEST
        return ErrorResponse(reason=reasons.invalid_data)

    if get_hash(user_data.password) != user.password:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return ErrorResponse(reason=reasons.invalid_login_password)

    token_value = str(uuid4())
    token = Tokens(login=user_data.login, token=token_value, creation_time=time())
    db.post_create_token(session, token)
    return Token(token=token_value)


@me.get(prefix + "me/profile", status_code=200)
async def get_my_profile(response: Response, Authorization: Optional[str] = Header(default=None),
                         session=Depends(get_session)):
    if Authorization is None:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return ErrorResponse(reason=reasons.invalid_token)

    token = Authorization.split()

    if len(token) != 2:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return ErrorResponse(reason=reasons.invalid_token)

    token = token[1]
    token = (db.get_token_by_token(session, token)).one_or_none()

    if token is None:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return ErrorResponse(reason=reasons.invalid_token)

    if time() - token.creation_time >= DAY_TIME:
        db.delete_token(session, token)
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return ErrorResponse(reason=reasons.invalid_token)

    user = (db.get_user_by_login(session, token.login)).one()

    return validate_user(User(login=user.login, password=user.password, email=user.email, countryCode=user.countryCode,
                              isPublic=user.isPublic, phone=user.phone, image=user.image))


@me.patch(prefix + "me/profile", status_code=200)
async def patch_my_profile(response: Response, user_data: UpdateProfile,
                           Authorization: Optional[str] = Header(default=None), session=Depends(get_session)):
    if Authorization is None:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return ErrorResponse(reason=reasons.invalid_token)

    token = Authorization.split()

    if len(token) != 2:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return ErrorResponse(reason=reasons.invalid_token)

    token = token[1]
    token = (db.get_token_by_token(session, token)).one_or_none()

    if token is None:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return ErrorResponse(reason=reasons.invalid_token)

    if time() - token.creation_time >= DAY_TIME:
        db.delete_token(session, token)
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return ErrorResponse(reason=reasons.invalid_token)

    if not validate_update_profile(user_data):
        response.status_code = status.HTTP_400_BAD_REQUEST
        return ErrorResponse(reason=reasons.invalid_data)

    if user_data.countryCode is not None:
        country = (db.get_country_by_alpha2(session, user_data.countryCode)).one_or_none()
        if country is None:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return ErrorResponse(reason=reasons.invalid_data)

    if user_data.phone is not None:
        user = (db.get_user_by_phone(session, user_data.phone)).one_or_none()
        if user is not None:
            response.status_code = status.HTTP_409_CONFLICT
            return ErrorResponse(reason=reasons.invalid_unique)

    db.update_user_by_login(session, token.login, user_data)
    user = (db.get_user_by_login(session, token.login)).one()

    return validate_user(
        User(login=user.login, password=user.password, email=user.email, countryCode=user.countryCode,
             isPublic=user.isPublic, phone=user.phone, image=user.image))


@me.post(prefix + "me/updatePassword", status_code=200)
async def update_my_password(response: Response, user_data: UpdatePassword,
                             Authorization: Optional[str] = Header(default=None), session=Depends(get_session)):
    if Authorization is None:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return ErrorResponse(reason=reasons.invalid_token)

    token = Authorization.split()

    if len(token) != 2:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return ErrorResponse(reason=reasons.invalid_token)

    token = token[1]
    token = (db.get_token_by_token(session, token)).one_or_none()

    if token is None:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return ErrorResponse(reason=reasons.invalid_token)

    if time() - token.creation_time >= DAY_TIME:
        db.delete_token(session, token)
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return ErrorResponse(reason=reasons.invalid_token)

    if not validate_password(user_data.newPassword):
        response.status_code = status.HTTP_400_BAD_REQUEST
        return ErrorResponse(reason=reasons.invalid_data)

    user = (db.get_user_by_login(session, token.login)).one()

    if get_hash(user_data.oldPassword) != user.password:
        response.status_code = status.HTTP_403_FORBIDDEN
        return ErrorResponse(reason=reasons.invalid_login_password)

    db.update_password_by_login(session, user.login, user_data.newPassword)
    db.delete_tokens_by_login(session, user.login)
    return Status(status=OK)


@profiles.get(prefix + "profiles/{login}", status_code=200)
async def get_profile(response: Response, login: str,
                      Authorization: Optional[str] = Header(default=None), session=Depends(get_session)):
    if Authorization is None:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return ErrorResponse(reason=reasons.invalid_token)

    token = Authorization.split()

    if len(token) != 2:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return ErrorResponse(reason=reasons.invalid_token)

    token = token[1]
    token = (db.get_token_by_token(session, token)).one_or_none()

    if token is None:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return ErrorResponse(reason=reasons.invalid_token)

    if time() - token.creation_time >= DAY_TIME:
        db.delete_token(session, token)
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return ErrorResponse(reason=reasons.invalid_token)

    user = (db.get_user_by_login(session, login)).one_or_none()

    if login == token.login:
        return validate_user(
            User(login=user.login, password=user.password, email=user.email, countryCode=user.countryCode,
                 isPublic=user.isPublic, phone=user.phone, image=user.image))

    if user is None:
        response.status_code = status.HTTP_403_FORBIDDEN
        return ErrorResponse(reason=reasons.invalid_data)

    if not user.isPublic:
        array_friends = (db.get_friends_by_login(session, login)).all()
        if any(friend.friend == token.login for friend in array_friends):
            return validate_user(
                User(login=user.login, password=user.password, email=user.email, countryCode=user.countryCode,
                     isPublic=user.isPublic, phone=user.phone, image=user.image))
        else:
            response.status_code = status.HTTP_403_FORBIDDEN
            return ErrorResponse(reason=reasons.invalid_data)

    return validate_user(
        User(login=user.login, password=user.password, email=user.email, countryCode=user.countryCode,
             isPublic=user.isPublic, phone=user.phone, image=user.image))


@friends.post(prefix + "friends/add", status_code=200)
async def post_add_friend(response: Response, user_data: AddFriend,
                          Authorization: Optional[str] = Header(default=None), session=Depends(get_session)):
    if Authorization is None:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return ErrorResponse(reason=reasons.invalid_token)

    token = Authorization.split()

    if len(token) != 2:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return ErrorResponse(reason=reasons.invalid_token)

    token = token[1]
    token = (db.get_token_by_token(session, token)).one_or_none()

    if token is None:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return ErrorResponse(reason=reasons.invalid_token)

    if time() - token.creation_time >= DAY_TIME:
        db.delete_token(session, token)
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return ErrorResponse(reason=reasons.invalid_token)

    user = (db.get_user_by_login(session, user_data.login)).one_or_none()

    if user is None:
        response.status_code = status.HTTP_404_NOT_FOUND
        return ErrorResponse(reason=reasons.invalid_data)

    already = (db.get_friend_by_login(session, token.login, user_data.login)).one_or_none()

    if already is not None:
        return Status(status=OK)

    date = datetime.now().strftime(TIME_PATTERN) + "07:00"
    db.post_create_friend(session, Friends(login=token.login, friend=user_data.login, addedAt=date))
    return Status(status=OK)


@friends.post(prefix + "friends/remove", status_code=200)
async def post_add_friend(response: Response, user_data: RemoveFriend,
                          Authorization: Optional[str] = Header(default=None), session=Depends(get_session)):
    if Authorization is None:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return ErrorResponse(reason=reasons.invalid_token)

    token = Authorization.split()

    if len(token) != 2:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return ErrorResponse(reason=reasons.invalid_token)

    token = token[1]
    token = (db.get_token_by_token(session, token)).one_or_none()

    if token is None:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return ErrorResponse(reason=reasons.invalid_token)

    if time() - token.creation_time >= DAY_TIME:
        db.delete_token(session, token)
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return ErrorResponse(reason=reasons.invalid_token)

    already = (db.get_friend_by_login(session, token.login, user_data.login)).one_or_none()

    if already is None:
        return Status(status=OK)

    db.delete_friend(session, already)
    return Status(status=OK)


@friends.get(prefix + "friends", status_code=200)
async def get_my_friends(response: Response,
                         Authorization: Optional[str] = Header(default=None),
                         limit: Optional[int] = Query(5),
                         offset: Optional[int] = Query(0), session=Depends(get_session)):
    if Authorization is None:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return ErrorResponse(reason=reasons.invalid_token)

    token = Authorization.split()

    if len(token) != 2:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return ErrorResponse(reason=reasons.invalid_token)

    token = token[1]
    token = (db.get_token_by_token(session, token)).one_or_none()

    if token is None:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return ErrorResponse(reason=reasons.invalid_token)

    if time() - token.creation_time >= DAY_TIME:
        db.delete_token(session, token)
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return ErrorResponse(reason=reasons.invalid_token)

    if not validate_limit(limit):
        response.status_code = status.HTTP_400_BAD_REQUEST
        return ErrorResponse(reason=reasons.invalid_token)

    if not validate_offset(offset):
        response.status_code = status.HTTP_400_BAD_REQUEST
        return ErrorResponse(reason=reasons.invalid_token)

    array_friends = (db.get_friends_by_login(session, token.login)).all()
    array_friends = sorted(array_friends,
                           key=lambda friend: datetime.strptime(friend.addedAt[:-5], TIME_PATTERN),
                           reverse=True)
    array_friends = array_friends[offset:]
    array_friends = array_friends[:limit]
    return [Friend(login=friend.friend, addedAt=friend.addedAt) for friend in array_friends]


@posts.post(prefix + "posts/new", status_code=200)
async def post_add_post(response: Response,
                        post_data: AddPost,
                        Authorization: Optional[str] = Header(default=None),
                        session=Depends(get_session)):
    if Authorization is None:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return ErrorResponse(reason=reasons.invalid_token)

    token = Authorization.split()

    if len(token) != 2:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return ErrorResponse(reason=reasons.invalid_token)

    token = token[1]
    token = (db.get_token_by_token(session, token)).one_or_none()

    if token is None:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return ErrorResponse(reason=reasons.invalid_token)

    if time() - token.creation_time >= DAY_TIME:
        db.delete_token(session, token)
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return ErrorResponse(reason=reasons.invalid_token)

    if not validate_content(post_data.content):
        response.status_code = status.HTTP_400_BAD_REQUEST
        return ErrorResponse(reason=reasons.invalid_token)

    if not validate_tags(post_data.tags):
        response.status_code = status.HTTP_400_BAD_REQUEST
        return ErrorResponse(reason=reasons.invalid_token)

    post_id = str(uuid4())
    date = datetime.now().strftime(TIME_PATTERN) + "07:00"
    db.post_create_post(session, Posts(id=post_id, author=token.login, content=post_data.content,
                                       tags=post_data.tags, createdAt=date,
                                       likesCount=0, dislikesCount=0))
    return Post(id=post_id, author=token.login, content=post_data.content,
                tags=post_data.tags, createdAt=date,
                likesCount=0, dislikesCount=0)


@posts.get(prefix + "posts/{postId}", status_code=200)
async def get_post(response: Response,
                   postId: str,
                   Authorization: Optional[str] = Header(default=None),
                   session=Depends(get_session)):
    if Authorization is None:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return ErrorResponse(reason=reasons.invalid_token)

    token = Authorization.split()

    if len(token) != 2:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return ErrorResponse(reason=reasons.invalid_token)

    token = token[1]
    token = (db.get_token_by_token(session, token)).one_or_none()

    if token is None:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return ErrorResponse(reason=reasons.invalid_token)

    if time() - token.creation_time >= DAY_TIME:
        db.delete_token(session, token)
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return ErrorResponse(reason=reasons.invalid_token)

    post = (db.get_post_by_id(session, postId)).one_or_none()

    if post is None:
        response.status_code = status.HTTP_404_NOT_FOUND
        return ErrorResponse(reason=reasons.invalid_data)

    author = (db.get_user_by_login(session, post.author)).one()

    if token.login == author.login:
        return Post(id=post.id, content=post.content, author=post.author,
                    tags=post.tags, createdAt=post.createdAt, likesCount=post.likesCount,
                    dislikesCount=post.dislikesCount)

    if not author.isPublic:
        array_friends = (db.get_friends_by_login(session, author.login)).all()
        if any(friend.friend == token.login for friend in array_friends):
            return Post(id=post.id, content=post.content, author=post.author,
                        tags=post.tags, createdAt=post.createdAt, likesCount=post.likesCount,
                        dislikesCount=post.dislikesCount)
        else:
            response.status_code = status.HTTP_404_NOT_FOUND
            return ErrorResponse(reason=reasons.invalid_data)

    return Post(id=post.id, content=post.content, author=post.author,
                tags=post.tags, createdAt=post.createdAt, likesCount=post.likesCount,
                dislikesCount=post.dislikesCount)


@posts.get(prefix + "posts/feed/my", status_code=200)
async def get_my_feed(response: Response,
                      Authorization: Optional[str] = Header(default=None),
                      limit: Optional[int] = Query(5),
                      offset: Optional[int] = Query(0), session=Depends(get_session)):
    if Authorization is None:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return ErrorResponse(reason=reasons.invalid_token)

    token = Authorization.split()

    if len(token) != 2:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return ErrorResponse(reason=reasons.invalid_token)

    token = token[1]
    token = (db.get_token_by_token(session, token)).one_or_none()

    if token is None:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return ErrorResponse(reason=reasons.invalid_token)

    if time() - token.creation_time >= DAY_TIME:
        db.delete_token(session, token)
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return ErrorResponse(reason=reasons.invalid_token)

    array_posts = (db.get_posts_by_login(session, token.login)).all()
    array_posts = sorted(array_posts, key=lambda post: datetime.strptime(post.createdAt[:-5], TIME_PATTERN),
                         reverse=True)
    array_posts = array_posts[offset:]
    array_posts = array_posts[:limit]
    return [Post(id=post.id, content=post.content, author=post.author,
                 tags=post.tags, createdAt=post.createdAt, likesCount=post.likesCount,
                 dislikesCount=post.dislikesCount) for post in array_posts]


@posts.get(prefix + "posts/feed/{login}", status_code=200)
async def get_feed(response: Response,
                   login: str,
                   Authorization: Optional[str] = Header(default=None),
                   limit: Optional[int] = Query(5),
                   offset: Optional[int] = Query(0),
                   session=Depends(get_session)):
    if Authorization is None:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return ErrorResponse(reason=reasons.invalid_token)

    token = Authorization.split()

    if len(token) != 2:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return ErrorResponse(reason=reasons.invalid_token)

    token = token[1]
    token = (db.get_token_by_token(session, token)).one_or_none()

    if token is None:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return ErrorResponse(reason=reasons.invalid_token)

    if time() - token.creation_time >= DAY_TIME:
        db.delete_token(session, token)
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return ErrorResponse(reason=reasons.invalid_token)

    author = (db.get_user_by_login(session, login)).one_or_none()

    if author is None:
        response.status_code = status.HTTP_404_NOT_FOUND
        return ErrorResponse(reason=reasons.invalid_token)

    array_posts = (db.get_posts_by_login(session, login)).all()
    array_posts = sorted(array_posts, key=lambda post: datetime.strptime(post.createdAt[:-5], TIME_PATTERN),
                         reverse=True)

    if token.login == author.login:
        array_posts = array_posts[offset:]
        array_posts = array_posts[:limit]
        return [Post(id=post.id, content=post.content, author=post.author,
                     tags=post.tags, createdAt=post.createdAt, likesCount=post.likesCount,
                     dislikesCount=post.dislikesCount) for post in array_posts]

    if not author.isPublic:
        array_friends = (db.get_friends_by_login(session, author.login)).all()
        if any(friend.friend == token.login for friend in array_friends):
            return [Post(id=post.id, content=post.content, author=post.author,
                         tags=post.tags, createdAt=post.createdAt, likesCount=post.likesCount,
                         dislikesCount=post.dislikesCount) for post in array_posts]
        else:
            response.status_code = status.HTTP_404_NOT_FOUND
            return ErrorResponse(reason=reasons.invalid_data)

    return [Post(id=post.id, content=post.content, author=post.author,
                 tags=post.tags, createdAt=post.createdAt, likesCount=post.likesCount,
                 dislikesCount=post.dislikesCount) for post in array_posts]


@posts.post(prefix + "posts/{postId}/like", status_code=200)
async def post_like_post(response: Response,
                         postId: str,
                         Authorization: Optional[str] = Header(default=None),
                         session=Depends(get_session)):
    if Authorization is None:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return ErrorResponse(reason=reasons.invalid_token)

    token = Authorization.split()

    if len(token) != 2:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return ErrorResponse(reason=reasons.invalid_token)

    token = token[1]
    token = (db.get_token_by_token(session, token)).one_or_none()

    if token is None:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return ErrorResponse(reason=reasons.invalid_token)

    if time() - token.creation_time >= DAY_TIME:
        db.delete_token(session, token)
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return ErrorResponse(reason=reasons.invalid_token)

    post = (db.get_post_by_id(session, postId)).one_or_none()

    if post is None:
        response.status_code = status.HTTP_404_NOT_FOUND
        return ErrorResponse(reason=reasons.invalid_data)

    author = (db.get_user_by_login(session, post.author)).one()

    if token.login == author.login:
        mark = (db.get_mark_for_post(session, postId, token.login)).one_or_none()

        if mark is None:
            db.post_create_mark(session, Marks(post_id=postId, login=token.login, liked=True))
            db.increment_like(session, postId)
            post = (db.get_post_by_id(session, postId)).one()
            return Post(id=post.id, content=post.content, author=post.author,
                        tags=post.tags, createdAt=post.createdAt, likesCount=post.likesCount,
                        dislikesCount=post.dislikesCount)
        elif mark.liked:
            return Post(id=post.id, content=post.content, author=post.author,
                        tags=post.tags, createdAt=post.createdAt, likesCount=post.likesCount,
                        dislikesCount=post.dislikesCount)
        else:
            db.change_mark(session, postId, token.login)
            db.increment_like(session, postId)
            db.decrement_dislike(session, postId)
            post = (db.get_post_by_id(session, postId)).one()
            return Post(id=post.id, content=post.content, author=post.author,
                        tags=post.tags, createdAt=post.createdAt, likesCount=post.likesCount,
                        dislikesCount=post.dislikesCount)

    if not author.isPublic:
        array_friends = (db.get_friends_by_login(session, author.login)).all()
        if any(friend.friend == token.login for friend in array_friends):
            mark = (db.get_mark_for_post(session, postId, token.login)).one_or_none()

            if mark is None:
                db.post_create_mark(session, Marks(post_id=postId, login=token.login, liked=True))
                db.increment_like(session, postId)
                post = (db.get_post_by_id(session, postId)).one()
                return Post(id=post.id, content=post.content, author=post.author,
                            tags=post.tags, createdAt=post.createdAt, likesCount=post.likesCount,
                            dislikesCount=post.dislikesCount)
            elif mark.liked:
                return Post(id=post.id, content=post.content, author=post.author,
                            tags=post.tags, createdAt=post.createdAt, likesCount=post.likesCount,
                            dislikesCount=post.dislikesCount)
            else:
                db.change_mark(session, postId, token.login)
                db.increment_like(session, postId)
                db.decrement_dislike(session, postId)
                post = (db.get_post_by_id(session, postId)).one()
                return Post(id=post.id, content=post.content, author=post.author,
                            tags=post.tags, createdAt=post.createdAt, likesCount=post.likesCount,
                            dislikesCount=post.dislikesCount)
        else:
            response.status_code = status.HTTP_404_NOT_FOUND
            return ErrorResponse(reason=reasons.invalid_data)

    mark = (db.get_mark_for_post(session, postId, token.login)).one_or_none()

    if mark is None:
        db.post_create_mark(session, Marks(post_id=postId, login=token.login, liked=True))
        db.increment_like(session, postId)
        post = (db.get_post_by_id(session, postId)).one()
        return Post(id=post.id, content=post.content, author=post.author,
                    tags=post.tags, createdAt=post.createdAt, likesCount=post.likesCount,
                    dislikesCount=post.dislikesCount)
    elif mark.liked:
        return Post(id=post.id, content=post.content, author=post.author,
                    tags=post.tags, createdAt=post.createdAt, likesCount=post.likesCount,
                    dislikesCount=post.dislikesCount)
    else:
        db.change_mark(session, postId, token.login)
        db.increment_like(session, postId)
        db.decrement_dislike(session, postId)
        post = (db.get_post_by_id(session, postId)).one()
        return Post(id=post.id, content=post.content, author=post.author,
                    tags=post.tags, createdAt=post.createdAt, likesCount=post.likesCount,
                    dislikesCount=post.dislikesCount)


@posts.post(prefix + "posts/{postId}/dislike", status_code=200)
async def post_dislike_post(response: Response,
                            postId: str,
                            Authorization: Optional[str] = Header(default=None),
                            session=Depends(get_session)):
    if Authorization is None:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return ErrorResponse(reason=reasons.invalid_token)

    token = Authorization.split()

    if len(token) != 2:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return ErrorResponse(reason=reasons.invalid_token)

    token = token[1]
    token = (db.get_token_by_token(session, token)).one_or_none()

    if token is None:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return ErrorResponse(reason=reasons.invalid_token)

    if time() - token.creation_time >= DAY_TIME:
        db.delete_token(session, token)
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return ErrorResponse(reason=reasons.invalid_token)

    post = (db.get_post_by_id(session, postId)).one_or_none()

    if post is None:
        response.status_code = status.HTTP_404_NOT_FOUND
        return ErrorResponse(reason=reasons.invalid_data)

    author = (db.get_user_by_login(session, post.author)).one()

    if token.login == author.login:
        mark = (db.get_mark_for_post(session, postId, token.login)).one_or_none()

        if mark is None:
            db.post_create_mark(session, Marks(post_id=postId, login=token.login, liked=False))
            db.increment_dislike(session, postId)
            post = (db.get_post_by_id(session, postId)).one()
            return Post(id=post.id, content=post.content, author=post.author,
                        tags=post.tags, createdAt=post.createdAt, likesCount=post.likesCount,
                        dislikesCount=post.dislikesCount)
        elif not mark.liked:
            return Post(id=post.id, content=post.content, author=post.author,
                        tags=post.tags, createdAt=post.createdAt, likesCount=post.likesCount,
                        dislikesCount=post.dislikesCount)
        else:
            db.change_mark(session, postId, token.login)
            db.increment_dislike(session, postId)
            db.decrement_like(session, postId)
            post = (db.get_post_by_id(session, postId)).one()
            return Post(id=post.id, content=post.content, author=post.author,
                        tags=post.tags, createdAt=post.createdAt, likesCount=post.likesCount,
                        dislikesCount=post.dislikesCount)

    if not author.isPublic:
        array_friends = (db.get_friends_by_login(session, author.login)).all()
        if any(friend.friend == token.login for friend in array_friends):
            mark = (db.get_mark_for_post(session, postId, token.login)).one_or_none()

            if mark is None:
                db.post_create_mark(session, Marks(post_id=postId, login=token.login, liked=False))
                db.increment_dislike(session, postId)
                post = (db.get_post_by_id(session, postId)).one()
                return Post(id=post.id, content=post.content, author=post.author,
                            tags=post.tags, createdAt=post.createdAt, likesCount=post.likesCount,
                            dislikesCount=post.dislikesCount)
            elif not mark.liked:
                return Post(id=post.id, content=post.content, author=post.author,
                            tags=post.tags, createdAt=post.createdAt, likesCount=post.likesCount,
                            dislikesCount=post.dislikesCount)
            else:
                db.change_mark(session, postId, token.login)
                db.increment_dislike(session, postId)
                db.decrement_like(session, postId)
                post = (db.get_post_by_id(session, postId)).one()
                return Post(id=post.id, content=post.content, author=post.author,
                            tags=post.tags, createdAt=post.createdAt, likesCount=post.likesCount,
                            dislikesCount=post.dislikesCount)
        else:
            response.status_code = status.HTTP_404_NOT_FOUND
            return ErrorResponse(reason=reasons.invalid_data)

    mark = (db.get_mark_for_post(session, postId, token.login)).one_or_none()

    if mark is None:
        db.post_create_mark(session, Marks(post_id=postId, login=token.login, liked=False))
        db.increment_dislike(session, postId)
        post = (db.get_post_by_id(session, postId)).one()
        return Post(id=post.id, content=post.content, author=post.author,
                    tags=post.tags, createdAt=post.createdAt, likesCount=post.likesCount,
                    dislikesCount=post.dislikesCount)
    elif not mark.liked:
        return Post(id=post.id, content=post.content, author=post.author,
                    tags=post.tags, createdAt=post.createdAt, likesCount=post.likesCount,
                    dislikesCount=post.dislikesCount)
    else:
        db.change_mark(session, postId, token.login)
        db.increment_dislike(session, postId)
        db.decrement_like(session, postId)
        post = (db.get_post_by_id(session, postId)).one()
        return Post(id=post.id, content=post.content, author=post.author,
                    tags=post.tags, createdAt=post.createdAt, likesCount=post.likesCount,
                    dislikesCount=post.dislikesCount)


@api.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"reason": reasons.invalid_data}
    )


if __name__ == "__main__":
    create_db()
    for router in routers:
        api.include_router(router)
    uvicorn.run(api, host="0.0.0.0", port=settings.SERVER_PORT)
