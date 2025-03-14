import unittest

import pytest

from mongoneo import *
from mongoneo.queryset import QueryFieldList


class TestQueryFieldList:
    def test_empty(self):
        q = QueryFieldList()
        assert not q

        q = QueryFieldList(always_include=["_cls"])
        assert not q

    def test_include_include(self):
        q = QueryFieldList()
        q += QueryFieldList(
            fields=["a", "b"], value=QueryFieldList.ONLY, _only_called=True
        )
        assert q.as_dict() == {"a": 1, "b": 1}
        q += QueryFieldList(fields=["b", "c"], value=QueryFieldList.ONLY)
        assert q.as_dict() == {"a": 1, "b": 1, "c": 1}

    def test_include_exclude(self):
        q = QueryFieldList()
        q += QueryFieldList(fields=["a", "b"], value=QueryFieldList.ONLY)
        assert q.as_dict() == {"a": 1, "b": 1}
        q += QueryFieldList(fields=["b", "c"], value=QueryFieldList.EXCLUDE)
        assert q.as_dict() == {"a": 1}

    def test_exclude_exclude(self):
        q = QueryFieldList()
        q += QueryFieldList(fields=["a", "b"], value=QueryFieldList.EXCLUDE)
        assert q.as_dict() == {"a": 0, "b": 0}
        q += QueryFieldList(fields=["b", "c"], value=QueryFieldList.EXCLUDE)
        assert q.as_dict() == {"a": 0, "b": 0, "c": 0}

    def test_exclude_include(self):
        q = QueryFieldList()
        q += QueryFieldList(fields=["a", "b"], value=QueryFieldList.EXCLUDE)
        assert q.as_dict() == {"a": 0, "b": 0}
        q += QueryFieldList(fields=["b", "c"], value=QueryFieldList.ONLY)
        assert q.as_dict() == {"c": 1}

    def test_always_include(self):
        q = QueryFieldList(always_include=["x", "y"])
        q += QueryFieldList(fields=["a", "b", "x"], value=QueryFieldList.EXCLUDE)
        q += QueryFieldList(fields=["b", "c"], value=QueryFieldList.ONLY)
        assert q.as_dict() == {"x": 1, "y": 1, "c": 1}

    def test_reset(self):
        q = QueryFieldList(always_include=["x", "y"])
        q += QueryFieldList(fields=["a", "b", "x"], value=QueryFieldList.EXCLUDE)
        q += QueryFieldList(fields=["b", "c"], value=QueryFieldList.ONLY)
        assert q.as_dict() == {"x": 1, "y": 1, "c": 1}
        q.reset()
        assert not q
        q += QueryFieldList(fields=["b", "c"], value=QueryFieldList.ONLY)
        assert q.as_dict() == {"x": 1, "y": 1, "b": 1, "c": 1}

    def test_using_a_slice(self):
        q = QueryFieldList()
        q += QueryFieldList(fields=["a"], value={"$slice": 5})
        assert q.as_dict() == {"a": {"$slice": 5}}


