# TurtleNest

v3 Cloud and sharing platform for [Turtlestitch](https://www.turtlestitch.org)

Rewritten from scratch with a backend in [Django](https://www.djangoproject.com/) and some [tailwind](https://tailwindcss.com) and [htmx](https://htmx.org/) on the frontend side.

Currently, supports both the legacy [TurtleCloud](https://github.com/backface/turtleCloud)/[BeetleCloud](https://github.com/bromagosa/beetleCloud) API and the new [Snap!](https://snap.berkeley.edu)/[SnapCloud](https://github.com/snap-cloud/snapCloud) API

### How to get started?

    cp env.SAMPLE .env

make sure those settings fit you.
Link or copy docker-compose.dev.yml to docker-compose.override.yml in case you want to run a local web proxy server (caddy) or if need changes for your local system best put it there. then run:

    docker compose up

You also need to create an admin/superuser if you are not importing/migrating from an existing database (as we do):

	docker compose exec django python manage.py createsuperuser

Finally go to: [http://localhost:8000](http://localhost:8000)
