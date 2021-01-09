#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from datetime import *
from models import db,Venue,Artist,Show

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# TODO: connect to a local postgresql database -- done

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

#----------------------------------------------------------------------------#
#  Venues
#----------------------------------------------------------------------------#

@app.route('/venues')
def venues():
    # TODO: replace with real venues data.
    #       num_shows should be aggregated based on number of upcoming shows per venue.

    # this will return all the distinct city and states
    areas = Venue.query.distinct(Venue.city, Venue.state)
    data = []  # empty data list to assign the data to it
    for x in areas:  # for each area , create a dict which have city and state and list of venues
        uniqueArea = {
            "city": x.city,
            "state": x.state,
            "venues": []
        }
        # here we assign the venues to uniqueArea Dict
        venues = Venue.query.filter_by(city=x.city, state=x.state)
        for y in venues:
            uniqueArea["venues"].append({
                "id": y.id,
                "name": y.name
            })
        data.append(uniqueArea)

    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # search for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    search_term = request.form.get('search_term', '')
    data = Venue.query.filter(Venue.name.ilike('%'+search_term+'%'))
    count = data.count()
    response = {
        "count": count,
        "data": data,
        "num_upcoming_shows": Venue.query.filter_by(id=data.id).join(Show, Show.venue_id == Venue.id).filter(Show.start_time > currentTime).count()
    }
    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
   # shows the venue page with the given venue_id
    # TODO: replace with real venue data from the venues table, using venue_id
    venue = Venue.query.filter_by(id=venue_id).first()
    shows = Show.query.filter_by(venue_id=venue_id).all()

    data = {
        "id": venue.id,
        "name": venue.name,
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "image_link": venue.image_link,
        "facebook_link": venue.facebook_link,
        "genres": venue.genres.replace('{', ' ').replace('}', ' ').split(','),
        "seeking_description": venue.seeking_description,
        "website": venue.website,
        "past_shows": [],
        "upcoming_shows": [],
        "past_shows_count": 0,
        "upcoming_shows_count": 0,
    }

    past_shows_count = 0
    upcoming_shows_count = 0

    for show in shows:
        if show.start_time < str(datetime.now()):
            artist_info = Artist.query.filter_by(id=show.artist_id).first()
            data['past_shows'].append({
                "artist_id": artist_info.id,
                "artist_name": artist_info.name,
                "artist_image_link": artist_info.image_link,
                "start_time": format_datetime(str(show.start_time))
            })
            past_shows_count += 1
            data['past_shows_count'] = past_shows_count

    for show in shows:
        if show.start_time > str(datetime.now()):
            artist_info = Artist.query.filter_by(id=show.artist_id).first()
            data['upcoming_shows'].append({
                "artist_id": artist_info.id,
                "artist_name": artist_info.name,
                "artist_image_link": artist_info.image_link,
                "start_time": format_datetime(str(show.start_time))
            })
            upcoming_shows_count += 1
            data['upcoming_shows_count'] = upcoming_shows_count
    return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)

    # -- done -- #


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    address = request.form['address']
    phone = request.form['phone']
    genres = request.form.getlist('genres')
    image_link = request.form['image_link']
    facebook_link = request.form['facebook_link']
    try:

        venue = Venue(name=name, city=city, state=state, address=address,
                      phone=phone, genres=genres, image_link=image_link, facebook_link=facebook_link)
        db.session.add(venue)
        db.session.commit()

        # on successful db insert, flash success
        flash('Venue ' + request.form['name'] + 'was successfully listed!')
    except:
        # TODO: on unsuccessful db insert, flash an error instead.
        # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
        # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
        flash('An error occurred. Venue ' +
              request.form['name'] + ' could not be listed.')
        db.session.rollback()
    finally:
        db.session.close()
    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    # TODO: Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
    try:
        venue = Venue.query.filter_by(id=venue_id)
        db.session.remove(venue)
        db.session.commit()

    except:
        flash('An error occured when deleting a venue ' +
              venue.name + 'could not be deleted')
        db.session.rollback()
    finally:
        db.session.close()

    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    return render_template('pages/home.html')

#  Artists
#  ----------------------------------------------------------------

@app.route('/artists')
def artists():
    # TODO: replace with real data returned from querying the database -- done
    return render_template('pages/artists.html', artists=Artist.query.all())


