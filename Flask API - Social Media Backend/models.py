from app import db, app, login_manager
import sqlalchemy_utils
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy_utils import EmailType, PasswordType
from flask_user import UserManager

# Schema for Users table
class Users(db.Model,UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(EmailType, nullable=False, unique=True)
    password = db.Column(PasswordType(
        schemes=[
            'pbkdf2_sha512',
            'md5_crypt'
        ],
        deprecated=['md5_crypt']
    ))
    username = db.Column(db.String(200), nullable=False)
    roles = db.relationship('Role', secondary='user_roles')
    lists = db.relationship('Lists', secondary='list_roles')
    def as_dict(self):
       return {c.name: str(getattr(self, c.name)) for c in self.__table__.columns}

# Defining user roles
class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), unique=True)

#    def __init__(self, name):
#        self.name = name

# User Roles - assosiation table
class UserRoles(db.Model):
    __tablename__ = 'user_roles'
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey(
        'users.id', ondelete='CASCADE'))
    role_id = db.Column(db.Integer(), db.ForeignKey(
        'roles.id', ondelete='CASCADE'))    
    def as_dict(self):
        return {c.name: str(getattr(self, c.name)) for c in self.__table__.columns}

# Schema for Lists
class Lists(db.Model):
    __tablename__ = "lists"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)
    cards = db.relationship('Cards', backref='lists', lazy=True)
    def as_dict(self):
        return {c.name: str(getattr(self, c.name)) for c in self.__table__.columns}

# Schema for List Roles
class ListRoles(db.Model):
    __tablename__ = 'list_roles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id'))
    lists_id = db.Column(db.Integer(), db.ForeignKey('lists.id'))
    def as_dict(self):
        return {c.name: str(getattr(self, c.name)) for c in self.__table__.columns}

# Schema for Cards
class Cards(db.Model):
    __tablename__ = "cards"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    description = db.Column(db.String(250))
    lists_id = db.Column(db.Integer, db.ForeignKey('lists.id'), nullable=False)
    comments = db.relationship('Comments', backref='cards', lazy=True)
    def as_dict(self):
        return {c.name: str(getattr(self, c.name)) for c in self.__table__.columns}

# Schema for Comments
class Comments(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    cards_id = db.Column(db.Integer, db.ForeignKey('cards.id'), nullable=False)
    content = db.Column(db.String(250))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    replies = db.relationship('Replies', backref='comments', lazy=True)
    def as_dict(self):
        return {c.name: str(getattr(self, c.name)) for c in self.__table__.columns}

# Schema for Replies
class Replies(db.Model):
    __tablename__ = "replies"
    id = db.Column(db.Integer, primary_key=True)
    replies = db.Column(db.String(250))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    comment_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=False)
    def as_dict(self):
        return {c.name: str(getattr(self, c.name)) for c in self.__table__.columns}

@login_manager.user_loader
def load_user(id):
    print(Users.query.get(int(id)).id)
    return (Users.query.get(int(id)))
