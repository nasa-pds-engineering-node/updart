import unittest
from datetime import datetime
from typing import get_args

import pds.peppi as pep  # type: ignore
from pds.api_client import PdsProduct


class ClientTestCase(unittest.TestCase):
    MAX_ITERATIONS = 1000
    """Maximum number of iterations over query results to perform before ending test."""

    def setUp(self) -> None:
        self.client = pep.PDSRegistryClient()
        self.products = pep.Products(self.client)

    def test_all(self):
        n = 0
        for p in self.products:
            n += 1
            assert isinstance(p, PdsProduct)
            if n > self.MAX_ITERATIONS:
                break

        assert True

    def test_fields(self):
        selected_fields = ["pds:Primary_Result_Summary.pds:processing_level", "pds:File.pds:file_name"]
        non_selected_fields_examples = ["pds:Time_Coordinates.pds:stop_date_time", "pds:Identification_Area.pds:title"]
        for p in self.products.fields(selected_fields):
            break

        for field in selected_fields:
            assert field in p.properties

        for field in non_selected_fields_examples:
            assert field not in p.properties

    def test_as_dataframe(self):
        selected_fields = ["pds:Time_Coordinates.pds:start_date_time", "pds:Time_Coordinates.pds:stop_date_time"]
        df = (
            self.products.of_collection("urn:nasa:pds:apollo_pse:data_seed::1.0")
            .fields(selected_fields)
            .as_dataframe(max_rows=10)
        )

        assert len(df) == 10

        for field in selected_fields:
            assert field in df.columns

        assert isinstance(df["pds:Time_Coordinates.pds:start_date_time"].iloc[0], str)

    def test_empty_dataframe(self):
        df = self.products.of_collection("non_existing_collection").as_dataframe()
        assert df is None

    def test_query_modification_during_pagination(self):
        n = 0
        for p in self.products:
            n += 1
            assert isinstance(p, PdsProduct)

            if n > self.MAX_ITERATIONS:
                # Attempt to modify the query clause while there are still results
                # to paginate through. This should result in a RuntimeError.
                with self.assertRaises(RuntimeError):
                    self.products.observationals()

                # Now reset the state on the Products instance. This should
                # allow clauses to be added again
                self.products.reset()

                try:
                    self.products.observationals()
                except RuntimeError:
                    self.fail("Unexpected RuntimeError raised")

                break

    def test_has_target(self):
        lidvid = "urn:nasa:pds:context:target:asteroid.65803_didymos"
        n = 0
        for p in self.products.has_target(lidvid):
            n += 1
            assert lidvid in p.properties["ref_lid_target"]
            if n > self.MAX_ITERATIONS:
                break

    def test_has_investigation(self):
        lid = "urn:nasa:pds:context:investigation:individual_investigation.lab.hydrocarbon_spectra"
        n = 0
        for p in self.products.has_investigation(lid):
            n += 1
            assert lid in p.properties["ref_lid_investigation"]
            if n > self.MAX_ITERATIONS:
                break

    def test_before(self):
        iso8601_date = "2005-07-06T05:50:23Z".replace("Z", "+00:00")
        date_ref = datetime.fromisoformat(iso8601_date)
        n = 0
        for p in self.products.before(date_ref):
            n += 1
            iso8601_date_found = p.start_date_time.replace("Z", "+00:00")
            date_found = datetime.fromisoformat(iso8601_date_found)
            assert date_found <= date_ref
            if n > self.MAX_ITERATIONS:
                break

    def test_after(self):
        iso8601_date = "2005-07-07T05:50:23Z".replace("Z", "+00:00")
        date_ref = datetime.fromisoformat(iso8601_date)
        n = 0
        for p in self.products.after(date_ref):
            n += 1
            iso8601_date_found = p.start_date_time.replace("Z", "+00:00")
            date_found = datetime.fromisoformat(iso8601_date_found)
            assert date_found >= date_ref
            if n > self.MAX_ITERATIONS:
                break

    def test_before_and_has_target(self):
        lidvid = "urn:nasa:pds:context:target:comet.9p_tempel_1"
        iso8601_date = "2005-07-06T05:47:25+00:00"
        date_ref = datetime.fromisoformat(iso8601_date)
        n = 0
        for p in self.products.has_target(lidvid).before(date_ref):
            n += 1
            assert lidvid in p.properties["ref_lid_target"]
            iso8601_date_found = p.start_date_time.replace("Z", "+00:00")
            date_found = datetime.fromisoformat(iso8601_date_found)
            assert date_found <= date_ref
            if n > self.MAX_ITERATIONS:
                break

    def test_products_of_collection(self):
        lidvid = "urn:nasa:pds:apollo_pse:data_seed::1.0"
        n = 0
        for p in self.products.of_collection(lidvid):
            n += 1
            found_id = p.properties["ops:Provenance.ops:parent_collection_identifier"][0]
            assert found_id == lidvid
            if n > self.MAX_ITERATIONS:
                break

    def test_observationals(self):
        n = 0
        for p in self.products.observationals():
            n += 1
            assert "Product_Observational" in p.properties["product_class"]
            if n > self.MAX_ITERATIONS:
                break

    def test_collections(self):
        n = 0
        for p in self.products.collections():
            n += 1
            assert "Product_Collection" in p.properties["product_class"]
            if n > self.MAX_ITERATIONS:
                break

    def test_collections_with_type(self):
        collection_types = ["Context", "Data", "Browse"]
        for collection_type in collection_types:
            n = 0
            for p in self.products.collections(collection_type=collection_type):
                n += 1
                assert "Product_Collection" in p.properties["product_class"]
                assert collection_type in p.properties["pds:Collection.pds:collection_type"]
                if n > self.MAX_ITERATIONS:
                    self.products.reset()
                    break

    def test_bundles(self):
        n = 0
        for p in self.products.bundles():
            n += 1
            assert "Product_Bundle" in p.properties["product_class"]
            if n > self.MAX_ITERATIONS:
                break

    def test_has_instrument(self):
        lidvid = "urn:nasa:pds:context:instrument:cls.farir_beamline"
        n = 0
        for p in self.products.has_instrument(lidvid):
            n += 1
            assert lidvid in p.properties["ref_lid_instrument"]
            if n > self.MAX_ITERATIONS:
                break

    def test_has_instrument_host(self):
        lidvid = "urn:nasa:pds:context:instrument_host:spacecraft.insight"
        n = 0
        for p in self.products.has_instrument_host(lidvid):
            n += 1
            assert lidvid in p.properties["ref_lid_instrument_host"]
            if n > self.MAX_ITERATIONS:
                break

    def test_has_processing_level(self):
        for processing_level in get_args(pep.client.PROCESSING_LEVELS):
            n = 0
            for p in self.products.has_processing_level(processing_level):
                n += 1
                assert processing_level.title() in p.properties["pds:Primary_Result_Summary.pds:processing_level"]
                if n > self.MAX_ITERATIONS:
                    self.products.reset()
                    break

    def test_get(self):
        lid = "urn:nasa:pds:lab.hydrocarbon_spectra:document:n2h2202k295k"
        vid = "1.0"
        lidvid = f"{lid}::{vid}"
        n = 0
        for p in self.products.get(lidvid):
            n += 1
            assert lid in p.properties["lid"]
            assert vid in p.properties["vid"]
            if n > self.MAX_ITERATIONS:
                break

    def test_filter(self):
        node_name = "PDS_ATM"
        clause = f'ops:Harvest_Info.ops:node_name eq "{node_name}"'
        n = 0
        for p in self.products.filter(clause):
            n += 1
            assert node_name in p.properties["ops:Harvest_Info.ops:node_name"]
            if n > self.MAX_ITERATIONS:
                break


if __name__ == "__main__":
    unittest.main()
