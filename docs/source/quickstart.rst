===========
Quickstart
===========

Peppi is meant to be simple to start with.

It brings you to the core of your research in a few lines of code.

The following code has been tested with **Python 3.11**.



Try it
~~~~~~~


Install:

.. code-block:: bash

    pip install pds.peppi


The following lines of code can be found in this `file <https://github.com/NASA-PDS/peppi/tree/main/tests/pds/peppi/quickstart.py>`_

Import:

.. code-block:: python

    from datetime import datetime
    import pds.peppi as pep


Get the connection to the PDS Web API (and the underlying Registry):

.. code-block:: python

    client = pep.PDSRegistryClient()

Find your data, observation data of mercury before 2012-01-23:
Alternate filter methods can be found in the :doc:`reference`

.. code-block:: python

    date1 = datetime.fromisoformat("2012-01-23")
    # mercury identifier in PDS, find it, in the type "target"
    # in the `PDS keyword search <https://pds.nasa.gov/datasearch/keyword-search/search.jsp>`_
    mercury_id = "urn:nasa:pds:context:target:planet.mercury"

    # filter here:
    products = pep.Products(client).has_target(mercury_id).before(date1).observationals()


Iterate on the results:

.. code-block:: python

    for i, p in enumerate(products):
        print(p.id, p.investigations)
        # there a lot of data there, break after a couple of hundreds
        if i > 200:
            break


Numerous pre-defined filters are available, you can `explore them <https://nasa-pds.github.io/peppi/reference.html#pds.peppi.query_builder.QueryBuilder>`_.

Next steps
~~~~~~~~~~~

- Full library :doc:`reference`
- Various Demo Use cases `Jupyter notebooks <https://github.com/NASA-PDS/search-api-notebook>`_ and `Seismic use case <https://github.com/civilinifr/cloud_testcase/>`_
- Missing a feature ? Request it, create a `ticket <https://github.com/nasa-pds/peppi/issues>`_ or start a `discussion <https://github.com/NASA-PDS/peppi/discussions>`_.
