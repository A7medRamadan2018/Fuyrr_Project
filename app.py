#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import random
import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from sqlalchemy import func, TIMESTAMP
from datetime import datetime
import re
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)
# : connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#
# Artist-Venue : many To Many
show = db.Table('show',
                db.Column('artist_id', db.Integer, db.ForeignKey(
                    'Artist.id', ondelete="CASCADE"), primary_key=True),
                db.Column('venue_id', db.Integer, db.ForeignKey(
                    'Venue.id', ondelete="CASCADE"), primary_key=True),
                db.Column('start_time', db.DateTime, nullable=False)
                )

# Venue Table


class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(12), nullable=False, unique=True)
    facebook_link = db.Column(db.String(1000), nullable=False, unique=True)
    image_link = db.Column(db.String(1000), nullable=False, unique=True)
    website = db.Column(db.String(1000), nullable=False, unique=True)
    seeking_talent = db.Column(db.Boolean, nullable=False)
    seeking_description = db.Column(db.String(120), nullable=True)
    # relation
    genres_venue = db.relationship(
        'Genres_Venue', backref=db.backref('genres_vn', lazy=True), cascade="all, delete")

# Genres with multi-valued associated with venue table


class Genres_Venue(db.Model):
    __tablename__ = 'genres_venue'
    venue_id = db.Column(db.Integer, db.ForeignKey(
        'Venue.id', ondelete="CASCADE"),  primary_key=True)
    genres = db.Column(db.String(500), primary_key=True)

# Artist Table


class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(12), nullable=False, unique=True)
    facebook_link = db.Column(db.String(1000), nullable=True, unique=True)
    image_link = db.Column(db.String(1000), nullable=False, unique=True)
    website = db.Column(db.String(1000), nullable=True, unique=True)
    seeking_talent = db.Column(db.Boolean, nullable=False)
    seeking_description = db.Column(db.String(120), nullable=True)

    genres_artist = db.relationship(
        'Genres_Artist', backref=db.backref('genres_art', lazy=True), cascade="all, delete")
    venues = db.relationship('Venue', secondary=show,
                             backref=db.backref('Artist', lazy=True), cascade="all, delete")

# Genres with multi-valued associated with artist table


class Genres_Artist(db.Model):
    __tablename__ = 'genres_artist'
    artist_id = db.Column(db.Integer, db.ForeignKey(
        'Artist.id', ondelete="CASCADE"), primary_key=True)
    genres = db.Column(db.String(500), primary_key=True)


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#


def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format)


app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#


@app.route('/')
def index():
    return render_template('pages/home.html')

#  Venuesdel
#  ----------------------------------------------------------------


@app.route('/venues')
def venues():
    # : replace with real venues data.
    # num_shows should be aggregated based on number of upcoming shows per venue.
    result = db.session.query(Venue.city, Venue.state, func.count(
        Venue.city)).group_by(Venue.city, Venue.state).all()
    data = []
    for r in result:
        venues = Venue.query.filter_by(city=r.city).all()
        data.append({
            'city': r.city,
            'state': r.state,
            'venues':
            [
                {"id": r.id,
                 "name": r.name,
                 'num_upcoming_show': len(db.session.query(show).filter(show.c.venue_id == r.id, show.c.start_time > datetime.now()).all())
                 } for r in venues
            ]
        })
    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    # : implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"

    result = Venue.query.filter(Venue.name.like("%"+request.form.get('search_term')+"%")).all()
    response = {
        "count": len(result),
        "data": [
            {"id": r.id,
             "name": r.name,
             'num_upcoming_shows': len(db.session.query(show).filter(show.c.venue_id == r.id, show.c.start_time > datetime.now()).all())
             } for r in result
        ]
    }
    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    # replace with real venue data from the venues table, using venue_id
    venue = Venue.query.filter_by(id=venue_id).first()
    genres = db.session.query(Genres_Venue).filter(Genres_Venue.venue_id == venue_id).all()

    all_past_shows = db.session.query(Artist, Venue, show).filter(show.c.start_time < datetime.now(), Venue.id == venue_id, Venue.id == show.c.venue_id, Artist.id == show.c.artist_id).all()

    all_upcoming_shows = db.session.query(Artist, Venue, show).filter(show.c.start_time > datetime.now(
    ), Venue.id == venue_id, Venue.id == show.c.venue_id, Artist.id == show.c.artist_id).all()

    data = {
        'id': venue.id,
        'name': venue.name,
        'genres': [gen.genres for gen in genres],
        'address': venue.address,
        'city': venue.city,
        'phone': venue.phone,
        'state': venue.state,
        'website': venue.website,
        'facebook_link': venue.facebook_link,
        'seeking_talent': venue.seeking_talent,
        'seeking_description': venue.seeking_description,
        'image_link': venue.image_link,
        'past_shows':
        [
            {
                "artist_id": ar[0].id,
                "artist_name": ar[0].name,
                "artist_image_link": ar[0].image_link,
                "start_time": format_datetime(str(ar[3]))
            } for ar in all_past_shows
        ],
        'upcoming_shows':
        [
            {
                "artist_id": ar[0].id,
                "artist_name": ar[0].name,
                "artist_image_link": ar[0].image_link,
                "start_time": format_datetime(str(ar[3]))
            } for ar in all_upcoming_shows
        ],
        "past_shows_count": len(all_past_shows),
        "upcoming_shows_count": len(all_upcoming_shows),
    }

    data = list(filter(lambda d: d['id'] == venue_id, [data]))[0]
    return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

