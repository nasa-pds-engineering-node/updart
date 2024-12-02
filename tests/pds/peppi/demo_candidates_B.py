import pds.peppi as pep

# ** option B **
# Same as before, but under the hood the Products inherit ResultSet and QueryBuilder
# to separate concerns in classes and simplify the code
# PRO: user code is short
# CON: blurred boundaries between Query and Result
client = pep.PDSRegistryClient()

lidvid = "urn:nasa:pds:context:target:asteroid.65803_didymos"
products = pep.Products(client)
products = products.has_target(lidvid).observationals()

# do something sequentially
for i, p in enumerate(products):
    print(p.id)
    if i > 10:
        break

# get all the results at once in a new object, here pandas dataframe
df = products.as_dataframe(max_rows=10)
