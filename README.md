# TurtleNest

v3 Cloud and sharing platform for [Turtlestitch](https://www.turtlestitch.org)

Rewritten from scratch with a backend in [Django](https://www.djangoproject.com/) and some [tailwind](https://tailwindcss.com) and [htmx](https://htmx.org/) on the frontend side.

Currently, supports both the legacy [TurtleCloud](https://github.com/backface/turtleCloud)/[BeetleCloud](https://github.com/bromagosa/beetleCloud) API and the new [Snap!](https://snap.berkeley.edu)/[SnapCloud](https://github.com/snap-cloud/snapCloud) API

### How to get started?

    cp env.SAMPLE .env

make sure those values fit your system.

    docker compose up

You also need to create an admin/superuser if you are not importing/migrating from an existing database (as we do):

	docker compose exec django python manage.py createsuperuser

Finally go to: [http://localhost:8000](http://localhost:8000)


### Development

#### Backend

Link (or copy) docker-compose.dev.yml to docker-compose.override.yml 

    cp docker-compose.dev.yml docker-compose.override.yml

This will start Django's development server on port 8000 with hot reloading.
It also starts caddy as local proxy server on port 80 and with SSL on port 443. 
In some cases this is needed for testing. Feel free to adapt ports and other settings
the the docker-compose.override file - it is not tracked by git.

You can the standart Django management script like:

    docker compose exec django python manage.py 

If you don't like docker, you can run turtlenest with [uv](https://docs.astral.sh/uv/). 
Just make sure you configure a valid database in your environment or .env file, see env.SAMPLE. 
Install dependies:
   
    uv sync --frozen

run development server

    uv run manage.py runserver

or using a .env file:

    uv run --env-file .env manage.py runserver

#### Frontend


For styling in frontend development you need to run tailwind to watch and compile the stylesheets.
You need node and a node package manager. We use [pnpm](https://pnpm.io/)
On first use run:

	pnpm install

Then:

    pnpm run dev
    