def validation(field_for_valid, index):
    if index == 1:
        regex = re.compile(r'^(\d{3}-\d{3}-\d{4})')
    elif index == 2:
        reg = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
        regex = re.compile(reg)
    return bool(regex.match(field_for_valid))


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    # : insert form data as a new Venue record in the db, instead
    # : modify data to be the data object returned from db insertion

    error = False
    venue = Venue()
    venue.name = request.form.get('name')
    c_name = bool(venue.name)
    venue.city = request.form.get('city')
    c_city = bool(venue.city)
    venue.state = request.form.get('state')
    c_state = bool(venue.state)
    venue.phone = request.form.get('phone')
    c_phone = bool(venue.phone)
    venue.address = request.form.get('address')
    c_address = bool(venue.address)
    venue.genres = request.form.getlist('genres')
    c_genres = False if len(venue.genres) == 0 else True
    venue.facebook_link = request.form.get('facebook_link')
    c_facebook_link = bool(venue.facebook_link)
    venue.image_link = request.form.get('image_link')
    c_image_link = bool(venue.image_link)
    venue.website = request.form.get('website')
    c_website = bool(venue.website)
    value = request.form.get('seeking_talent')
    if value is not None:
        venue.seeking_talent = True
        venue.seeking_description = request.form.get('seeking_description')
    else:
        venue.seeking_talent = False

    # perform Validation for missing fields and valid phone, websites
    if not validation(venue.phone, 1):
        flash('phone Number is Wrong', 'danger')
        error = True

    if not validation(venue.website, 2):
        flash('website is Wrong', 'danger')
        error = True

    if not validation(venue.facebook_link, 2):
        flash('facebook link is Wrong', 'danger')
        error = True

    if not validation(venue.image_link, 2):
        flash('image link is Wrong', 'danger')
        error = True

    if c_name and c_address and c_city and c_genres and c_phone and c_state \
            and c_website and c_image_link and c_facebook_link and not error:
        db.session.add(venue)
        db.session.commit()
        for g in venue.genres:
            genres_vens = Genres_Venue()
            genres_vens.venue_id = venue.id
            genres_vens.genres = g
            db.session.add(genres_vens)
        db.session.commit()
        # on successful db insert, flash success
        flash('Venue ' + request.form['name'] +
              ' was successfully listed!', 'success')

    if not c_name or not c_address or not c_city or not c_genres or not c_phone or not c_state \
            or not c_website or not c_image_link or not c_facebook_link:
        error = True
        flash('Please insert All Fields', 'danger')

    if error:
        db.session.rollback()
        return redirect(request.referrer)
    else:
        return render_template('pages/home.html')



@app.route('/venues/<venue_id>', methods =['DELETE'])
def delete_venue(venue_id):
    # : Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
    try:
        Venue.query.filter_by(id=venue_id).delete()
        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()
    return redirect(request.referrer)

    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage

#  Artists
#  ----------------------------------------------------------------


