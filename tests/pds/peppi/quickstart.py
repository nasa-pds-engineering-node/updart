from datetime import datetime

import pds.peppi as pep

# Get the connection to the PDS Web API (and the underlying Registry)
client = pep.PDSRegistryClient()

# Find your data, observation data of mercury before 2012-01-23:
# find alternate filter methods in the `reference </reference.html#pds.peppi.query_builder.QueryBuilder>`_
date1 = datetime.fromisoformat("2012-01-23")
# mercury identifier in PDS, find it as target
# in the `PDS keyword search <https://pds.nasa.gov/datasearch/keyword-search/search.jsp>`_
mercury_id = "urn:nasa:pds:context:target:planet.mercury"
# filter here:
products = pep.Products(client).has_target("Mercury").before(date1).observationals()

# Iterate on the results:
for i, p in enumerate(products):
    print(p.id, p.investigations)
    # there a lot of there data, break after a couple of hundreds
    if i > 200:
        break
