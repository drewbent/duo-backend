<div align="center">
    <p align="center">
        <a href="https://www.youtube.com/watch?v=HqCNxhVDSgs" title="Duo — 1-on-1 peer learning for Khan Academy">
            <img src="https://i.imgur.com/LkUGAuD.png" alt="Logo" width="150px" />
        </a>
        <h1>Duo Backend</h1>
    </p>
</div>

<p align="center">1-on-1 peer learning for Khan Academy.</p>

<div align="center">
    <p align="center">
        <a href="https://www.youtube.com/watch?v=HqCNxhVDSgs" title="Duo — 1-on-1 peer learning for Khan Academy">
            <img src="https://i.imgur.com/z03nnf8.png" alt="Duo screenshot" style="max-width: 800px; width: 100%" />
        </a>
    </p>
</div>

## Overview

Backend and API for the Duo project. Built with Flask and SQL, and used by both the Chrome extension and admin dashboard.

## What is the Duo project?

1-on-1 peer learning for Khan Academy.

Duo is a Chrome extension for students in the Khan Lab School or Oxford Day Academy PeerX classes to engage in peer learning. It is not intended for widespread public use and is not currently being maintained, although you are welcome to draw inspiration or adapt from it. It is licensed under the terms of the MIT license.

The project was created by Drew Bent and Phil Shen in 2020.

### Links
- [Video overview](https://www.youtube.com/watch?v=HqCNxhVDSgs)
- [Chrome extension used in KLS and ODA classes](http://bit.ly/chromeduo)

### Repositories
- [Chrome extension](https://github.com/drewbent/duo)
- [Backend and API](https://github.com/drewbent/duo-backend)
- [Admin dashboard](https://github.com/drewbent/duo-admin)

## Set Up

To install requirements:
1. `pip install -r api/requirements.txt`

To create the database locally:
1. `createdb mastery`
3. `python manage.py db migrate`
4. `python manage.py db upgrade`
5. `brew services start postgresql`
6. `sudo -u postgres createuser --superuser {username}`

To view/edit the local database:
1. `psql -U {username} -d mastery`

To run the app locally:
1. `python app.py`

To deploy the API to Heroku:
1. `git subtree push --prefix api heroku master`