@app.route('/artists')
def artists():
    # : replace with real data returned from querying the database
    result = Artist.query.all()
    data = [
        {"id": r.id,
         "name": r.name}
        for r in result
    ]
    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    # : implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    result = Artist.query.filter(Artist.name.like(
        "%"+request.form.get('search_term')+"%")).all()
    response = {
        "count": len(result),
        "data": [
            {"id": r.id,
             "name": r.name
             } for r in result
        ]
    }
    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the venue page with the given venue_id
    # : replace with real venue data from the venues table, using venue_id

    artist = Artist.query.filter_by(id=artist_id).first()
    genres = db.session.query(Genres_Artist).filter(
        Genres_Artist.artist_id == artist_id).all()
    all_past_shows = db.session.query(Venue, show).filter(
        show.c.start_time < datetime.now(), Venue.id == show.c.venue_id).all()
    all_upcoming_shows = db.session.query(Venue, show).filter(
        show.c.start_time > datetime.now(), Venue.id == show.c.venue_id).all()

    data = {
        'id': artist.id,
        'name': artist.name,
        'genres': [gen.genres for gen in genres],
        'city': artist.city,
        'phone': artist.phone,
        'state': artist.state,
        'website': artist.website,
        'facebook_link': artist.facebook_link,
        'seeking_talent': artist.seeking_talent,
        'seeking_description': artist.seeking_description,
        'image_link': artist.image_link,
        'past_shows':
        [
            {
                "venue_id": ar[0].id,
                "venue_name": ar[0].name,
                "venue_image_link": ar[0].image_link,
                "start_time": format_datetime(str(ar[3]))
            } for ar in all_past_shows
        ],
        'upcoming_shows':
        [
            {
                "venue_id": ar[0].id,
                "venue_name": ar[0].name,
                "venue_image_link": ar[0].image_link,
                "start_time": format_datetime(str(ar[3]))
            } for ar in all_upcoming_shows
        ],
        "past_shows_count": len(all_past_shows),
        "upcoming_shows_count": len(all_upcoming_shows),
    }

    data = list(filter(lambda d: d['id'] == artist_id, [data]))[0]
    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------


