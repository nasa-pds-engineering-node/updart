import unittest

import pds.peppi as pep


class OrexProductsTestCase(unittest.TestCase):
    MAX_ITERATIONS = 1000
    """Maximum number of iterations over query results to perform before ending test."""

    def setUp(self) -> None:
        self.client = pep.PDSRegistryClient()
        self.products = pep.OrexProducts(self.client)

    def test_has_investigation(self):
        # Check that an instance of OrexProducts is initialized with a has_instrument filter
        self.assertIn(
            'ref_lid_investigation eq "urn:nasa:pds:context:investigation:mission.orex"', self.products._q_string
        )

        # Check that an attempt to add an investigation filter results in an exception
        with self.assertRaises(NotImplementedError):
            self.products.has_investigation("urn:nasa:pds:context:investigation:mission.not_orex")

    def test_within_range(self):
        n = 0
        for p in self.products.within_range(100.0):
            n += 1

            assert "orex:Spatial.orex:target_range" in p.properties
            assert len(p.properties["orex:Spatial.orex:target_range"]) >= 1
            assert all(float(target_range) <= 100.0 for target_range in p.properties["orex:Spatial.orex:target_range"])

            if n > self.MAX_ITERATIONS:
                break

    def test_within_bbox(self):
        n = 0
        for p in self.products.within_bbox(9.0, 15.0, 21.0, 27.0):
            n += 1

            assert "orex:Spatial.orex:latitude" in p.properties
            assert "orex:Spatial.orex:longitude" in p.properties
            assert len(p.properties["orex:Spatial.orex:latitude"]) >= 1
            assert len(p.properties["orex:Spatial.orex:longitude"]) >= 1
            assert all(9.0 <= float(latitude) <= 15.0 for latitude in p.properties["orex:Spatial.orex:latitude"])
            assert all(21.0 <= float(longitude) <= 27.0 for longitude in p.properties["orex:Spatial.orex:longitude"])

            if n > self.MAX_ITERATIONS:
                break
