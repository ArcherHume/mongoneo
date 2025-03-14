import unittest

from mongoneo import *
from tests.utils import MongoDBTestCase


class TestGeoField(MongoDBTestCase):
    def _test_for_expected_error(self, Cls, loc, expected):
        try:
            Cls(loc=loc).validate()
            self.fail(f"Should not validate the location {loc}")
        except ValidationError as e:
            assert expected == e.to_dict()["loc"]

    def test_geopoint_validation(self):
        class Location(Document):
            loc = GeoPointField()

        invalid_coords = [{"x": 1, "y": 2}, 5, "a"]
        expected = "GeoPointField can only accept tuples or lists of (x, y)"

        for coord in invalid_coords:
            self._test_for_expected_error(Location, coord, expected)

        invalid_coords = [[], [1], [1, 2, 3]]
        for coord in invalid_coords:
            expected = "Value (%s) must be a two-dimensional point" % repr(coord)
            self._test_for_expected_error(Location, coord, expected)

        invalid_coords = [[{}, {}], ("a", "b")]
        for coord in invalid_coords:
            expected = "Both values (%s) in point must be float or int" % repr(coord)
            self._test_for_expected_error(Location, coord, expected)

        invalid_coords = [21, 4, "a"]
        for coord in invalid_coords:
            expected = "GeoPointField can only accept tuples or lists of (x, y)"
            self._test_for_expected_error(Location, coord, expected)

    def test_point_validation(self):
        class Location(Document):
            loc = PointField()

        invalid_coords = {"x": 1, "y": 2}
        expected = (
            "PointField can only accept a valid GeoJson dictionary or lists of (x, y)"
        )
        self._test_for_expected_error(Location, invalid_coords, expected)

        invalid_coords = {"type": "MadeUp", "coordinates": []}
        expected = 'PointField type must be "Point"'
        self._test_for_expected_error(Location, invalid_coords, expected)

        invalid_coords = {"type": "Point", "coordinates": [1, 2, 3]}
        expected = "Value ([1, 2, 3]) must be a two-dimensional point"
        self._test_for_expected_error(Location, invalid_coords, expected)

        invalid_coords = [5, "a"]
        expected = "PointField can only accept lists of [x, y]"
        for coord in invalid_coords:
            self._test_for_expected_error(Location, coord, expected)

        invalid_coords = [[], [1], [1, 2, 3]]
        for coord in invalid_coords:
            expected = "Value (%s) must be a two-dimensional point" % repr(coord)
            self._test_for_expected_error(Location, coord, expected)

        invalid_coords = [[{}, {}], ("a", "b")]
        for coord in invalid_coords:
            expected = "Both values (%s) in point must be float or int" % repr(coord)
            self._test_for_expected_error(Location, coord, expected)

        Location(loc=[1, 2]).validate()
        Location(
            loc={"type": "Point", "coordinates": [81.4471435546875, 23.61432859499169]}
        ).validate()

    def test_linestring_validation(self):
        class Location(Document):
            loc = LineStringField()

        invalid_coords = {"x": 1, "y": 2}
        expected = "LineStringField can only accept a valid GeoJson dictionary or lists of (x, y)"
        self._test_for_expected_error(Location, invalid_coords, expected)

        invalid_coords = {"type": "MadeUp", "coordinates": [[]]}
        expected = 'LineStringField type must be "LineString"'
        self._test_for_expected_error(Location, invalid_coords, expected)

        invalid_coords = {"type": "LineString", "coordinates": [[1, 2, 3]]}
        expected = (
            "Invalid LineString:\nValue ([1, 2, 3]) must be a two-dimensional point"
        )
        self._test_for_expected_error(Location, invalid_coords, expected)

        invalid_coords = [5, "a"]
        expected = "Invalid LineString must contain at least one valid point"
        self._test_for_expected_error(Location, invalid_coords, expected)

        invalid_coords = [[1]]
        expected = (
            "Invalid LineString:\nValue (%s) must be a two-dimensional point"
            % repr(invalid_coords[0])
        )
        self._test_for_expected_error(Location, invalid_coords, expected)

        invalid_coords = [[1, 2, 3]]
        expected = (
            "Invalid LineString:\nValue (%s) must be a two-dimensional point"
            % repr(invalid_coords[0])
        )
        self._test_for_expected_error(Location, invalid_coords, expected)

        invalid_coords = [[[{}, {}]], [("a", "b")]]
        for coord in invalid_coords:
            expected = (
                "Invalid LineString:\nBoth values (%s) in point must be float or int"
                % repr(coord[0])
            )
            self._test_for_expected_error(Location, coord, expected)

        Location(loc=[[1, 2], [3, 4], [5, 6], [1, 2]]).validate()

    def test_polygon_validation(self):
        class Location(Document):
            loc = PolygonField()

        invalid_coords = {"x": 1, "y": 2}
        expected = (
            "PolygonField can only accept a valid GeoJson dictionary or lists of (x, y)"
        )
        self._test_for_expected_error(Location, invalid_coords, expected)

        invalid_coords = {"type": "MadeUp", "coordinates": [[]]}
        expected = 'PolygonField type must be "Polygon"'
        self._test_for_expected_error(Location, invalid_coords, expected)

        invalid_coords = {"type": "Polygon", "coordinates": [[[1, 2, 3]]]}
        expected = "Invalid Polygon:\nValue ([1, 2, 3]) must be a two-dimensional point"
        self._test_for_expected_error(Location, invalid_coords, expected)

        invalid_coords = [[[5, "a"]]]
        expected = (
            "Invalid Polygon:\nBoth values ([5, 'a']) in point must be float or int"
        )
        self._test_for_expected_error(Location, invalid_coords, expected)

        invalid_coords = [[[]]]
        expected = "Invalid Polygon must contain at least one valid linestring"
        self._test_for_expected_error(Location, invalid_coords, expected)

        invalid_coords = [[[1, 2, 3]]]
        expected = "Invalid Polygon:\nValue ([1, 2, 3]) must be a two-dimensional point"
        self._test_for_expected_error(Location, invalid_coords, expected)

        invalid_coords = [[[{}, {}]], [("a", "b")]]
        expected = "Invalid Polygon:\nBoth values ([{}, {}]) in point must be float or int, Both values (('a', 'b')) in point must be float or int"
        self._test_for_expected_error(Location, invalid_coords, expected)

        invalid_coords = [[[1, 2], [3, 4]]]
        expected = "Invalid Polygon:\nLineStrings must start and end at the same point"
        self._test_for_expected_error(Location, invalid_coords, expected)

        Location(loc=[[[1, 2], [3, 4], [5, 6], [1, 2]]]).validate()

    def test_multipoint_validation(self):
        class Location(Document):
            loc = MultiPointField()

        invalid_coords = {"x": 1, "y": 2}
        expected = "MultiPointField can only accept a valid GeoJson dictionary or lists of (x, y)"
        self._test_for_expected_error(Location, invalid_coords, expected)

        invalid_coords = {"type": "MadeUp", "coordinates": [[]]}
        expected = 'MultiPointField type must be "MultiPoint"'
        self._test_for_expected_error(Location, invalid_coords, expected)

        invalid_coords = {"type": "MultiPoint", "coordinates": [[1, 2, 3]]}
        expected = "Value ([1, 2, 3]) must be a two-dimensional point"
        self._test_for_expected_error(Location, invalid_coords, expected)

        invalid_coords = [[]]
        expected = "Invalid MultiPoint must contain at least one valid point"
        self._test_for_expected_error(Location, invalid_coords, expected)

        invalid_coords = [[[1]], [[1, 2, 3]]]
        for coord in invalid_coords:
            expected = "Value (%s) must be a two-dimensional point" % repr(coord[0])
            self._test_for_expected_error(Location, coord, expected)

        invalid_coords = [[[{}, {}]], [("a", "b")]]
        for coord in invalid_coords:
            expected = "Both values (%s) in point must be float or int" % repr(coord[0])
            self._test_for_expected_error(Location, coord, expected)

        Location(loc=[[1, 2]]).validate()
        Location(
            loc={
                "type": "MultiPoint",
                "coordinates": [[1, 2], [81.4471435546875, 23.61432859499169]],
            }
        ).validate()

    def test_multilinestring_validation(self):
        class Location(Document):
            loc = MultiLineStringField()

        invalid_coords = {"x": 1, "y": 2}
        expected = "MultiLineStringField can only accept a valid GeoJson dictionary or lists of (x, y)"
        self._test_for_expected_error(Location, invalid_coords, expected)

        invalid_coords = {"type": "MadeUp", "coordinates": [[]]}
        expected = 'MultiLineStringField type must be "MultiLineString"'
        self._test_for_expected_error(Location, invalid_coords, expected)

        invalid_coords = {"type": "MultiLineString", "coordinates": [[[1, 2, 3]]]}
        expected = "Invalid MultiLineString:\nValue ([1, 2, 3]) must be a two-dimensional point"
        self._test_for_expected_error(Location, invalid_coords, expected)

        invalid_coords = [5, "a"]
        expected = "Invalid MultiLineString must contain at least one valid linestring"
        self._test_for_expected_error(Location, invalid_coords, expected)

        invalid_coords = [[[1]]]
        expected = (
            "Invalid MultiLineString:\nValue (%s) must be a two-dimensional point"
            % repr(invalid_coords[0][0])
        )
        self._test_for_expected_error(Location, invalid_coords, expected)

        invalid_coords = [[[1, 2, 3]]]
        expected = (
            "Invalid MultiLineString:\nValue (%s) must be a two-dimensional point"
            % repr(invalid_coords[0][0])
        )
        self._test_for_expected_error(Location, invalid_coords, expected)

        invalid_coords = [[[[{}, {}]]], [[("a", "b")]]]
        for coord in invalid_coords:
            expected = (
                "Invalid MultiLineString:\nBoth values (%s) in point must be float or int"
                % repr(coord[0][0])
            )
            self._test_for_expected_error(Location, coord, expected)

        Location(loc=[[[1, 2], [3, 4], [5, 6], [1, 2]]]).validate()

    def test_multipolygon_validation(self):
        class Location(Document):
            loc = MultiPolygonField()

        invalid_coords = {"x": 1, "y": 2}
        expected = "MultiPolygonField can only accept a valid GeoJson dictionary or lists of (x, y)"
        self._test_for_expected_error(Location, invalid_coords, expected)

        invalid_coords = {"type": "MadeUp", "coordinates": [[]]}
        expected = 'MultiPolygonField type must be "MultiPolygon"'
        self._test_for_expected_error(Location, invalid_coords, expected)

        invalid_coords = {"type": "MultiPolygon", "coordinates": [[[[1, 2, 3]]]]}
        expected = (
            "Invalid MultiPolygon:\nValue ([1, 2, 3]) must be a two-dimensional point"
        )
        self._test_for_expected_error(Location, invalid_coords, expected)

        invalid_coords = [[[[5, "a"]]]]
        expected = "Invalid MultiPolygon:\nBoth values ([5, 'a']) in point must be float or int"
        self._test_for_expected_error(Location, invalid_coords, expected)

        invalid_coords = [[[[]]]]
        expected = "Invalid MultiPolygon must contain at least one valid Polygon"
        self._test_for_expected_error(Location, invalid_coords, expected)

        invalid_coords = [[[[1, 2, 3]]]]
        expected = (
            "Invalid MultiPolygon:\nValue ([1, 2, 3]) must be a two-dimensional point"
        )
        self._test_for_expected_error(Location, invalid_coords, expected)

        invalid_coords = [[[[{}, {}]]], [[("a", "b")]]]
        expected = "Invalid MultiPolygon:\nBoth values ([{}, {}]) in point must be float or int, Both values (('a', 'b')) in point must be float or int"
        self._test_for_expected_error(Location, invalid_coords, expected)

        invalid_coords = [[[[1, 2], [3, 4]]]]
        expected = (
            "Invalid MultiPolygon:\nLineStrings must start and end at the same point"
        )
        self._test_for_expected_error(Location, invalid_coords, expected)

        Location(loc=[[[[1, 2], [3, 4], [5, 6], [1, 2]]]]).validate()

    def test_indexes_geopoint(self):
        """Ensure that indexes are created automatically for GeoPointFields."""

        class Event(Document):
            title = StringField()
            location = GeoPointField()

        geo_indicies = Event._geo_indices()
        assert geo_indicies == [{"fields": [("location", "2d")]}]

    def test_geopoint_embedded_indexes(self):
        """Ensure that indexes are created automatically for GeoPointFields on
        embedded documents.
        """

        class Venue(EmbeddedDocument):
            location = GeoPointField()
            name = StringField()

        class Event(Document):
            title = StringField()
            venue = EmbeddedDocumentField(Venue)

        geo_indicies = Event._geo_indices()
        assert geo_indicies == [{"fields": [("venue.location", "2d")]}]

    def test_indexes_2dsphere(self):
        """Ensure that indexes are created automatically for GeoPointFields."""

        class Event(Document):
            title = StringField()
            point = PointField()
            line = LineStringField()
            polygon = PolygonField()

        geo_indicies = Event._geo_indices()
        assert {"fields": [("line", "2dsphere")]} in geo_indicies
        assert {"fields": [("polygon", "2dsphere")]} in geo_indicies
        assert {"fields": [("point", "2dsphere")]} in geo_indicies

    def test_indexes_2dsphere_embedded(self):
        """Ensure that indexes are created automatically for GeoPointFields."""

        class Venue(EmbeddedDocument):
            name = StringField()
            point = PointField()
            line = LineStringField()
            polygon = PolygonField()

        class Event(Document):
            title = StringField()
            venue = EmbeddedDocumentField(Venue)

        geo_indicies = Event._geo_indices()
        assert {"fields": [("venue.line", "2dsphere")]} in geo_indicies
        assert {"fields": [("venue.polygon", "2dsphere")]} in geo_indicies
        assert {"fields": [("venue.point", "2dsphere")]} in geo_indicies

    def test_geo_indexes_recursion(self):
        class Location(Document):
            name = StringField()
            location = GeoPointField()

        class Parent(Document):
            name = StringField()
            location = ReferenceField(Location)

        Location.drop_collection()
        Parent.drop_collection()

        Parent(name="Berlin").save()
        info = Parent._get_collection().index_information()
        assert "location_2d" not in info
        info = Location._get_collection().index_information()
        assert "location_2d" in info

        assert len(Parent._geo_indices()) == 0
        assert len(Location._geo_indices()) == 1

    def test_geo_indexes_auto_index(self):
        # Test just listing the fields
        class Log(Document):
            location = PointField(auto_index=False)
            datetime = DateTimeField()

            meta = {"indexes": [[("location", "2dsphere"), ("datetime", 1)]]}

        assert Log._geo_indices() == []

        Log.drop_collection()
        Log.ensure_indexes()

        info = Log._get_collection().index_information()
        assert info["location_2dsphere_datetime_1"]["key"] == [
            ("location", "2dsphere"),
            ("datetime", 1),
        ]

        # Test listing explicitly
        class Log(Document):
            location = PointField(auto_index=False)
            datetime = DateTimeField()

            meta = {
                "indexes": [{"fields": [("location", "2dsphere"), ("datetime", 1)]}]
            }

        assert Log._geo_indices() == []

        Log.drop_collection()
        Log.ensure_indexes()

        info = Log._get_collection().index_information()
        assert info["location_2dsphere_datetime_1"]["key"] == [
            ("location", "2dsphere"),
            ("datetime", 1),
        ]


if __name__ == "__main__":
    unittest.main()
