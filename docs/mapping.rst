Mapping XML to Models
=====================

XML is mapped to ``xml_models.Model`` via ``Fields``.  Each field requires an xpath expression that determines which
node or attribute to get the data from.  Each field also has an optional ``default`` value for when no value can be
retrieved from the XML.

Basic Fields
------------

TThe available field mappings are

- :class:`CharField` -- returns string data
- :class:`IntField` -- returns integers
- :class:`DateField` -- returns a date from using the supplied ``date_format`` mask or the default ISO8601 format
- :class:`FloatField` -- returns a floating point number
- :class:`BoolField` -- returns a boolean
- :class:`OneToOneField` -- returns a ``xml_model.Model`` subclass
- :class:`CollectionField` -- returns a collection of either one of the above types, or an ``xml_model.Model`` subclass

Most of these fields are fairly self explanatory. The ``CollectionField`` and ``OneToOneField`` is where it gets
interesting. This is what allows you to map instances or collections of nested entities, such as:-

.. code-block:: xml

    <Person id="112">
      <firstName>Chris</firstName>
      <lastName>Tarttelin</lastName>
      <occupation>Code Geek</occupation>
      <website>http://www.pyruby.com</website>
      <contact-info>
        <contact type="telephone">
          <info>(555) 555-5555</info>
          <description>Cell phone, but no calls during work hours</description>
        </contact>
        <contact type="email">
          <info>me@here.net</info>
          <description>Where possible, contact me by email</description>
        </contact>
        <contact type="telephone">
          <info>1-800-555-5555</info>
          <description>Toll free work number for during office hours.</description>
        </contact>
      </contact-info>
    </Person>

This can be mapped using a ``Person`` and a ``ContactInfo`` model:-

.. code-block:: python

    class Person(Model):
      id = IntField(xpath="/Person/@id")
      firstName = CharField(xpath="/Person/firstName")
      lastName = CharField(xpath="/Person/lastName")
      contacts = CollectionField(ContactInfo, order_by="contact_type", xpath="/Person/contact-info/contact")

    class ContactInfo(Model):
      contact_type = CharField(xpath="/contact/@type")
      info = CharField(xpath="/contact/info")
      description = CharField(xpath="/contact/description", default="No description supplied")

This leads to the usage of a person as :-

>>> person.contacts[0].info
me@here.com

Collections
-----------

When querying collections or lists, it is assumed that a collection of zero or more results are returned wrapped in an
enclosing collection tag.

As some REST APIs may return lists wrapped in one or more layers of metadata, Models may also define
a ``collection_node`` attribute. this allows the XML processor to find the relevant node.

.. note:: ``collection_node`` is the tag name only and not an xpath expression.

For example, given the following XML

.. code-block:: xml

    <reponse status="200">
      <metadata count="2">
      <collection>
        <model ... />
        <model ... />
      </collection>
      </metadata>
    </response>

We would need to define a Model with a ``collection_node`` like so

.. code-block:: python

    class SomeModel(Model):
      fieldA = CharField(xpath="/some/node")

      collection_node = 'collection'

