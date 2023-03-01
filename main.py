import sqlalchemy
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os
import requests
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
import ast
import smtplib

app = Flask(__name__)
app.config['SECRET_KEY'] = 'om'
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///houses.db"
app.config['UPLOAD_FOLDER'] = "static/house_images"

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.jinja_env.globals.update(zip=zip)

email = "ghost.rentals.gupta@gmail.com"
password = "kpdlztnelhfchuzo"
connection = smtplib.SMTP('smtp.gmail.com')

with app.app_context():
    db = SQLAlchemy(app)


    class House(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        title = db.Column(db.String(250), unique=True, nullable=False)
        address = db.Column(db.String(250), nullable=False)
        description = db.Column(db.String(250), nullable=False)
        renter = db.Column(db.Integer, nullable=False)
        price = db.Column(db.Integer, nullable=False)
        type = db.Column(db.String(250), nullable=False)
        size = db.Column(db.Integer, nullable=False)
        owner = db.Column(db.String(250), nullable=False)
        mt_price = db.Column(db.Integer, nullable=False)
        bank = db.Column(db.Integer, nullable=False)
        user_owner = db.Column(db.Integer, nullable=False)

        # This will allow each book object to be identified by its title when printed.
        def __repr__(self):
            return f'<House {self.title}>'


    class Bank(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        title = db.Column(db.String(250), unique=True, nullable=False)
        upi = db.Column(db.String(250), unique=True, nullable=False)
        account = db.Column(db.String(250), nullable=False)
        ifsc = db.Column(db.String(250), nullable=False)
        type = db.Column(db.String(250), nullable=False)
        branch = db.Column(db.String(300), nullable=False)

        # This will allow each book object to be identified by its title when printed.
        def __repr__(self):
            return f'<Bank {self.title}>'


    class User(UserMixin, db.Model):
        id = db.Column(db.Integer, primary_key=True)
        title = db.Column(db.String(250), unique=True, nullable=False)
        email = db.Column(db.String(250), unique=True, nullable=False)
        username = db.Column(db.String(250), nullable=False)
        password = db.Column(db.String(250), nullable=False)
        properties = db.Column(db.String(250), unique=True, nullable=True)
        user_type = db.Column(db.String(250), nullable=True)

        def __repr__(self):
            return f'<Lessee {self.title}>'


    db.create_all()

    print(db.session.query(House).all())

    login_manager = LoginManager()
    login_manager.init_app(app)


    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))


    @app.route('/')
    def home():
        all_houses = db.session.query(House).all()
        all_houses.reverse()
        if current_user.is_authenticated and current_user.user_type == 'lessor':
            # all_houses = db.session.query(House, user_owner=current_user.id).all()
            all_houses = db.session.execute(db.select(House).filter_by(user_owner=current_user.id)).all()

            houses = [item for t in all_houses for item in t]
            print(all_houses)
            print(type(all_houses))
            print(houses)
            print(type(houses))
            houses.reverse()

            return render_template("index.html", houses=houses)
        elif current_user.is_authenticated and current_user.user_type == 'lessee':
            all_houses = db.session.query(House, user_owner=current_user.id).all()
            all_houses.reverse()
            return render_template("index.html", houses=all_houses)
        else:
            flash('Please login or register as a lessor to continue.')
            return render_template("error.html")




    @app.route('/add', methods=["GET", "POST"])
    def add():
        if request.method == "POST":
            new_house = House(
                title=request.form['title'],
                address=request.form['address'],
                description=request.form['description'],
                renter=0,
                price=request.form['price'],
                type=request.form['type'],
                size=request.form['size'],
                owner=request.form['owner'],
                mt_price=request.form['mt-price'],
                bank=request.form['bank'],
                user_owner=int(current_user.id)

            )
            db.session.add(new_house)
            db.session.commit()
            image = request.files['file']

            image.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(str(new_house.id))))

            # Redirects home.
            return redirect(url_for('home'))
        if current_user.is_authenticated and current_user.user_type == 'lessor':
            banks = db.session.query(Bank).all()

            return render_template("add.html", banks=banks)
        elif current_user.is_authenticated and current_user.user_type == 'lessee':
            flash('Lessee accounts are prohibited to add a new house.')
            return redirect(url_for('home'))
        else:
            flash('Please login or register as a lessor to continue.')
            return redirect(url_for('home'))


    @app.route('/add-bank', methods=["GET", "POST"])
    def add_bank():
        if request.method == "POST":
            try:
                response = requests.get(f"https://ifsc.razorpay.com/{request.form['ifsc']}").json()
                branch = response["BANK"] + ", " + response["BRANCH"]
            except:
                branch = "Bank not found."
            new_bank = Bank(
                title=request.form['title'],
                upi=request.form['upi'],
                account=request.form['account'],
                ifsc=request.form['ifsc'],
                type=request.form['type'],
                branch=branch

            )
            db.session.add(new_bank)
            db.session.commit()

            # Redirects home.
            return redirect(url_for('home'))
        if current_user.is_authenticated and current_user.user_type == 'lessor':
            return render_template("add_bank.html")
        elif current_user.is_authenticated and current_user.user_type == 'lessee':
            flash('Lessee accounts are prohibited to add a new house.')
            return redirect(url_for('home'))
        else:
            flash('Please login or register as a lessor to continue.')
            return redirect(url_for('home'))


    @app.route('/bank', methods=["GET", "POST"])
    def bank():
        bank_id = request.args.get('id')
        bank_selected = Bank.query.get(bank_id)

        return render_template("bank.html", bank=bank_selected, branch=bank_selected.branch)


    @app.route('/new-agreement', methods=["GET", "POST"])
    def agree():
        if request.method == "POST":
            house_id = request.form['house']

            pdf = request.files['file']
            place_to_save = f'static/agreements/{house_id}'
            try:
                pdf.save(os.path.join(place_to_save, secure_filename(request.form['time'] + '.pdf')))
            except:
                os.mkdir(os.path.join('static/agreements', str(house_id)))
                pdf.save(os.path.join(place_to_save, secure_filename(request.form['time'] + '.pdf')))

            # Redirects home.
            return redirect(url_for('home'))

        houses = db.session.query(House).all()

        return render_template("add_agreement.html", houses=houses)


    @app.route('/agreements', methods=["GET", "POST"])
    def agreements():
        house_id = request.args.get('id')
        house_selected = House.query.get(house_id)
        agreements = os.listdir(f'static/agreements/{house_id}')

        return render_template("agreements.html", agreements=agreements, id=house_id)


    @app.route('/register-lessor', methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            try:
                user = User(
                    title=request.form['title'],
                    properties="[]",
                    email=request.form['email'],
                    username=request.form['username'],
                    password=request.form['password'],
                    user_type='lessor'
                )
                db.session.add(user)
                db.session.commit()
                if not current_user.is_authenticated:
                    login_user(user)
                print(current_user.username)
                return redirect(url_for('home', username=request.form.get('title')))
            except sqlalchemy.exc.IntegrityError:
                flash('You already registered with that username, try logging in! Or else, that username is already '
                      'taken.')
                return redirect(url_for('register'))
        return render_template("register.html")


    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == "POST":
            login_username = request.form['username']
            login_password = request.form['password']

            found_user = User.query.filter_by(username=login_username).first()
            if found_user == None:
                flash('That username does not exist, please try again.')
                return redirect(url_for('login'))
            else:
                database_password = found_user.password
                if database_password == login_password:
                    login_user(found_user)
                    print(current_user.username)
                    return redirect(url_for('home'))
                else:
                    flash('Password invalid, try again please.')
                    return redirect(url_for('login'))

        return render_template("login.html", logged_in=current_user.is_authenticated)


    @app.route('/logout')
    def logout():
        logout_user()
        return redirect(url_for('home'))


    @app.route('/register-lessee', methods=["GET", "POST"])
    def register_lessee():
        if request.method == "POST":
            try:
                user = User(
                    title=request.form['title'],
                    properties=str(request.form['house']),
                    email=request.form['email'],
                    username=request.form['username'],
                    password='',
                    user_type='lessee'
                )
                db.session.add(user)
                db.session.commit()

                connection.starttls()
                connection.login(email, password)
                connection.sendmail(email, user.email,
                                    f'Subject:Set up your lessee account on GHOST Tenancy\n\n'
                                    f'Dear {user.title},\n'
                                    f'{current_user.title} has requested you to register as a lessee on GHOST Tenancy\n'
                                    f'Username: {user.username} | Property: {db.session.get(House, int(user.properties)).title}\n'
                                    f'To continue, please open the following link:\n'
                                    f'{request.root_url}{url_for("lessee_setup")}\n'
                                    f'\n Thank you and have a wonderful day ahead!\n'
                                    f'GHOST - tenancy made simple')

                return redirect(url_for('home'))
            except sqlalchemy.exc.IntegrityError:
                flash('Lessee already registered with that username, try logging in! Or else, that username is already '
                      'taken.')
                return redirect(url_for('register_lessee'))
        if current_user.is_authenticated and current_user.user_type == 'lessor':
            all_properties = House.query.filter_by(user_owner=current_user.id, renter="0").all()
            return render_template("register_lessee.html", houses=all_properties)
        elif current_user.is_authenticated and current_user.user_type == 'lessee':
            flash('Lessee accounts are prohibited to add a new lessee.')
            return redirect(url_for('home'))
        else:
            flash('Please login or register as a lessor to continue.')
            return redirect(url_for('home'))


    @app.route('/lessee-setup', methods=["GET", "POST"])
    def lessee_setup():
        if request.method == "POST":
                user = db.session.get(User, request.form['id'])
                user.password = request.form['password']
                db.session.commit()
                flash('Lessee setup completed. Login with your username and password.')

        lessee_id = request.args.get('id')
        lessee = db.session.get(User, int(lessee_id))
        return render_template("register_lessee.html", lessee=lessee)


    @app.route('/house', methods=["GET", "POST"])
    def house():
        house_id = request.args.get('id')
        house = db.session.get(House, int(house_id))
        owner = db.session.get(User, house.user_owner).title
        if house.renter == 0:
            renter = 'Standby'
        else:
            renter = db.session.get(User, house.renter).title
        try:
            agreements = os.listdir(f'static/agreements/{house_id}')
        except:
            agreements = 'No agreements found.'
        return render_template("house.html", house=house, owner=owner, renter=renter, agreements=agreements, id=house_id)

if __name__ == "__main__":
    app.run(debug=True)
