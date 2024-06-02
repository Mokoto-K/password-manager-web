from wtforms import StringField, EmailField, PasswordField, SubmitField
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from flask import Flask, render_template, url_for, request
from wtforms.validators import DataRequired
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap5
from flask_wtf import FlaskForm
# from sqlalchemy import String, Integer

class Base(DeclarativeBase):
    pass

# Initializations
db = SQLAlchemy(model_class=Base)
app = Flask(__name__)
bootstrap = Bootstrap5(app)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///manager.db"
app.config["SECRET_KEY"] = "qwerty"
db.init_app(app)


# TODO: Don't forget to handle the case of having two accounts for one website, it will cause unique error
class Passwords(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    website: Mapped[str] = mapped_column(unique=True, nullable=False)
    email: Mapped[str] = mapped_column(nullable=False)
    password: Mapped[str] = mapped_column(nullable=False)


# TODO: Implement generative passwords
# The form to add a website, email and password
class EntryForm(FlaskForm):
    website = StringField(name="website", validators=[DataRequired()])
    email = EmailField(name="email", validators=[DataRequired()])
    password = PasswordField(name="password", validators=[DataRequired()])
    submit = SubmitField(name="submit", validators=[DataRequired()])


with app.app_context():
    db.create_all()


@app.route("/")
def home():

    return render_template("index.html", )


@app.route('/add', methods=["GET", "POST"])
def add():
    form = EntryForm()
    if form.validate_on_submit():
        new_entry = Passwords(website= request.form.get('website'),
                              email= request.form.get('email'),
                              password = request.form.get('password'),
                              )
        db.session.add(new_entry)
        db.session.commit()
        return render_template("add.html", message="Successfully Added Password", form=form)
    return render_template("add.html", form=form)


if __name__ == "__main__":
    app.run(debug=True)

# TODO: Let the user click a website which auto fills the login form for them or auto logs them in, either or.