@app.route('/artists/search', methods=['POST'])
def search_artists():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    search_term = request.form.get('search_term', '')
    data = Artist.query.filter(Artist.name.ilike('%'+search_term+'%'))
    count = data.count()
    response = {
        "count": count,
        "data": data
    }
    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

    # -- done -- #


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the venue page with the given venue_id
    # TODO: replace with real venue data from the venues table, using venue_id -- done
    artist = Artist.query.filter_by(id=artist_id).first()
    shows = Show.query.filter_by(artist_id=artist_id).all()
    data = {
        "id": artist.id,
        "name": artist.name,
        "genres": artist.genres.replace('{', ' ').replace('}', ' ').split(','),
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website": artist.website,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link,
        "past_shows": [],
        "upcoming_shows": [],
        "past_shows_count": 0,
        "upcoming_shows_count": 0,
    }
    past_shows_count = 0
    upcoming_shows_count = 0

    for show in shows:
        if show.start_time < str(datetime.now()):
            venue_info = Venue.query.filter_by(id=show.venue_id).first()
            data['past_shows'].append({
                "venue_id": venue_info.id,
                "venue_name": venue_info.name,
                "venue_image_link": venue_info.image_link,
                "start_time": format_datetime(str(show.start_time))
            })
            past_shows_count += 1
            data['past_shows_count'] = past_shows_count

    for show in shows:
        if show.start_time > str(datetime.now()):
            venue_info = Venue.query.filter_by(id=show.venue_id).first()
            data['upcoming_shows'].append({
                "venue_id": venue_info.id,
                "venue_name": venue_info.name,
                "venue_image_link": venue_info.image_link,
                "start_time": format_datetime(str(show.start_time))
            })
            upcoming_shows_count += 1
            data['upcoming_shows_count'] = upcoming_shows_count
    return render_template('pages/show_artist.html', artist=data)


#  Update
#  ----------------------------------------------------------------


@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    data = Artist.query.filter_by(id=artist_id)
    return render_template('forms/edit_artist.html', form=form, artist=data)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    try:
        artist = Artist.query.filter_by(id=artist_id).first()
        artist.name = request.form['name']
        artist.city = request.form['city']
        artist.state = request.form['state']
        artist.phone = request.form['phone']
        artist.genres = request.form.getlist('genres')
        artist.facebook_link = request.form['facebook_link']
        db.session.commit()
        flash('Arist' + request.form['name'] + ' was succefully edited !')
    except:
        db.session.rollback()
        flash('Arist' + request.form['name'] + ' Couldn\'t be edited')
    finally:
        db.session.close()
    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    # TODO: populate form with values from venue with ID <venue_id>
    data = Venue.query.filter_by(id=venue_id).first()
    return render_template('forms/edit_venue.html', form=form, venue=data)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    try:
        venue = Venue.query.filter_by(id=venue_id)
        venue.name = request.form['name']
        venue.city = request.form['city']
        venue.state = request.form['state']
        venue.phone = request.form['phone']
        venue.genres = request.form.getlist('genres')
        venue.facebook_link = request.form['facebook_link']
        db.session.commit()
        flash('Venue ' + request.form['name'] + ' was successfully edited!')
    except:
        db.session.rollback()
        flash('An error occurred. Artist ' +
              request.form['name'] + ' could not be edited.')
    finally:
        db.session.close()
    return redirect(url_for('show_venue', venue_id=venue_id))

#  ----------------------------------------------------------------
#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # called upon submitting the new artist listing form
    # TODO: insert form data as a new Artist record in the db, instead
    # TODO: modify data to be the data object returned from db insertion
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    phone = request.form['phone']
    genres = request.form.getlist('genres')
    image_link = request.form['image_link']
    facebook_link = request.form['facebook_link']
    try:
        artist = Artist(name=name, city=city, state=state, phone=phone,
                        genres=genres, image_link=image_link, facebook_link=facebook_link)
        db.session.add(artist)
        db.session.commit()
        # on successful db insert, flash success
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
    except Exception as e:
        print(e)
        # TODO: on unsuccessful db insert, flash an error instead.
        # e.g., flash('An error occurred. artist ' + data.name + ' could not be listed.')
        db.session.rollback()
        flash('An error occurred. artist ' +
              artist.name + ' could not be listed.')
    finally:
        db.session.close()
    return render_template('pages/home.html')

#  ----------------------------------------------------------------
#  Shows
#  ----------------------------------------------------------------


@app.route('/shows')
def shows():
    # displays list of shows at /shows
    # TODO: replace with real venues data.
    #       num_shows should be aggregated based on number of upcoming shows per venue.
    shows = Show.query.all()
    data = []
    for show in shows:
        venue = Venue.query.filter_by(id=show.venue_id).first()
        artist = Artist.query.filter_by(id=show.artist_id).first()
        data.append({
            "venue_id": show.venue_id,
            "venue_name": venue.name,
            "artist_id": artist.id,
            "artist_name": artist.name,
            "artist_image_link": artist.image_link,
            "start_time": show.start_time
        })
    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    # TODO: insert form data as a new Show record in the db, instead
    try:
        # from form
        artist_id = request.form['artist_id']
        venue_id = request.form['venue_id']
        start_time = request.form['start_time']
        # create a new show
        show = Show()
        show.venue_id = venue_id
        show.artist_id = artist_id
        show.start_time = start_time
        # add show to db
        db.session.add(show)
        db.session.commit()
        flash('Show was successfully listed!')
    # exception handler
    except:
        db.session.rollback()
        flash('An error occurred. Show could not be listed.')
    # close session
    finally:
        db.session.close()

    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Show could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    return render_template('pages/home.html')


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
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
