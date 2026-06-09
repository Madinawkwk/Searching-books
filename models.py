import random
from typing import List

from flask import Flask
from faker import Faker
from datetime import datetime
from sqlalchemy import select, ForeignKey, DateTime, func
from sqlalchemy.orm import mapped_column, Mapped, relationship
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from extenstions import db

favorites = db.Table(
    'favorites',
    db.Column('user_id', ForeignKey('users.id'), primary_key=True),
    db.Column('book_id', ForeignKey('books.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    username: Mapped[str] = mapped_column(db.String(80), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(db.String(120), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(db.String(256), nullable=True)
    oauth_provider: Mapped[List[str]] = mapped_column(db.String(20), nullable=True)
    oauth_id: Mapped[List[str]] = mapped_column(db.String(100), nullable=True, unique=True)

    profile: Mapped[List["Profile"]] = relationship(back_populates="user", uselist=False)
    posts: Mapped[List["Post"]] = relationship(back_populates="user", lazy='dynamic')
    reviews: Mapped[List["Review"]] = relationship(back_populates="user", lazy='dynamic')
    favorite_books: Mapped[List["Book"]] = relationship(
        secondary=favorites,
        back_populates="fans",
        lazy='select'
    )

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class Profile(db.Model):
    __tablename__ = 'profiles'
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), unique=True, nullable=False)
    bio: Mapped[List[str]] = mapped_column(db.Text, default='')
    avatar_url: Mapped[List[str]] = mapped_column(db.String(256), default='')

    user: Mapped["User"] = relationship(back_populates="profile", uselist=False)


class Book(db.Model):
    __tablename__ = 'books'
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    olid: Mapped[str] = mapped_column(db.String(20), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(db.String(256), nullable=False)
    authors: Mapped[str] = mapped_column(db.String(256), default='Неизвестен')
    cover_url: Mapped[List[str]] = mapped_column(db.String(256), nullable=True)
    publish_year: Mapped[List[str]] = mapped_column(db.String(20), nullable=True)

    reviews: Mapped[List["Review"]] = relationship(back_populates="book", lazy='dynamic')
    fans: Mapped[List["User"]] = relationship(
        secondary=favorites,
        back_populates="favorite_books",
        lazy='dynamic'
    )


class Review(db.Model):
    __tablename__ = 'reviews'
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    book_id: Mapped[int] = mapped_column(ForeignKey('books.id'), nullable=False)
    text: Mapped[str] = mapped_column(db.Text, nullable=False)
    rating: Mapped[int] = mapped_column(db.Integer, default=5)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="reviews")
    book: Mapped["Book"] = relationship(back_populates="reviews")


class Post(db.Model):
    __tablename__ = 'posts'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    title: Mapped[str] = mapped_column(db.String(200), nullable=False)
    content: Mapped[str] = mapped_column(db.Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="posts")


def fill_db(app:Flask):
    fake = Faker()

    with app.app_context():
        users = []
        for _ in range(10):
            user = User(
                username=fake.unique.user_name(),
                email=fake.unique.email()
            )
            user.set_password('1234')
            db.session.add(user)
            user.profile = Profile(
                bio=fake.text(max_nb_chars=200),
            )
            db.session.add(user.profile)
            users.append(user)
        db.session.commit()

        books = []
        for _ in range(20):
            book = Book(
                olid=f'OL{fake.unique.random_number(digits=7)}M',
                title=fake.sentence(nb_words=4),
                authors=fake.name(),
                cover_url=None,
                publish_year=random.randint(1950, 2026)
            )
            db.session.add(book)
            books.append(book)
        db.session.commit()

        for user in users:
            num_posts = random.randint(0, 10)
            for _ in range(num_posts):
                post = Post(
                    title=fake.sentence(nb_words=6),
                    content=fake.text(max_nb_chars=300),
                    user=user
                )
                db.session.add(post)
        db.session.commit()

        for user in users:
            num_favorites = random.randint(0, 5)
            if num_favorites > 0:
                selected_books = random.sample(books, min(num_favorites, len(books)))
                user.favorite_books.extend(selected_books)
        db.session.commit()

        for book in books:
            num_reviews = random.randint(0, 5)
            for _ in range(num_reviews):
                reviewer = random.choice(users)
                review = Review(
                    user=reviewer,
                    book=book,
                    text=fake.paragraph(nb_sentences=3),
                    rating=random.randint(1, 5)
                )
                db.session.add(review)
        db.session.commit()

def create_db(app: Flask):
	with app.app_context():
		db.create_all()
