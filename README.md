[![Build Status](https://travis-ci.org/alephnullplex/xml_models2.svg?branch=master)](https://travis-ci.org/alephnullplex/xml_models2)
[![Coverage Status](https://coveralls.io/repos/alephnullplex/xml_models2/badge.svg?branch=master)](https://coveralls.io/r/alephnullplex/xml_models2?branch=master)

# XmlModels2

XmlModels allows you to define Models similar in nature to Django models that are backed by XML endpoints rather than a
database.   Using a familiar declarative definition, the fields map to values in the XML document by means of XPath
expressions. With support for querying external REST APIs using a django-esque approach, we have strived to make
writing and using xml backed models as close to django database models as we can, within the limitations of the
available API calls.

# Installation

The simplest approach is to to use `pip install xml_models2`

# A simple example

Just to get started, this is an example of taking an XML representation of an Address that might be returned from a
GET request to an external REST api.

    <Address id="2">
      <number>22</number>
      <street>Acacia Avenue</street>
      <city>Maiden</city>
      <country>England</country>
      <postcode>IM6 66B</postcode>
    </Address>

    class Address(xml_models.Model):
      id=xml_models.IntField(xpath="/Address/@id")
      number = xml_models.IntField(xpath="/Address/number")
      street = xml_models.CharField(xpath="/Address/street")
      city = xml_models.CharField(xpath="/Address/city")
      country = xml_models.CharField(xpath="/Address/country")
      postcode = xml_models.CharField(xpath="/Address/postcode")

      finders = {(id,): 'http://adresses/%s'}

This example would be used as follows:-

    >>> address = Address.objects.get(id=2)
    >>> print "address is %s, %s" % (address.number, address.street)
    "22, Acacia Avenue"

# Heritage

This project is a fork of [Django REST Models](http://djangorestmodel.sourceforge.net/)
