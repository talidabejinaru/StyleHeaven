from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from collections import defaultdict
from . import app, db
from .models import Item, User, Favorite, ShoppingCartItem
from .forms import RegisterForm, LoginForm, PurchaseItemForm, SellItemForm

@app.route('/')
@app.route('/home')
def home_page():
    return render_template('home.html')

@app.route('/market', methods=['GET', 'POST'])
@login_required
def market_page():
    purchase_form = PurchaseItemForm()
    selling_form = SellItemForm()
    if request.method == "POST":
        # Purchase Item Logic
        purchased_item = request.form.get('purchased_item')
        p_item_object = Item.query.filter_by(name=purchased_item).first()
        if p_item_object:
            if current_user.can_purchase(p_item_object):
                p_item_object.buy(current_user)
                flash(f"Congratulations! You purchased {p_item_object.name} for {p_item_object.price}$", category='success')
            else:
                flash(f"Unfortunately, you don't have enough money to purchase {p_item_object.name}!", category='danger')
        # Sell Item Logic
        sold_item = request.form.get('sold_item')
        s_item_object = Item.query.filter_by(name=sold_item).first()
        if s_item_object:
            if current_user.can_sell(s_item_object):
                s_item_object.sell(current_user)
                flash(f"Congratulations! You sold {s_item_object.name} back to market!", category='success')
            else:
                flash(f"Something went wrong with selling {s_item_object.name}", category='danger')

        return redirect(url_for('market_page'))

    if request.method == "GET":
        items = Item.query.filter_by(owner=None)
        owned_items = Item.query.filter_by(owner=current_user.id)
        return render_template('market.html', items=items, purchase_form=purchase_form, owned_items=owned_items, selling_form=selling_form)

# Add this new route for newsletter subscription
@app.route('/subscribe_newsletter', methods=['POST'])
def subscribe_newsletter():
    email = request.form.get('email')
    if email:
        new_subscriber = NewsletterSubscriber(email=email)
        db.session.add(new_subscriber)
        db.session.commit()
        flash('You have successfully subscribed to the newsletter!', 'success')
    else:
        flash('Please enter a valid email address.', 'danger')
    return redirect(url_for('home_page'))

@app.route('/register', methods=['GET', 'POST'])
def register_page():
    form = RegisterForm()
    if form.validate_on_submit():
        user_to_create = User(username=form.username.data,
                              email_address=form.email_address.data,
                              password=form.password1.data)
        db.session.add(user_to_create)
        db.session.commit()
        login_user(user_to_create)
        flash(f"Account created successfully! You are now logged in as {user_to_create.username}", category='success')
        return redirect(url_for('home_page'))
    if form.errors != {}:  # If there are errors from the validations
        for err_msg in form.errors.values():
            flash(f'There was an error with creating a user: {err_msg}', category='danger')

    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    form = LoginForm()
    if form.validate_on_submit():
        attempted_user = User.query.filter_by(username=form.username.data).first()
        if attempted_user and attempted_user.check_password_correction(
                attempted_password=form.password.data
        ):
            login_user(attempted_user)
            flash(f'Success! You are logged in as: {attempted_user.username}', category='success')
            return redirect(url_for('home_page'))
        else:
            flash('Username and password do not match! Please try again', category='danger')

    return render_template('login.html', form=form)

@app.route('/logout')
def logout_page():
    logout_user()
    flash("You have been logged out!", category='info')
    return redirect(url_for("home_page"))

@app.route('/women')
@login_required
def women_page():
    items = Item.query.filter_by(category='women').all()
    items_by_subcategory = defaultdict(list)
    for item in items:
        items_by_subcategory[item.subcategory].append(item)
    favorite_item_ids = [fav.product_id for fav in current_user.favorites]
    return render_template('women.html', items_by_subcategory=items_by_subcategory, favorite_item_ids=favorite_item_ids)

@app.route('/men')
@login_required
def men_page():
    items = Item.query.filter_by(category='men').all()
    items_by_subcategory = defaultdict(list)
    for item in items:
        items_by_subcategory[item.subcategory].append(item)
    favorite_item_ids = [fav.product_id for fav in current_user.favorites]
    return render_template('men.html', items_by_subcategory=items_by_subcategory, favorite_item_ids=favorite_item_ids)

@app.route('/kids')
@login_required
def kids_page():
    items = Item.query.filter_by(category='kids').all()
    items_by_subcategory = defaultdict(list)
    for item in items:
        items_by_subcategory[item.subcategory].append(item)
    favorite_item_ids = [fav.product_id for fav in current_user.favorites]
    return render_template('kids.html', items_by_subcategory=items_by_subcategory, favorite_item_ids=favorite_item_ids)

