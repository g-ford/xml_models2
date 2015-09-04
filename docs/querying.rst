Querying Models
===============

Querying is based on Django Model querying.  Each ``Model`` has a class attribute ``objects`` which is the entry point
for querying. However the querying ability is limited in scope and only supports very basic filtering.

To do anything interesting you will need to define finders on your models.  There are no assumptions made about the nature of
the REST API e.g. it is not even assumed that an ``id`` attribute can be queried.

.. _finders:

Finders
-------

An external REST api will present a limited number of options for querying data. Because the different options do not
have to follow any specific convention, the model must define what finders are available and what parameters they accept.
This still attempts to follow a Django-esque approach

.. code-block:: python

    class Person(xml_models.Model:
        ...
        finders = { (firstName, lastName): "http://person/firstName/%s/lastName/%s",
                    (id,): "http://person/%s"}

The above defines two query options. The following code exercises these options

.. code-block:: python

    >>> people = Person.objects.filter(firstName='Chris', lastName='Tarttelin')
    >>> people.count()
    1
    >>> person = Person.objects.get(id=123)
    >>> person.firstName
    Chris


Self-signed HTTPS Endpoints
----

Self-signed, or endpoints signed by a non-standard CA, are supported by setting ``xml_models.VERIFY`` as per the requests
documentation for [SSL certificate verification](http://docs.python-requests.org/en/latest/user/advanced/#ssl-cert-verification).

For example, to not verify a self-signed certificate you can use the following:

.. code-block:: python
    >>> import xml_models
    >>> xml_models.VERIFY = False




