FROM python:3.11-slim-bookworm 

ENV PYTHONUNBUFFERED 1 \
  PYTHONDONTWRITEBYTECODE 1

ENV PORT=8000 \
  NUM_WORKERS=3 \
  TIMEOUT=300
    
# install system dependencies
RUN --mount=type=cache,target=/var/cache/apt \
  apt-get update && apt-get -y upgrade
  
RUN --mount=type=cache,target=/var/cache/apt \
  apt-get install -y \
  build-essential \
  postgresql-client-common postgresql-client \
  gettext libpq-dev \
  libmaxminddb0 libmaxminddb-dev mmdb-bin
  
RUN apt-get clean && apt-get autoremove -y && rm -rf /var/cache/apt


# setup workdir
RUN mkdir /app
WORKDIR /app

# install python dependencies
ENV POETRY_NO_INTERACTION=1 \
  POETRY_VIRTUALENVS_IN_PROJECT=0 \
  POETRY_VIRTUALENVS_CREATE=0 \
  POETRY_CACHE_DIR=/tmp/poetry_cache

# use poetry ton install packges
#################################
# install poetry
RUN pip install poetry
COPY ./pyproject.toml /app/pyproject.toml
RUN --mount=type=cache,target=/tmp/poetry_cache poetry install --with dev --no-root
#RUN poetry install --without dev --no-root && rm -rf $POETRY_CACHE_DIR
#RUN poetry install --with dev --no-root && rm -rf $POETRY_CACHE_DIR

# # use pip
#################################
# RUN poetry export -f requirements.txt -o requirements.txt --without-hashes
# #COPY ./requirements.txt /app/requirements.txt
# RUN pip install --no-cache-dir --upgrade -r requirements.txt


# copy files and create dirs 
COPY . /app
RUN mkdir -p /app/media && mkdir -p /app/static 


# build frontend css
#RUN npm install && npm run build

# MULTISTAGE  BUILD copy from builder
# FROM python:3.11-slim-bookworm as runtime
#
# ENV VIRTUAL_ENV=/app/.venv \
#    PATH="/app/.venv/bin:$PATH"
# COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

# create docker entrypoint
ADD docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod a+x /docker-entrypoint.sh
ENTRYPOINT ["/docker-entrypoint.sh"]

# # download geoip date
# RUN mkdir -p libs/geoip && cd libs/geoip \
#   && curl -o GeoLite2-City.mmdb  https://git.io/GeoLite2-City.mmdb \
#   && curl -o GeoLite2-Country.mmdb https://git.io/GeoLite2-Country.mmdb 

# add django user
RUN addgroup --system --gid 1000 django \
    && adduser --system --uid 1000 --ingroup django django 
RUN chown -R django:django /app
USER django

# Collect our static media.
# https://stackoverflow.com/questions/59719175/where-to-run-collectstatic-when-deploying-django-app-to-heroku-using-docker
# RUN DEBUG=False python /app/manage.py collectstatic --noinput --settings=turtlenest.settings
RUN python /app/manage.py collectstatic --noinput


CMD exec gunicorn  --bind 0.0.0.0:$PORT \
    --timeout $TIMEOUT \
    --workers $NUM_WORKERS \
    --access-logfile - \
    turtlenest.wsgi:application
