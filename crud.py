from sqlalchemy.orm import Session
from sqlalchemy import select
from validators import get_hash
from models import *
from schemas import *


class CRUD:
    def get_countries(self, session: Session):
        sql_query = select(Countries).order_by(Countries.alpha2)
        result = session.execute(sql_query)

        return result.scalars()

    def get_country_by_alpha2(self, session: Session, alpha2: str):
        sql_query = select(Countries).filter(Countries.alpha2 == alpha2)
        result = session.execute(sql_query)

        return result.scalars()

    def get_users(self, session: Session):
        sql_query = select(Users).order_by(Users.id)
        result = session.execute(sql_query)

        return result.scalars()

    def get_user_by_login(self, session: Session, login: str):
        sql_query = select(Users).filter(Users.login == login)
        result = session.execute(sql_query)

        return result.scalars()

    def get_user_by_phone(self, session: Session, phone: str):
        sql_query = select(Users).filter(Users.phone == phone)
        result = session.execute(sql_query)

        return result.scalars()

    def get_user_by_email(self, session: Session, email: str):
        sql_query = select(Users).filter(Users.email == email)
        result = session.execute(sql_query)

        return result.scalars()

    def get_token_by_token(self, session: Session, token: str):
        sql_query = select(Tokens).filter(Tokens.token == token)
        result = session.execute(sql_query)

        return result.scalars()

    def get_friends_by_login(self, session: Session, login: str):
        sql_query = select(Friends).filter(Friends.login == login)
        result = session.execute(sql_query)

        return result.scalars()

    def get_friend_by_login(self, session: Session, login: str, friend: str):
        sql_query = select(Friends).filter(Friends.login.like(login), Friends.friend.like(friend))
        result = session.execute(sql_query)

        return result.scalars()

    def get_post_by_id(self, session: Session, postId: str):
        sql_query = select(Posts).filter(Posts.id == postId)
        result = session.execute(sql_query)

        return result.scalars()

    def get_posts_by_login(self, session: Session, login: str):
        sql_query = select(Posts).filter(Posts.author == login)
        result = session.execute(sql_query)

        return result.scalars()

    def get_mark_for_post(self, session: Session, postId: str, login: str):
        sql_query = select(Marks).filter(Marks.post_id.like(postId), Marks.login.like(login))
        result = session.execute(sql_query)

        return result.scalars()

    def update_user_by_login(self, session: Session, login: str,
                             user_data: UpdateProfile):
        sql_query = select(Users).filter(Users.login == login)
        result = session.execute(sql_query)
        user = result.scalars().one()

        if user_data.countryCode is not None:
            user.countryCode = user_data.countryCode
        if user_data.isPublic is not None:
            user.isPublic = user_data.isPublic
        if user_data.image is not None:
            user.image = user_data.image
        if user.image == "":
            user.image = None
        if user_data.phone is not None:
            user.phone = user_data.phone
        if user.phone == "":
            user.phone = None
        session.commit()

    def update_password_by_login(self, session: Session, login: str,
                                 newPassword: str):
        sql_query = select(Users).filter(Users.login == login)
        result = session.execute(sql_query)
        user = result.scalars().one()
        user.password = get_hash(newPassword)
        session.commit()

    def increment_like(self, session: Session, postId: str):
        sql_query = select(Posts).filter(Posts.id == postId)
        result = session.execute(sql_query)
        post = result.scalars().one()
        post.likesCount += 1
        session.commit()

    def decrement_like(self, session: Session, postId: str):
        sql_query = select(Posts).filter(Posts.id == postId)
        result = session.execute(sql_query)
        post = result.scalars().one()
        post.likesCount -= 1
        session.commit()

    def increment_dislike(self, session: Session, postId: str):
        sql_query = select(Posts).filter(Posts.id == postId)
        result = session.execute(sql_query)
        post = result.scalars().one()
        post.dislikesCount += 1
        session.commit()

    def decrement_dislike(self, session: Session, postId: str):
        sql_query = select(Posts).filter(Posts.id == postId)
        result = session.execute(sql_query)
        post = result.scalars().one()
        post.dislikesCount -= 1
        session.commit()

    def change_mark(self, session: Session, postId: str, login: str):
        sql_query = select(Marks).filter(Marks.post_id.like(postId), Marks.login.like(login))
        result = session.execute(sql_query)
        mark = result.scalars().one()
        mark.liked = not mark.liked
        session.commit()

    def post_create_user(self, session: Session, user_data: Users):
        session.add(user_data)
        session.commit()

    def post_create_token(self, session: Session, token_data: Tokens):
        session.add(token_data)
        session.commit()

    def post_create_friend(self, session: Session, friend_data: Friends):
        session.add(friend_data)
        session.commit()

    def post_create_post(self, session: Session, post_data: Posts):
        session.add(post_data)
        session.commit()

    def post_create_mark(self, session: Session, mark_data: Marks):
        session.add(mark_data)
        session.commit()

    def delete_token(self, session: Session, token_data: Tokens):
        session.delete(token_data)
        session.commit()

    def delete_tokens_by_login(self, session: Session, login: str):
        sql_query = select(Tokens).filter(Tokens.login == login)
        result = session.execute(sql_query)
        tokens = result.scalars().all()
        for token in tokens:
            session.delete(token)
        session.commit()

    def delete_friend(self, session: Session, friend_data: Friends):
        session.delete(friend_data)
        session.commit()
