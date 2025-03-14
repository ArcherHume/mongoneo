import timeit


def main():
    setup = """
from pymongo import MongoClient

connection = MongoClient(w=1)
connection.drop_database('mongoneo_benchmark_test')
"""

    stmt = """
db = connection.mongoneo_benchmark_test
noddy = db.noddy

for i in range(10000):
    example = {'fields': {}}
    for j in range(20):
        example['fields']["key"+str(j)] = "value "+str(j)

    noddy.insert_one(example)

myNoddys = noddy.find()
[n for n in myNoddys]  # iterate
"""

    print("-" * 100)
    print('PyMongo: Creating 10000 dictionaries (write_concern={"w": 1}).')
    t = timeit.Timer(stmt=stmt, setup=setup)
    print(f"{t.timeit(1)}s")

    stmt = """
from pymongo import WriteConcern

db = connection.mongoneo_benchmark_test
noddy = db.noddy.with_options(write_concern=WriteConcern(w=0))

for i in range(10000):
    example = {'fields': {}}
    for j in range(20):
        example['fields']["key"+str(j)] = "value "+str(j)

    noddy.insert_one(example)

myNoddys = noddy.find()
[n for n in myNoddys]  # iterate
"""

    print("-" * 100)
    print('PyMongo: Creating 10000 dictionaries (write_concern={"w": 0}).')
    t = timeit.Timer(stmt=stmt, setup=setup)
    print(f"{t.timeit(1)}s")

    setup = """
from pymongo import MongoClient

connection = MongoClient()
connection.drop_database('mongoneo_benchmark_test')
connection.close()

from mongoneo import Document, DictField, connect
connect("mongoneo_benchmark_test", w=1)

class Noddy(Document):
    fields = DictField()
"""

    stmt = """
for i in range(10000):
    noddy = Noddy()
    for j in range(20):
        noddy.fields["key"+str(j)] = "value "+str(j)
    noddy.save()

myNoddys = Noddy.objects()
[n for n in myNoddys]  # iterate
"""

    print("-" * 100)
    print('MongoNeo: Creating 10000 dictionaries (write_concern={"w": 1}).')
    t = timeit.Timer(stmt=stmt, setup=setup)
    print(f"{t.timeit(1)}s")

    stmt = """
for i in range(10000):
    noddy = Noddy()
    fields = {}
    for j in range(20):
        fields["key"+str(j)] = "value "+str(j)
    noddy.fields = fields
    noddy.save()

myNoddys = Noddy.objects()
[n for n in myNoddys]  # iterate
"""

    print("-" * 100)
    print("MongoNeo: Creating 10000 dictionaries (using a single field assignment).")
    t = timeit.Timer(stmt=stmt, setup=setup)
    print(f"{t.timeit(1)}s")

    stmt = """
for i in range(10000):
    noddy = Noddy()
    for j in range(20):
        noddy.fields["key"+str(j)] = "value "+str(j)
    noddy.save(write_concern={"w": 0})

myNoddys = Noddy.objects()
[n for n in myNoddys] # iterate
"""

    print("-" * 100)
    print('MongoNeo: Creating 10000 dictionaries (write_concern={"w": 0}).')
    t = timeit.Timer(stmt=stmt, setup=setup)
    print(f"{t.timeit(1)}s")

    stmt = """
for i in range(10000):
    noddy = Noddy()
    for j in range(20):
        noddy.fields["key"+str(j)] = "value "+str(j)
    noddy.save(write_concern={"w": 0}, validate=False)

myNoddys = Noddy.objects()
[n for n in myNoddys] # iterate
"""

    print("-" * 100)
    print(
        'MongoNeo: Creating 10000 dictionaries (write_concern={"w": 0}, validate=False).'
    )
    t = timeit.Timer(stmt=stmt, setup=setup)
    print(f"{t.timeit(1)}s")

    stmt = """
for i in range(10000):
    noddy = Noddy()
    for j in range(20):
        noddy.fields["key"+str(j)] = "value "+str(j)
    noddy.save(force_insert=True, write_concern={"w": 0}, validate=False)

myNoddys = Noddy.objects()
[n for n in myNoddys] # iterate
"""

    print("-" * 100)
    print(
        'MongoNeo: Creating 10000 dictionaries (force_insert=True, write_concern={"w": 0}, validate=False).'
    )
    t = timeit.Timer(stmt=stmt, setup=setup)
    print(f"{t.timeit(1)}s")


if __name__ == "__main__":
    main()
