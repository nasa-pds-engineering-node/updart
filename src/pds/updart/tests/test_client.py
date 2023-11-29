import unittest
from datetime import datetime

import pds.updart as upd  # type: ignore


class ClientTestCase(unittest.TestCase):
    def setUp(self) -> None:
        pass

    def test_all(self):
        client = upd.PDSRegistryClient()
        products = upd.Products(client)
        for p in products:
            print(p.id)
        assert True

    def test_has_target(self):
        client = upd.PDSRegistryClient()
        products = upd.Products(client)
        lidvid = "urn:nasa:pds:context:target:asteroid.65803_didymos"
        for p in products.has_target(lidvid):
            assert lidvid in p.properties["ref_lid_target"]

    def test_before(self):
        client = upd.PDSRegistryClient()
        products = upd.Products(client)
        iso8601_date = "2005-07-06T05:50:23Z".replace("Z", "+00:00")
        date_ref = datetime.fromisoformat(iso8601_date)
        for p in products.before(date_ref):
            iso8601_date_found = p.properties["pds:Time_Coordinates.pds:start_date_time"][0].replace("Z", "+00:00")
            date_found = datetime.fromisoformat(iso8601_date_found)
            assert date_found <= date_ref

    def test_after(self):
        # TODO implement
        pass

    def test_before_and_has_target(self):
        client = upd.PDSRegistryClient()
        products = upd.Products(client)
        lidvid = "urn:nasa:pds:context:target:comet.9p_tempel_1"
        iso8601_date = "2005-07-06T05:47:25Z".replace("Z", "+00:00")
        date_ref = datetime.fromisoformat(iso8601_date)
        for p in products.has_target(lidvid).before(date_ref):
            assert lidvid in p.properties["ref_lid_target"]
            iso8601_date_found = p.properties["pds:Time_Coordinates.pds:start_date_time"][0].replace("Z", "+00:00")
            date_found = datetime.fromisoformat(iso8601_date_found)
            assert date_found <= date_ref


if __name__ == "__main__":
    unittest.main()
