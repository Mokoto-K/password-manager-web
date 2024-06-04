from wtforms import StringField, EmailField, PasswordField, SubmitField
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from flask import Flask, render_template, url_for, request, redirect, flash
from wtforms.validators import DataRequired, Length
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap5
from flask_wtf import FlaskForm
# from sqlalchemy import String, Integer

# TODO: Add confirm password on add and edit screen
# TODO: Sort the passwords on the user page alphabetically
class Base(DeclarativeBase):
    pass

# Initializations
db = SQLAlchemy(model_class=Base)
app = Flask(__name__)
bootstrap = Bootstrap5(app)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///manager.db"
app.config["SECRET_KEY"] = "qwerty"
db.init_app(app)


# TODO: Change the schema of the db and the form to have a confirm password field
# TODO: Don't forget to handle the case of having two accounts for one website, it will cause unique error
class Passwords(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    website: Mapped[str] = mapped_column(unique=True, nullable=False)
    email: Mapped[str] = mapped_column(nullable=False)
    password: Mapped[str] = mapped_column(nullable=False)


# TODO: Implement generative passwords
# The form to add a website, email and password
# TODO: Handled error of strings entered being too big to display for the css with code for now
class EntryForm(FlaskForm):
    website = StringField(name="website", validators=[DataRequired(), Length(max=40)])
    email = EmailField(name="email", validators=[DataRequired(), Length(max=40)])
    password = PasswordField(name="password", validators=[DataRequired(), Length(max=40)])
    submit = SubmitField(name="submit", validators=[DataRequired()])


with app.app_context():
    db.create_all()


@app.route("/")
def home():
    return render_template("index.html", )

@app.route("/manage_passwords")
def manage_passwords():
    passwords = db.session.scalars(db.select(Passwords)).all()
    return render_template("user.html", passwords=passwords)


# TODO: ADD a check to make sure the user isnt adding the same website twice, is unqiue will catch and crash
@app.route('/add', methods=["GET", "POST"])
def add():
    form = EntryForm()
    # TODO: stop someone from entering the same website
    if form.validate_on_submit():

        # TODO: Replace with verifying function, same for edit and delete
        check_website = [item.website for item in db.session.scalars((db.select(Passwords))).all()]
        if request.form.get('website') in check_website:
            flash("Password for website already exists")
            return render_template("add.html", form=form)

        new_entry = Passwords(website= request.form.get('website'),
                              email= request.form.get('email'),
                              password = request.form.get('password'),
                              )
        db.session.add(new_entry)
        db.session.commit()
        return render_template("add.html", message="Successfully Added Password", form=form)
    return render_template("add.html", form=form)


# TODO: This can collapse into the "add" route instead by passing the id and having and "if id:" statement in add.
@app.route("/edit", methods=["GET", "POST"])
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
            entry.website = form.website.data
            entry.email = form.email.data
            entry.password = form.password.data
            db.session.commit()
            return redirect(url_for('manage_passwords'))
        return render_template("add.html", form=form)
    return redirect(url_for("add"))

# TODO: For editing too, make a function that checks a result exists, so we can centrally deal with failed requests
@app.route("/delete")
def delete():
    check_id = [str(item.id) for item in db.session.scalars((db.select(Passwords))).all()]
    if request.args.get('id') in check_id:
        db.session.delete(db.session.scalar((db.select(Passwords).where(Passwords.id == request.args.get('id')))))
        db.session.commit()
        return redirect(url_for("manage_passwords"))
    return redirect(url_for("manage_passwords"))

if __name__ == "__main__":
    app.run(debug=True)

# TODO: Let the user click a website which auto fills the login form for them or auto logs them in, either or.
