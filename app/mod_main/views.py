# app/mod_main/views.py

from flask import render_template, Blueprint, request, flash, redirect, url_for

from app.mod_main.forms import SignUpForm
from app import db
from app.models import Email
import mixpanel
from mixpanel import Mixpanel
import uuid


# initiate mixpanel
mp = Mixpanel("insert mixpanel project key here")


main_blueprint = Blueprint('main', __name__,)
privacy_blueprint = Blueprint('privacy', __name__,)
promo_blueprint = Blueprint('promo', __name__,)


@main_blueprint.route('/', methods=['GET', 'POST'])
def index():
    """Landing page for users to enter emails."""
    form = SignUpForm(request.form)
    if form.validate_on_submit():
        emailFound = Email.query.filter_by(email=form.email.data).first()
        if emailFound:
            flash('Sorry that email aleady exists!', 'danger')
        else:
            if request.form['btn'] == 'planSignUp':
                entry = Email(email=form.email.data, price_plan=request.form['plans'], source="Price plan signups")
                db.session.add(entry)
                db.session.commit()

                mp.track(str(uuid.uuid1()), 'Price plan SignUp')

                flash('Thank you for your interest! w\'ll be in touch shortly', 'success')
                return redirect(url_for('main.index'))
            elif request.form['btn'] == 'reg_signUp':
                entry = Email(email=form.email.data, price_plan=None, source="Regular signup")
                db.session.add(entry)
                db.session.commit()

                mp.track(str(uuid.uuid1()), 'Regular SignUp')

                flash('Thank you for your interest! w\'ll be in touch shortly', 'success')
                return redirect(url_for('main.index'))

    return render_template('main/index.html', form=form)




@promo_blueprint.route('/promotion_page', methods=['GET', 'POST'])
def promo():
    # """Closed launch promo."""
    form = SignUpForm(request.form)
    if form.validate_on_submit():
        emailFound = Email.query.filter_by(email=form.email.data).first()
        if emailFound:
            flash('Sorry that email aleady exists!', 'danger')
        else:
            if request.form['btn'] == 'planSignUp':
                print("closed lunch promo")
                entry = Email(email=form.email.data, price_plan=request.form['plans'], source="Price plan signup - closed lunch-Promo")
                db.session.add(entry)
                db.session.commit()

                mp.track(str(uuid.uuid1()), 'Price plan signup - closed lunch-Promo')

                flash('Thank you for your interest! w\'ll be in touch shortly', 'success')
                return redirect(url_for('main.index'))

            elif request.form['btn'] == 'reg_signUp':
                entry = Email(email=form.email.data, price_plan=None, source="Regular signup - closed lunch-Promo")
                db.session.add(entry)
                db.session.commit()

                mp.track(str(uuid.uuid1()), 'Regular SignUp - closed lunch-Promo')

                flash('Thank you for your interest! w\'ll be in touch shortly', 'success')
                return redirect(url_for('main.index'))

    return render_template('main/promo.html', form=form)



@privacy_blueprint.route('/privacy', methods=['GET', 'POST'])
def privacy():
    return render_template('main/privacy.html')