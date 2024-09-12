import unittest
from datetime import datetime

import pds.updart as upd  # type: ignore


class ClientTestCase(unittest.TestCase):
    def setUp(self) -> None:
        pass

    def test_all(self):
        """
        Up to 1000 products
        :return:
        """
        client = upd.PDSRegistryClient()
        products = upd.Products(client)
        n = 0
        for p in products:
            n += 1
            print(p.id)
            if n > 1000:
                break
        assert True

    def test_has_target(self):
        client = upd.PDSRegistryClient()
        products = upd.Products(client)
        lidvid = "urn:nasa:pds:context:target:asteroid.65803_didymos"
        n = 0
        for p in products.has_target(lidvid):
            n += 1
            assert lidvid in p.properties["ref_lid_target"]
            if n > 1000:
                break

    def test_before(self):
        client = upd.PDSRegistryClient()
        products = upd.Products(client)
        iso8601_date = "2005-07-06T05:50:23Z".replace("Z", "+00:00")
        date_ref = datetime.fromisoformat(iso8601_date)
        n = 0
        for p in products.before(date_ref):
            n += 1
            iso8601_date_found = p.start_date_time.replace("Z", "+00:00")
            date_found = datetime.fromisoformat(iso8601_date_found)
            assert date_found <= date_ref
            if n > 1000:
                break

    def test_after(self):
        # TODO implement
        pass

    def test_products_of_collection(self):
        client = upd.PDSRegistryClient()
        products = upd.Products(client)
        id = "urn:nasa:pds:apollo_pse:data_seed::1.0"
        n = 0
        for p in products.of_collection(id):
            n += 1
            found_id = p.properties["ops:Provenance.ops:parent_collection_identifier"][0]
            assert found_id == id
            if n > 1000:
                break

    def test_before_and_has_target(self):
        client = upd.PDSRegistryClient()
        products = upd.Products(client)
        lidvid = "urn:nasa:pds:context:target:comet.9p_tempel_1"
        iso8601_date = "2005-07-06T05:47:25+00:00"
        date_ref = datetime.fromisoformat(iso8601_date)
        n = 0
        for p in products.has_target(lidvid).before(date_ref):
            n += 1
            assert lidvid in p.properties["ref_lid_target"]
            iso8601_date_found = p.start_date_time.replace("Z", "+00:00")
            date_found = datetime.fromisoformat(iso8601_date_found)
            assert date_found <= date_ref
            if n > 1000:
                break


if __name__ == "__main__":
    unittest.main()
