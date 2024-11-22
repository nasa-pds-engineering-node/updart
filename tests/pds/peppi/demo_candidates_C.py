import pds.peppi as pep

# ** option C **
# Products result is instantiated from both the connexion to the API and the query
# PRO: that sounds the most simple and readable implementation for the user
# CON: we loose the elegance of the Query being evaluated smoothly into a ResultSet

client = pep.PDSRegistryClient()

lidvid = "urn:nasa:pds:context:target:asteroid.65803_didymos"
query = pep.QueryBuilder().has_target(lidvid).observationals()
products = pep.Products(client, query)

# do something sequentially
for i, p in enumerate(products):
    print(p.id)
    if i > 10:
        break

# get all the results at once in a new object, here pandas dataframe
df = products.as_dataframe(max_rows=10)
