## S P I N U P C A F E

# SPIN-UP Automation Tests

Pytest based framework to perform functional end-to-end testing of Spark backend APIs

Automated tests for [SPARK](https://github.rackspace.com/kapi3776/Spark_pytest),

## Initial Setup

You should use a virtualenv. There are plenty of resources out there that describe them.

1. Create a virtual env using python-3.6 --> `virtualenv -p python3 spark_pytest`
2. Activate the virtual env --> `source {path/to/spark_pytest}/bin/activate`
3. Install all the dependencies --> `pip install -r requirements.txt`
4. Set the environment against which you want to run your tests:

    (i) Run --> `export ENV_FOR_DYNACONF=default` if you want to run using the default section config settings which 
    points to old production or spark oh three.

   (ii)Run --> `export ENV_FOR_DYNACONF=development` if you want to run tests using the development section config 
   settings, which points to the development-spark env.
   
   (iii)Run --> `export ENV_FOR_DYNACONF=staging` if you want to run tests using the staging section config settings,
   which points to the staging-spark env.
   
   (iv)Run --> `export ENV_FOR_DYNACONF=production` if you want to run tests using the production section config 
   settings, which points to the production-spark env.
   
(Go to `settings.toml` to understand the different section/environment-scope configs)

## Running Tests

Before running the tests, navigate to the spark_pytest directory:

`cd Spark_pytest`

Run all tests with: `pytest`, but not a good idea though

Below are the different ways to run product specific tests:

## HOW TO RUN SERVER TESTS...

(i) Run all the server regression tests:

`pytest -m server`

(ii) Run all the server smoke tests

`pytest -m 'server and smoke'`

(iii) Run all the server crud tests

`pytest -k 'server_crud' -m server`

(iv) Run all the server snapshot crud tests

`pytest -k 'snapshot' -m server`

(v) Run all the server console functionality tests

`pytest -k 'console' -m server`

(vi) Run all the server rebuild core tests

`pytest -k 'rebuild' -m 'server and not integration'`

(vii)Run all the server rebuild with volume integration tests

`pytest -k 'rebuild' -m 'server and integration'`

(viii)Run all the server rescue tests

`pytest -k 'rescue' -m server`

(ix)Run all the server resize core tests

`pytest -k 'resize' -m 'server and not integration'`

(x)Run all the server resize with volume integration tests

`pytest -k 'resize' -m 'server and integration'`

(xi)Run all the server with volume integration tests

`pytest -m integration_only`

## HOW TO RUN VOLUME TESTS...

(i) Run all the volume regression tests

`pytest -m volume`

(ii) Run all the volume smoke tests

`pytest -m 'volume and smoke'`

(iii) Run all volume snapshot tests 

`pytest -k 'snapshot' -m volume`

## HOW TO RUN LOADBALANCER TESTS...

(i) Run all the loadbalancer regression tests

`pytest -m loadbalancer`

## Directory Layout
```
|                    __ User
|                   |__ Account
|____ Identity_Api__|__ Project
|                   |__ tests
|
|____ Common->|____ Clients
|             |
|             |___ Fixtures -->  Conftests_<product>.py
|             |
|             |___ Data_models_______ Constants
|                               |
|                               |____ tools
|_____ Tests
|
|_____ Conftest.py (Session level fixtures/ Plugins(product level conftests.py)
|
|_____ Settings.toml
|
|_____ Pytest.ini
|
|_____ Coverage (Coverage report)
|
|_____ Reports (HTML reports via allure

```
