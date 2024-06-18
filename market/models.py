from market import db, login_manager
from market import bcrypt
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer(), primary_key=True)
    username = db.Column(db.String(length=30), nullable=False, unique=True)
    email_address = db.Column(db.String(length=50), nullable=False, unique=True)
    password_hash = db.Column(db.String(length=60), nullable=False)
    budget = db.Column(db.Integer(), nullable=False, default=1000)
    items = db.relationship('Item', backref='owned_user', lazy=True)
    favorites = db.relationship('Favorite', backref='user', lazy=True)

    @property
    def prettier_budget(self):
        if len(str(self.budget)) >= 4:
            return f'{str(self.budget)[:-3]},{str(self.budget)[-3:]}$'
        else:
            return f"{self.budget}$"

    @property
    def password(self):
        return self.password

    @password.setter
    def password(self, plain_text_password):
        self.password_hash = bcrypt.generate_password_hash(plain_text_password).decode('utf-8')

    def check_password_correction(self, attempted_password):
        return bcrypt.check_password_hash(self.password_hash, attempted_password)

    def can_purchase(self, item_obj):
        return self.budget >= item_obj.price

    def can_sell(self, item_obj):
        return item_obj in self.items


class Item(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(length=30), nullable=False, unique=True)
    price = db.Column(db.Integer(), nullable=False)
    barcode = db.Column(db.String(length=12), nullable=False, unique=True)
    description = db.Column(db.String(length=1024), nullable=False, unique=True)
    image_filename = db.Column(db.String(length=100), nullable=True)
    owner = db.Column(db.Integer(), db.ForeignKey('user.id'))
    category = db.Column(db.String(length=50), nullable=False, default='general')
    subcategory = db.Column(db.String(length=50), nullable=False, default='general')

    def __repr__(self):
        return f'Item {self.name}'


    def buy(self, user):
        self.owner = user.id
        user.budget -= self.price
        db.session.commit()

    def sell(self, user):
        self.owner = None
        user.budget += self.price
        db.session.commit()


class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    product_name = db.Column(db.String(100), nullable=False)
    product_description = db.Column(db.String(1000), nullable=True)
    product_photo = db.Column(db.String(100), nullable=True)

    def __init__(self, user_id, product_id, product_name, product_description, product_photo):
        self.user_id = user_id
        self.product_id = product_id
        self.product_name = product_name
        self.product_description = product_description
        self.product_photo = product_photo

    def __repr__(self):
        return f"<Favorite {self.product_name}>"


class ShoppingCartItem(db.Model):
    __tablename__ = 'shopping_cart_item'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    size = db.Column(db.String(10), nullable=False)

    user = db.relationship('User', backref='shopping_cart_items')
    item = db.relationship('Item', backref='shopping_cart_items')

    def __repr__(self):
        return f'<ShoppingCartItem {self.item.name} - {self.size}>'


class NewsletterSubscriber(db.Model):
    __tablename__ = 'newsletter_subscribers'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)

    def __repr__(self):
        return f'<NewsletterSubscriber {self.email}>'

