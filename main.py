from wtforms import StringField, EmailField, PasswordField, SubmitField
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from flask import Flask, render_template, url_for, request, redirect, flash
from wtforms.validators import DataRequired, Length
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap5
from flask_wtf import FlaskForm
from sqlalchemy import String, Integer
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user
from datetime import datetime as dt

# TODO Change db's to relational to support multiple users
# TODO: For Adding, editing and deleting, make a function that checks a result exists to deal with None and Uniques
# TODO: Implement generative passwords
# TODO Add greeting message to home page when you log in
# TODO Change add h1 to edit when approaching from the edit button
# TODO Style up the h1s for login and register and anywhere else actually... like add maybe
# TODO Check validation docs to see if passwords or emails should have more specific validators
# TODO: Let the user click a website which auto fills the login form for them or auto logs them in, either or.


class Base(DeclarativeBase):
    pass


# Initializations
db = SQLAlchemy(model_class=Base)
app = Flask(__name__)
bootstrap = Bootstrap5(app)
login_manager = LoginManager()

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///manager.db"
app.config["SECRET_KEY"] = "qwerty"
db.init_app(app)
login_manager.init_app(app)


# --------------------------------Database Tables----------------------------
class Users(UserMixin, db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True, nullable=False)
    password: Mapped[str] = mapped_column(nullable=False)


class Passwords(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    website: Mapped[str] = mapped_column(unique=True, nullable=False)
    email: Mapped[str] = mapped_column(nullable=False)
    password: Mapped[str] = mapped_column(nullable=False)


# -------------------------------Flask Forms---------------------------------
class RegisterForm(FlaskForm):
    email = StringField(name="email", validators=[DataRequired(), Length(max=40)])
    password = PasswordField(name="password", validators=[DataRequired(), Length(max=40)])
    confirm_password = PasswordField(name="confirm_password", validators=[DataRequired(), Length(max=40)])
    submit = SubmitField(name="submit", validators=[DataRequired()])


class LoginForm(FlaskForm):
    email = StringField(name="email", validators=[DataRequired(), Length(max=40)])
    password = PasswordField(name="password", validators=[DataRequired(), Length(max=40)])
    submit = SubmitField(name="submit", validators=[DataRequired()])


# The form to add a website, email and password
class EntryForm(FlaskForm):
    website = StringField(name="website", validators=[DataRequired(), Length(max=40)])
    email = EmailField(name="email", validators=[DataRequired(), Length(max=40)])
    password = PasswordField(name="password", validators=[DataRequired(), Length(max=40)])
    confirm_password = PasswordField(name="confirm_password", validators=[DataRequired(), Length(max=40)])
    submit = SubmitField(name="submit", validators=[DataRequired()])


with app.app_context():
    db.create_all()


# context_processor can inject values into templates before rending them, perfect for putting the date in the footer
@app.context_processor
def set_date():
    return {"current_year": dt.now().strftime("%Y")}


@app.route("/")
def home():
    return render_template("index.html")


# TODO: Handled error of strings entered being too big to display for the css with code for now
@app.route("/manage_passwords")
@login_required
def manage_passwords():
    passwords = db.session.scalars(db.select(Passwords).order_by(Passwords.website)).all()
    return render_template("user.html", passwords=passwords)


@app.route('/add', methods=["GET", "POST"])
@login_required
def add():
    form = EntryForm()
    if form.validate_on_submit():

        # TODO: Replace with verifying function, same for edit and delete
        check_website = [item.website for item in db.session.scalars((db.select(Passwords))).all()]
        if request.form.get('website') in check_website:
            flash("Password for website already exists")
            return render_template("add.html", form=form)
        elif form.password.data != form.confirm_password.data:
            flash("Passwords did not match")
            return render_template("add.html", form=form)

        new_entry = Passwords(website=request.form.get('website'),
                              email=request.form.get('email'),
                              password=request.form.get('password'),
                              )
        db.session.add(new_entry)
        db.session.commit()
        return render_template("add.html", message="Successfully Added Password", form=form)
    return render_template("add.html", form=form)


# TODO: This can collapse into the "add" route instead by passing the id and having and "if id:" statement in add.
@app.route("/edit", methods=["GET", "POST"])
@login_required
def edit():
    # Checks ids in database to see if requested password to edit exists, to protect against manually enter id in url
    check_id = [str(item.id) for item in db.session.scalars((db.select(Passwords))).all()]
    if request.args.get('id') in check_id:
        entry = db.session.scalar((db.select(Passwords).where(Passwords.id == request.args.get('id'))))
        form = EntryForm(
            website=entry.website,
            email=entry.email,
            password=entry.password
        )
        if form.validate_on_submit():
            website_check = db.session.scalar((db.select(Passwords).where(Passwords.website == form.website.data)))
            if website_check is not None:
                flash(f"You already have a password saved for {form.website.data}")
                return render_template("add.html", form=form)
            elif form.password.data != form.confirm_password.data:
                flash(f"Passwords did not match")
                return render_template("add.html", form=form)
            entry.website = form.website.data
            entry.email = form.email.data
            entry.password = form.password.data
            db.session.commit()
            return redirect(url_for('manage_passwords'))
        return render_template("add.html", form=form)
    return redirect(url_for("add"))


@app.route("/delete")
@login_required
def delete():
    check_id = [str(item.id) for item in db.session.scalars((db.select(Passwords))).all()]
    if request.args.get('id') in check_id:
        db.session.delete(db.session.scalar((db.select(Passwords).where(Passwords.id == request.args.get('id')))))
        db.session.commit()
        return redirect(url_for("manage_passwords"))
    return redirect(url_for("manage_passwords"))


@login_manager.user_loader
def load_user(user_id):
    """Handles User authentication for the session"""
    return db.session.scalar(db.select(Users).where(Users.id == user_id))


@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    # Registers a user
    if form.validate_on_submit():
        if db.session.scalar(db.select(Users).where(Users.email == form.email.data)) is not None:
            flash("Email is already registered")
            return redirect(url_for("login"))
        elif form.password.data != form.confirm_password.data:
            flash(f"Passwords did not match")
            return redirect(url_for("register"))
        else:
            new_user = Users(email=form.email.data, password=form.password.data)
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for("home"))

    return render_template("register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = db.session.scalar(db.select(Users).where(Users.email == form.email.data))
        if user is None:
            flash("There is no user registered with this email address")
            return redirect(url_for("register"))
        elif user.password != form.password.data:
            flash("Incorrect Password")
            return redirect(url_for("login"))
        else:
            # TODO Consider redirecting elsewhere, like passwords or add password
            login_user(user)
            return redirect(url_for("home"))
    return render_template("login.html", form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)
