import unittest

from pymongo import MongoClient, ReadPreference

import mongoneo
from mongoneo.connection import ConnectionFailure

CONN_CLASS = MongoClient
READ_PREF = ReadPreference.SECONDARY


class ConnectionTest(unittest.TestCase):
    def setUp(self):
        mongoneo.connection._connection_settings = {}
        mongoneo.connection._connections = {}
        mongoneo.connection._dbs = {}

    def tearDown(self):
        mongoneo.connection._connection_settings = {}
        mongoneo.connection._connections = {}
        mongoneo.connection._dbs = {}

    def test_replicaset_uri_passes_read_preference(self):
        """Requires a replica set called "rs" on port 27017"""
        try:
            conn = mongoneo.connect(
                db="mongoneotest",
                host="mongodb://localhost/mongoneotest?replicaSet=rs",
                read_preference=READ_PREF,
            )
        except ConnectionFailure:
            return

        if not isinstance(conn, CONN_CLASS):
            # really???
            return

        assert conn.read_preference == READ_PREF


if __name__ == "__main__":
    unittest.main()
