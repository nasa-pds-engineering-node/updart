import pds.peppi as pep

# ** option A **
# a QueryBuilder has an explicit evaluation method called `crack`
# which triggers the query to be evaluated and returns a ResultSet object
# PRO:
#   - explicit evaluation of the result
#   - 'crack' could be kind of fun for peppi, but we could be more traditional with 'open' or 'execute'
# CON:
#   - crack or open might sound useless in the client code, or unclear what it's useful for
lidvid = "urn:nasa:pds:context:target:asteroid.65803_didymos"
query = pep.QueryBuilder().has_target(lidvid).observationals()

client = pep.PDSRegistryClient()
products = query.crack(client)

# do something sequentially
for i, p in enumerate(products):
    print(p.id)
    if i > 10:
        break

# get all the results at once in a new object, here pandas dataframe
df = query.crack(client).as_dataframe(max_rows=10)