@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = db.session.query(Artist).get(artist_id)
    genres = db.session.query(Genres_Artist).filter(
        Genres_Artist.artist_id == artist_id).all()
    # : populate form with fields from artist with ID <artist_id>
    form.name.data = artist.name
    form.genres.data = [gen.genres for gen in genres]
    form.city.data = artist.city
    form.state.data = artist.state
    form.phone.data = artist.phone
    form.website.data = artist.website
    form.facebook_link.data = artist.facebook_link
    form.seeking_talent.data = artist.seeking_talent
    form.seeking_description.data = artist.seeking_description
    form.image_link.data = artist.image_link
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # : take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes
    artist = db.session.query(Artist).get(artist_id)
    artist.name = request.form.get('name')
    artist.city = request.form.get('city')
    artist.state = request.form.get('state')
    artist.phone = request.form.get('phone')
    artist.genres = request.form.getlist('genres')
    artist.facebook_link = request.form.get('facebook_link')
    artist.image_link = request.form.get('image_link')
    artist.website = request.form.get('website')
    value = request.form.get('seeking_talent')
    if value is not None:
        artist.seeking_description = request.form.get('seeking_description')
        artist.seeking_talent = True
    else:
        artist.seeking_talent = False
    db.session.commit()
    flash(artist.name + ' Successefully Updated', 'success')
    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = db.session.query(Venue).get(venue_id)
    genres = db.session.query(Genres_Venue).filter(
        Genres_Venue.venue_id == venue_id).all()
    # : populate form with fields from artist with ID <artist_id>
    form.name.data = venue.name
    form.genres.data = [gen.genres for gen in genres]
    form.city.data = venue.city
    form.address.data = venue.address
    form.state.data = venue.state
    form.phone.data = venue.phone
    form.website.data = venue.website
    form.facebook_link.data = venue.facebook_link
    form.seeking_talent.data = venue.seeking_talent
    form.seeking_description.data = venue.seeking_description
    form.image_link.data = venue.image_link
    # : populate form with values from venue with ID <venue_id>
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # : take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
    venue = db.session.query(Venue).get(venue_id)
    venue.name = request.form.get('name')
    venue.city = request.form.get('city')
    venue.state = request.form.get('state')
    venue.address = request.form.get('state')
    venue.phone = request.form.get('phone')
    venue.genres = request.form.getlist('genres')
    venue.facebook_link = request.form.get('facebook_link')
    venue.image_link = request.form.get('image_link')
    venue.website = request.form.get('website')
    value = request.form.get('seeking_talent')
    if value is not None:
        venue.seeking_description = request.form.get('seeking_description')
        venue.seeking_talent = True
    else:
        venue.seeking_talent = False
    db.session.commit()
    flash(venue.name + ' Successefully Updaed', 'success')
    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # called upon submitting the new artist listing form
    # : insert form data as a new Venue record in the db, instead
    # : modify data to be the data object returned from db insertion

    error = False
    artist = Artist()
    artist.name = request.form.get('name')
    artist.city = request.form.get('city')
    artist.state = request.form.get('state')
    artist.phone = request.form.get('phone')
    artist.genres = request.form.getlist('genres')
    c_genres = False if len(artist.genres) == 0 else True
    artist.facebook_link = request.form.get('facebook_link')
    artist.image_link = request.form.get('image_link')
    artist.website = request.form.get('website')
    value = request.form.get('seeking_talent')
    if value is not None:
        artist.seeking_talent = True
        artist.seeking_description = request.form.get('seeking_description')
    else:
        artist.seeking_talent = False

    # perform Validation for missing fields and valid phone, websites
    if not validation(artist.phone, 1):
        flash('Phone Number is Wrong', 'danger')
        error = True

    if not validation(artist.website, 2):
        flash('Website is Wrong', 'danger')
        error = True

    if not validation(artist.facebook_link, 2):
        flash('Facebook link is Wrong', 'danger')
        error = True

    if not validation(artist.image_link, 2):
        flash('Image link is Wrong', 'danger')
        error = True

    if bool(artist.name) and bool(artist.city) and bool(artist.state) and bool(artist.phone) and c_genres and bool(artist.facebook_link) \
            and bool(artist.image_link) and bool(artist.website) and not error:
        db.session.add(artist)
        db.session.commit()
        for g in artist.genres:
            genres_arts = Genres_Artist()
            genres_arts.artist_id = artist.id
            genres_arts.genres = g
            db.session.add(genres_arts)
        db.session.commit()
        # on successful db insert, flash success
        flash('Artist ' + request.form['name'] +
              ' was successfully listed!', 'success')

    if not bool(artist.name) and not bool(artist.city) and not bool(artist.state) and not bool(artist.phone) and not c_genres and not bool(artist.facebook_link) \
            and not bool(artist.image_link) and not bool(artist.website):
        error = True
        flash('Please insert All Fields', 'danger')

    if error:
        db.session.rollback()
        return redirect(request.referrer)
    else:
        return render_template('pages/home.html')

#  Shows
#  ----------------------------------------------------------------


@app.route('/shows')
def shows():
    # displays list of shows at /shows
    # : replace with real venues data.
    #       num_shows should be aggregated based on number of upcoming shows per venue.
    all_shows_artists = db.session.query(show, Artist, Venue).filter(
        show.c.artist_id == Artist.id, show.c.venue_id == Venue.id).all()
    data = [
        {
            "venue_id": show[4].id,
            "venue_name": show[4].name,
            "artist_id": show[3].id,
            "artist_name": show[3].name,
            "artist_image_link": show[3].image_link,
            "start_time": format_datetime(str(show[2]), format='full')
        } for show in all_shows_artists
    ]
    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    # : insert form data as a new Show record in the db, instead
    error = 0
    try:
        artist_id = request.form.get('artist_id')
        venue_id = request.form.get('venue_id')
        start_time = request.form.get('start_time')
        new_show = show.insert().values(artist_id=artist_id,venue_id=venue_id, start_time=start_time)
        db.session.execute(new_show)
        db.session.commit()
        flash('Show was successfully listed!')
    except:
        error = 1
        db.session.rollback()
        flash('Error Occured !', 'danger')

    if error == 0:
        return render_template('pages/home.html')
    else:
        return redirect(request.referrer)


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run(debug=True)

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
