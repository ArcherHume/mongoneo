# MongoNeo

> A next-generation Python ORM for working with MongoDB


**Repository:** [https://github.com/MongoNeo/mongoneo](https://github.com/ArcherHume/mongoneo)
**Author:** Archer Hume (https://github.com/ArcherHume)
**Disclaimer:** This is a heavily modified fork of MongoEngine, and is still in early development. **NOT YET ON PIP**

## Supported MongoDB Versions

MongoNeo is currently tested against MongoDB v3.6, v4.0, v4.4, v5.0, v6.0 and v7.0. Future versions
should be supported as well, but aren't actively tested at the moment. Make
sure to open an issue or submit a pull request if you experience any problems
with a more recent MongoDB versions.

## Installation

We recommend the use of [virtualenv](https://virtualenv.pypa.io/) and of
[pip](https://pip.pypa.io/). You can then use `python -m pip install -U mongoneo`.
You may also have [setuptools](http://peak.telecommunity.com/DevCenter/setuptools)
and thus you can use `easy_install -U mongoneo`. Another option is
[pipenv](https://docs.pipenv.org/). You can then use `pipenv install mongoneo`
to both create the virtual environment and install the package. Otherwise, you can
download the source from [GitHub](https://github.com/ArcherHume/mongoneo) and
run `python setup.py install`.

## Dependencies

All of the dependencies can easily be installed via [pip](https://pip.pypa.io/).
At the very least, you'll need these two packages to use MongoNeo:

- pymongo>=3.4

If you utilize a `DateTimeField`, you might also use a more flexible date parser:

- dateutil>=2.1.0

If you need to use an `ImageField` or `ImageGridFsProxy`:

- Pillow>=7.0.0

If you need to use signals:

- blinker>=1.3

## Examples

Some simple examples of what MongoNeo code looks like:

```python
from mongoneo import *
connect('mydb')

@model(allow_inheritance=True)
class BlogPost:
    title = StringField(required=True, max_length=200)
    posted = DateTimeField(default=datetime.datetime.utcnow)
    published = BooleanField(default=False)
    tags = ListField(StringField(max_length=50))

class TextPost(BlogPost):
    content = StringField(required=True)

class LinkPost(BlogPost):
    url = StringField(required=True)

# Create a text-based post
>>> post1 = TextPost(title='Using MongoNeo', content='See the tutorial')
>>> post1.tags = ['mongodb', 'mongoneo']
>>> post1.save()

# Create a link-based post
>>> post2 = LinkPost(title='MongoNeo', url='[hmarr.com/mongoneo](https://github.com/ArcherHume/mongoneo)')
>>> post2.tags = ['mongoneo', 'github']
>>> post2.save()

# Publish Post 2
>>> post2.published = False
>>> post2.save()

# Iterate over all published posts using the BlogPost superclass
>>> for post in BlogPost.query.where(BlogPost.published == True):
...     print('===', post.title, '===')
...     if isinstance(post, TextPost):
...         print(post.content)
...     elif isinstance(post, LinkPost):
...         print('Link:', post.url)
...

# Count all blog posts and its subtypes
>>> BlogPost.objects.count()
2
>>> TextPost.objects.count()
1
>>> LinkPost.objects.count()
1

# Count tagged posts
>>> BlogPost.objects(tags='mongoneo').count()
2
>>> BlogPost.objects(tags='mongodb').count()
1
```

## Tests

To run the test suite, ensure you are running a local instance of MongoDB on
the standard port and have `pytest` installed. Then, run `pytest tests/`.

To run the test suite on every supported Python and PyMongo version, you can
use `tox`. You'll need to make sure you have each supported Python version
installed in your environment and then:

```shell
# Install tox
$ python -m pip install tox
# Run the test suites
$ tox
```