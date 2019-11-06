# XHominid Backend


Backend for an Android nutrition coaching and meal planning app

This flask-backend serves as the App website while handling backend requests from client app



## Components

### ...


## Secretes and keys

### ...


## QuickStart

### Install

1. Clone
1. Create and activate a virtualenv
1. Install the dependencies

### Config

Update *app/config.py*.

#### Set Environment Variables

Environment type:

```sh
$ set APP_SETTINGS=app.config.DevelopmentConfig
```
or
```sh
$ set APP_SETTINGS=app.config.ProductionConfig
```

Google credentials (access to postgres SQL DB):

```sh
$ set GOOGLE_APPLICATION_CREDENTIALS=silent-base-230717-54ef7bc5ff66.json
```

#### Create DB

```sh
$ python manage.py create_db
$ python manage.py db init
$ python manage.py db migrate
$ python manage.py create_admin
$ python manage.py create_data
```

#### Migrating DB

Use the following after adding a columns to the models in *models.py* to create the needed columns in your database:

```sh
$ python manage.py db migrate
$ python manage.py db upgrade
```

#### Run

```sh
$ python manage.py runserver
```

#### Testing

Without coverage:

```sh
$ python manage.py test
```

Without coverage and limited to a module inside "tests" directory

```sh
$ python manage.py test --test_name=test_endpoints
```

With coverage:

```sh
$ python manage.py cov
```