class TestOnlyExcludeAll(unittest.TestCase):
    def setUp(self):
        connect(db="mongoneotest")

        class Person(Document):
            name = StringField()
            age = IntField()
            meta = {"allow_inheritance": True}

        Person.drop_collection()
        self.Person = Person

    def test_mixing_only_exclude(self):
        class MyDoc(Document):
            a = StringField()
            b = StringField()
            c = StringField()
            d = StringField()
            e = StringField()
            f = StringField()

        include = ["a", "b", "c", "d", "e"]
        exclude = ["d", "e"]
        only = ["b", "c"]

        qs = MyDoc.objects.fields(**{i: 1 for i in include})
        assert qs._loaded_fields.as_dict() == {"a": 1, "b": 1, "c": 1, "d": 1, "e": 1}
        qs = qs.only(*only)
        assert qs._loaded_fields.as_dict() == {"b": 1, "c": 1}
        qs = qs.exclude(*exclude)
        assert qs._loaded_fields.as_dict() == {"b": 1, "c": 1}

        qs = MyDoc.objects.fields(**{i: 1 for i in include})
        qs = qs.exclude(*exclude)
        assert qs._loaded_fields.as_dict() == {"a": 1, "b": 1, "c": 1}
        qs = qs.only(*only)
        assert qs._loaded_fields.as_dict() == {"b": 1, "c": 1}

        qs = MyDoc.objects.exclude(*exclude)
        qs = qs.fields(**{i: 1 for i in include})
        assert qs._loaded_fields.as_dict() == {"a": 1, "b": 1, "c": 1}
        qs = qs.only(*only)
        assert qs._loaded_fields.as_dict() == {"b": 1, "c": 1}

    def test_slicing(self):
        class MyDoc(Document):
            a = ListField()
            b = ListField()
            c = ListField()
            d = ListField()
            e = ListField()
            f = ListField()

        include = ["a", "b", "c", "d", "e"]
        exclude = ["d", "e"]
        only = ["b", "c"]

        qs = MyDoc.objects.fields(**{i: 1 for i in include})
        qs = qs.exclude(*exclude)
        qs = qs.only(*only)
        qs = qs.fields(slice__b=5)
        assert qs._loaded_fields.as_dict() == {"b": {"$slice": 5}, "c": 1}

        qs = qs.fields(slice__c=[5, 1])
        assert qs._loaded_fields.as_dict() == {
            "b": {"$slice": 5},
            "c": {"$slice": [5, 1]},
        }

        qs = qs.exclude("c")
        assert qs._loaded_fields.as_dict() == {"b": {"$slice": 5}}

    def test_mix_slice_with_other_fields(self):
        class MyDoc(Document):
            a = ListField()
            b = ListField()
            c = ListField()

        qs = MyDoc.objects.fields(a=1, b=0, slice__c=2)
        assert qs._loaded_fields.as_dict() == {"c": {"$slice": 2}, "a": 1}

    def test_only(self):
        """Ensure that QuerySet.only only returns the requested fields."""
        person = self.Person(name="test", age=25)
        person.save()

        obj = self.Person.objects.only("name").get()
        assert obj.name == person.name
        assert obj.age is None

        obj = self.Person.objects.only("age").get()
        assert obj.name is None
        assert obj.age == person.age

        obj = self.Person.objects.only("name", "age").get()
        assert obj.name == person.name
        assert obj.age == person.age

        obj = self.Person.objects.only(*("id", "name")).get()
        assert obj.name == person.name
        assert obj.age is None

        # Check polymorphism still works
        class Employee(self.Person):
            salary = IntField(db_field="wage")

        employee = Employee(name="test employee", age=40, salary=30000)
        employee.save()

        obj = self.Person.objects(id=employee.id).only("age").get()
        assert isinstance(obj, Employee)

        # Check field names are looked up properly
        obj = Employee.objects(id=employee.id).only("salary").get()
        assert obj.salary == employee.salary
        assert obj.name is None

    def test_only_with_subfields(self):
        class User(EmbeddedDocument):
            name = StringField()
            email = StringField()

        class Comment(EmbeddedDocument):
            title = StringField()
            text = StringField()

        class VariousData(EmbeddedDocument):
            some = BooleanField()

        class BlogPost(Document):
            content = StringField()
            author = EmbeddedDocumentField(User)
            comments = ListField(EmbeddedDocumentField(Comment))
            various = MapField(field=EmbeddedDocumentField(VariousData))

        BlogPost.drop_collection()

        post = BlogPost(
            content="Had a good coffee today...",
            various={"test_dynamic": {"some": True}},
        )
        post.author = User(name="Test User")
        post.comments = [
            Comment(title="I aggree", text="Great post!"),
            Comment(title="Coffee", text="I hate coffee"),
        ]
        post.save()

        obj = BlogPost.objects.only("author.name").get()
        assert obj.content is None
        assert obj.author.email is None
        assert obj.author.name == "Test User"
        assert obj.comments == []

        obj = BlogPost.objects.only("various.test_dynamic.some").get()
        assert obj.various["test_dynamic"].some is True

        obj = BlogPost.objects.only("content", "comments.title").get()
        assert obj.content == "Had a good coffee today..."
        assert obj.author is None
        assert obj.comments[0].title == "I aggree"
        assert obj.comments[1].title == "Coffee"
        assert obj.comments[0].text is None
        assert obj.comments[1].text is None

        obj = BlogPost.objects.only("comments").get()
        assert obj.content is None
        assert obj.author is None
        assert obj.comments[0].title == "I aggree"
        assert obj.comments[1].title == "Coffee"
        assert obj.comments[0].text == "Great post!"
        assert obj.comments[1].text == "I hate coffee"

        BlogPost.drop_collection()

    def test_exclude(self):
        class User(EmbeddedDocument):
            name = StringField()
            email = StringField()

        class Comment(EmbeddedDocument):
            title = StringField()
            text = StringField()

        class BlogPost(Document):
            content = StringField()
            author = EmbeddedDocumentField(User)
            comments = ListField(EmbeddedDocumentField(Comment))

        BlogPost.drop_collection()

        post = BlogPost(content="Had a good coffee today...")
        post.author = User(name="Test User")
        post.comments = [
            Comment(title="I aggree", text="Great post!"),
            Comment(title="Coffee", text="I hate coffee"),
        ]
        post.save()

        obj = BlogPost.objects.exclude("author", "comments.text").get()
        assert obj.author is None
        assert obj.content == "Had a good coffee today..."
        assert obj.comments[0].title == "I aggree"
        assert obj.comments[0].text is None

        BlogPost.drop_collection()

    def test_exclude_only_combining(self):
        class Attachment(EmbeddedDocument):
            name = StringField()
            content = StringField()

        class Email(Document):
            sender = StringField()
            to = StringField()
            subject = StringField()
            body = StringField()
            content_type = StringField()
            attachments = ListField(EmbeddedDocumentField(Attachment))

        Email.drop_collection()
        email = Email(
            sender="me",
            to="you",
            subject="From Russia with Love",
            body="Hello!",
            content_type="text/plain",
        )
        email.attachments = [
            Attachment(name="file1.doc", content="ABC"),
            Attachment(name="file2.doc", content="XYZ"),
        ]
        email.save()

        obj = Email.objects.exclude("content_type").exclude("body").get()
        assert obj.sender == "me"
        assert obj.to == "you"
        assert obj.subject == "From Russia with Love"
        assert obj.body is None
        assert obj.content_type is None

        obj = Email.objects.only("sender", "to").exclude("body", "sender").get()
        assert obj.sender is None
        assert obj.to == "you"
        assert obj.subject is None
        assert obj.body is None
        assert obj.content_type is None

        obj = (
            Email.objects.exclude("attachments.content")
            .exclude("body")
            .only("to", "attachments.name")
            .get()
        )
        assert obj.attachments[0].name == "file1.doc"
        assert obj.attachments[0].content is None
        assert obj.sender is None
        assert obj.to == "you"
        assert obj.subject is None
        assert obj.body is None
        assert obj.content_type is None

        Email.drop_collection()

    def test_all_fields(self):
        class Email(Document):
            sender = StringField()
            to = StringField()
            subject = StringField()
            body = StringField()
            content_type = StringField()

        Email.drop_collection()

        email = Email(
            sender="me",
            to="you",
            subject="From Russia with Love",
            body="Hello!",
            content_type="text/plain",
        )
        email.save()

        obj = (
            Email.objects.exclude("content_type", "body")
            .only("to", "body")
            .all_fields()
            .get()
        )
        assert obj.sender == "me"
        assert obj.to == "you"
        assert obj.subject == "From Russia with Love"
        assert obj.body == "Hello!"
        assert obj.content_type == "text/plain"

        Email.drop_collection()

    def test_slicing_fields(self):
        """Ensure that query slicing an array works."""

        class Numbers(Document):
            n = ListField(IntField())

        Numbers.drop_collection()

        numbers = Numbers(n=[0, 1, 2, 3, 4, 5, -5, -4, -3, -2, -1])
        numbers.save()

        # first three
        numbers = Numbers.objects.fields(slice__n=3).get()
        assert numbers.n == [0, 1, 2]

        # last three
        numbers = Numbers.objects.fields(slice__n=-3).get()
        assert numbers.n == [-3, -2, -1]

        # skip 2, limit 3
        numbers = Numbers.objects.fields(slice__n=[2, 3]).get()
        assert numbers.n == [2, 3, 4]

        # skip to fifth from last, limit 4
        numbers = Numbers.objects.fields(slice__n=[-5, 4]).get()
        assert numbers.n == [-5, -4, -3, -2]

        # skip to fifth from last, limit 10
        numbers = Numbers.objects.fields(slice__n=[-5, 10]).get()
        assert numbers.n == [-5, -4, -3, -2, -1]

        # skip to fifth from last, limit 10 dict method
        numbers = Numbers.objects.fields(n={"$slice": [-5, 10]}).get()
        assert numbers.n == [-5, -4, -3, -2, -1]

    def test_slicing_nested_fields(self):
        """Ensure that query slicing an embedded array works."""

        class EmbeddedNumber(EmbeddedDocument):
            n = ListField(IntField())

        class Numbers(Document):
            embedded = EmbeddedDocumentField(EmbeddedNumber)

        Numbers.drop_collection()

        numbers = Numbers()
        numbers.embedded = EmbeddedNumber(n=[0, 1, 2, 3, 4, 5, -5, -4, -3, -2, -1])
        numbers.save()

        # first three
        numbers = Numbers.objects.fields(slice__embedded__n=3).get()
        assert numbers.embedded.n == [0, 1, 2]

        # last three
        numbers = Numbers.objects.fields(slice__embedded__n=-3).get()
        assert numbers.embedded.n == [-3, -2, -1]

        # skip 2, limit 3
        numbers = Numbers.objects.fields(slice__embedded__n=[2, 3]).get()
        assert numbers.embedded.n == [2, 3, 4]

        # skip to fifth from last, limit 4
        numbers = Numbers.objects.fields(slice__embedded__n=[-5, 4]).get()
        assert numbers.embedded.n == [-5, -4, -3, -2]

        # skip to fifth from last, limit 10
        numbers = Numbers.objects.fields(slice__embedded__n=[-5, 10]).get()
        assert numbers.embedded.n == [-5, -4, -3, -2, -1]

        # skip to fifth from last, limit 10 dict method
        numbers = Numbers.objects.fields(embedded__n={"$slice": [-5, 10]}).get()
        assert numbers.embedded.n == [-5, -4, -3, -2, -1]

    def test_exclude_from_subclasses_docs(self):
        class Base(Document):
            username = StringField()

            meta = {"allow_inheritance": True}

        class Anon(Base):
            anon = BooleanField()

        class User(Base):
            password = StringField()
            wibble = StringField()

        Base.drop_collection()
        User(username="mongodb", password="secret").save()

        user = Base.objects().exclude("password", "wibble").first()
        assert user.password is None

        with pytest.raises(LookUpError):
            Base.objects.exclude("made_up")

    def test_gt_gte_lt_lte_ne_operator_with_list(self):
        class Family(Document):
            ages = ListField(field=FloatField())

        Family.drop_collection()

        Family(ages=[1.0, 2.0]).save()
        Family(ages=[]).save()

        qs = list(Family.objects(ages__gt=[1.0]))
        assert len(qs) == 1
        assert qs[0].ages == [1.0, 2.0]

        qs = list(Family.objects(ages__gt=[1.0, 1.99]))
        assert len(qs) == 1
        assert qs[0].ages == [1.0, 2.0]

        qs = list(Family.objects(ages__gt=[]))
        assert len(qs) == 1
        assert qs[0].ages == [1.0, 2.0]

        qs = list(Family.objects(ages__gte=[1.0, 2.0]))
        assert len(qs) == 1
        assert qs[0].ages == [1.0, 2.0]

        qs = list(Family.objects(ages__lt=[1.0]))
        assert len(qs) == 1
        assert qs[0].ages == []

        qs = list(Family.objects(ages__lte=[5.0]))
        assert len(qs) == 2

        qs = list(Family.objects(ages__ne=[5.0]))
        assert len(qs) == 2

        qs = list(Family.objects(ages__ne=[]))
        assert len(qs) == 1
        assert qs[0].ages == [1.0, 2.0]


if __name__ == "__main__":
    unittest.main()