@app.route('/subcategory/<category>/<subcategory>')
@login_required
def subcategory_page(category, subcategory):
    items = Item.query.filter_by(category=category, subcategory=subcategory).all()
    favorite_item_ids = [fav.product_id for fav in current_user.favorites]
    return render_template('subcategory.html', items=items, category=category, subcategory=subcategory, favorite_item_ids=favorite_item_ids)

@app.route('/add_to_favorites/<int:product_id>', methods=['POST'])
@login_required
def add_to_favorites(product_id):
    # Verificăm dacă produsul este deja în favorite
    existing_favorite = Favorite.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if not existing_favorite:
        item = Item.query.get(product_id)
        if item:
            favorite = Favorite(
                user_id=current_user.id,
                product_id=item.id,
                product_name=item.name,
                product_description=item.description,
                product_photo=item.image_filename
            )
            db.session.add(favorite)
            db.session.commit()
            flash(f'Item added to favorites!', category='success')
        else:
            flash(f'Item does not exist!', category='danger')
    else:
        flash(f'Item is already in favorites!', category='info')
    return redirect(url_for('kids_page'))  # Redirecționăm utilizatorul înapoi la pagina anterioară

@app.route('/toggle_favorite', methods=['POST'])
@login_required
def toggle_favorite():
    item_id = request.form.get('item_id')
    item = Item.query.get(item_id)
    favorite = Favorite.query.filter_by(user_id=current_user.id, product_id=item_id).first()

    if favorite:
        db.session.delete(favorite)
        db.session.commit()
        flash('Item removed from favorites!', 'info')
    else:
        new_favorite = Favorite(
            user_id=current_user.id,
            product_id=item_id,
            product_name=item.name,
            product_description=item.description,
            product_photo=item.image_filename
        )
        db.session.add(new_favorite)
        db.session.commit()
        flash('Item added to favorites!', 'success')

    return redirect(request.referrer or url_for('home_page'))

@app.route('/favorite')
@login_required
def favorite_page():
    favorites = Favorite.query.filter_by(user_id=current_user.id).all()
    favorite_items = [Item.query.get(favorite.product_id) for favorite in favorites]
    return render_template('favorite.html', items=favorite_items)

@app.route('/shopping_cart')
@login_required
def shopping_cart_page():
    cart_items = ShoppingCartItem.query.filter_by(user_id=current_user.id).all()
    return render_template('shopping_cart.html', cart_items=cart_items)


@app.route('/add_to_cart', methods=['POST'])
@login_required
def add_to_cart():
    item_id = request.form.get('item_id')
    size = request.form.get('size')

    item = Item.query.get(item_id)
    if item:
        cart_item = ShoppingCartItem(
            user_id=current_user.id,
            item_id=item.id,
            size=size,
            price=item.price if item.price is not None else 0.0  # Ensure price is set here
        )
        db.session.add(cart_item)
        db.session.commit()
        flash('Product added to cart successfully!', 'success')
        return redirect(request.referrer or url_for('kids_page'))
    flash('Failed to add item to cart.', 'danger')
    return redirect(request.referrer or url_for('kids_page'))

@app.route('/remove_from_cart', methods=['POST'])
@login_required
def remove_from_cart():
    item_id = request.form.get('item_id')
    cart_item = ShoppingCartItem.query.get(item_id)
    if cart_item and cart_item.user_id == current_user.id:
        db.session.delete(cart_item)
        db.session.commit()
        flash('Item removed from cart', 'success')
    else:
        flash('Failed to remove item from cart', 'danger')
    return redirect(url_for('shopping_cart_page'))

@app.route('/order_details')
@login_required
def order_details():
    return render_template('order_details.html')

@app.route('/submit_order', methods=['POST'])
@login_required
def submit_order():
    # Process the form data if needed
    first_name = request.form['shippingFirstName']
    last_name = request.form['shippingLastName']
    phone = request.form['shippingPhone']
    address = request.form['shippingAddress']
    city = request.form['shippingCity']
    zip_code = request.form['shippingZip']
    card_number = request.form['cardNumber']
    card_expiry = request.form['cardExpiry']
    card_cvv = request.form['cardCVV']

    # Here you would process the order and save the information in the database

    # Clear the cart items for the current user
    ShoppingCartItem.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()

    # Flash success message
    flash('Your order has been successfully placed!', 'success')
    return redirect(url_for('home_page'))

if __name__ == '__main__':
    app.run(debug=True)
