# About

This is the backend repository for Code Stroke - an app designed to streamline
stroke management.

# API Documentation

The API documentation is located in [API.md](API.md).

# Getting Started 

At the moment, the setup process requires a number of configuration steps. In
the future, we plan to automate the setup process and provide a clean
configuration interface.

## Prerequisites

You will need to have a working installation of Python 3 and MySQL 5.6 or 5.7.
If you are using MySQL 8, you must choose `Legacy Authentication Method` as your
Authentication method at startup.

It is recommended you use a virtual environment, especially when developing. 

You may also require a Visual Studio C++ redistributable to successfully install
the required `pip` modules.

## Basic Setup

First, download or `git clone` this repository.

``` sh
git clone https://github.com/code-stroke/codestroke-backend.git codestroke-backend
```

Navigate to the cloned directory. If you are using a virtual environment, make
sure it is activated; otherwise, install the pip modules globally.

``` sh
cd codestroke-backend
pip install -r requirements.txt
```

Next, you will need to create an `app.conf` file in this directory. There is a
template, `template.conf` in `resources` which you can fill in, rename and move
to this directory. It is important to get the configuration details right at
this stage, otherwise the app will not run correctly. At some point, we hope to
move this configuration into a more convenient interface.

Next, from this directory, run:

``` sh
python quick_setup.py
```

This will create a test database and a deployment database and will prompt you
for details to add the first (and only!) administrator. This administrator
account is important, as it is the only way to add clinician users to the app.

Next, try:

``` sh
python app.py
```

This starts the development server in debug mode. If all is well, you should be
able to navigate to [http://localhost:5000](http://localhost:5000) and see a
message saying something along the lines of "You cannot access this page
directly." This is good as a sanity check.

Stop the development server with `Ctrl-c`, then run the tests with:

``` sh
pytest
```

You should then see whether all the tests pass or not. Hopefully, they'll all
pass - if not, you'll have to check which test failed and why.

If you are a developer, you can stop here - however if you want to deploy the
server, you will need to undergo a few further steps to set it up. You should
refer to your specific server's docs to find out how - for example, if you are
using IIS on Windows, you will need to add a `web.config` file to this
directory, configure `wfastcgi.py` with handler mappings and configure the
`PYTHON_PATH` and `WSGI_HANDLER` (app.app) values. 

# Demo Backend

A demo backend API is available on PythonAnywhere and can be accessed at
[http://codefactor.pythonanywhere.com/](http://codefactor.pythonanywhere.com/).

You will need to be added as a user to demo this API. If you are part of the
development team, please speak to one of the development members.
# Contributing

## API Document Generation

The API documentation is written in the
[OpenAPI](https://swagger.io/docs/specification/about/) specification. Part of
the API documentation (the definitions) are generated from
`resources/schema.sql` using the `scripts/scan_schema.py` script and should be
rerun if changes are made to the schema.

# TODOs

The following API changes are suggested for future releases. To avoid breaking
the current API, they will be kept on hold for now.

- Change all timestamp/date-time values to format `2012-04-23T18:25:43.511Z`
  (currently takes string of form `2012-04-23T18:25:43`)
 
