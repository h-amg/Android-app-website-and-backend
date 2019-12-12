# XHominid Webb App


Backend for an Android nutrition coaching and meal planning app

This flask-backend serves as the App website while handling backend requests from client app


## Introduction

XHomind is a platform that helps people looking for nutrition coaching and meal planning get connected with a qualified professional nutritionist. The platform enables professional nutritionists to conduct nutrition assessment interviews through XHomind video call feature. After this assessment the user then gets access to weekly meal plans prepared by the nutritionist, they are then able to directly message the nutritionist for further questions via XHominid messaging feature. In order to maintain continuous progress the users are able to book weekly one to one coaching sessions with their nutritionist via the video call booking feature. The user is able to view meal information, recipes and cooking instructions as well as mark meals eaten throughout the day. The daily nutritional intake logs are uploaded instantly and made accessible to the user nutritionist so that the can advice and guide them when needed and make improvements to the upcoming weeks' plan.


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

