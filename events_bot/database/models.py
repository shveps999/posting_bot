from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Table, Text, func, BigInteger
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.ext.declarative import declarative_base
from typing import List, Optional
from datetime import datetime

Base = declarative_base()

# Ассоциативная таблица для связи многие-ко-многим между пользователями и категориями
user_categories = Table(
    'user_categories',
    Base.metadata,
    Column('user_id', BigInteger, ForeignKey('users.id'), primary_key=True),
    Column('category_id', Integer, ForeignKey('categories.id'), primary_key=True)
)

# Ассоциативная таблица для связи многие-ко-многим между постами и категориями
post_categories = Table(
    'post_categories',
    Base.metadata,
    Column('post_id', Integer, ForeignKey('posts.id'), primary_key=True),
    Column('category_id', Integer, ForeignKey('categories.id'), primary_key=True)
)

class TimestampMixin:
    """Миксин для автоматических временных меток"""
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

class User(AsyncAttrs, TimestampMixin, Base):
    """Модель пользователя"""
    __tablename__ = 'users'
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # Основной город (для совместимости)
    cities: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Новое поле для списка городов
    
    # Связи
    posts: Mapped[List["Post"]] = relationship("Post", back_populates="author")
    likes: Mapped[List["Like"]] = relationship("Like", back_populates="user")
    categories: Mapped[List["Category"]] = relationship(
        "Category",
        secondary=user_categories,
        back_populates="users"
    )

class Category(AsyncAttrs, TimestampMixin, Base):
    """Модель категории"""
    __tablename__ = 'categories'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Связи
    posts: Mapped[List["Post"]] = relationship(
        "Post",
        secondary=post_categories,
        back_populates="categories"
    )
    users: Mapped[List["User"]] = relationship(
        "User",
        secondary=user_categories,
        back_populates="categories"
    )

class Post(AsyncAttrs, TimestampMixin, Base):
    """Модель поста"""
    __tablename__ = 'posts'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    author_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.id'))
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    image_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # Основной город (для совместимости)
    cities: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Новое поле для списка городов
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    event_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Связи
    author: Mapped["User"] = relationship("User", back_populates="posts")
    categories: Mapped[List["Category"]] = relationship(
        "Category",
        secondary=post_categories,
        back_populates="posts"
    )
    likes: Mapped[List["Like"]] = relationship("Like", back_populates="post")
    moderation_records: Mapped[List["ModerationRecord"]] = relationship("ModerationRecord", back_populates="post")

class Like(AsyncAttrs, TimestampMixin, Base):
    """Модель лайка"""
    __tablename__ = 'likes'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.id'))
    post_id: Mapped[int] = mapped_column(Integer, ForeignKey('posts.id'))
    
    # Связи
    user: Mapped["User"] = relationship("User", back_populates="likes")
    post: Mapped["Post"] = relationship("Post", back_populates="likes")

class ModerationAction:
    """Перечисление действий модерации"""
    APPROVE = 1
    REJECT = 2
    REQUEST_CHANGES = 3

class ModerationRecord(AsyncAttrs, TimestampMixin, Base):
    """Модель записи модерации"""
    __tablename__ = 'moderation_records'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    post_id: Mapped[int] = mapped_column(Integer, ForeignKey('posts.id'))
    moderator_id: Mapped[int] = mapped_column(BigInteger)
    action: Mapped[int] = mapped_column(Integer)
    comment: Mapped[Optional[str]] = mapped_column(Text)
    
    # Связи
    post: Mapped["Post"] = relationship("Post", back_populates="moderation_records")
