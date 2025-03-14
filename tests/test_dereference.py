import unittest

from bson import DBRef, ObjectId

from mongoneo import *
from mongoneo.context_managers import query_counter


class FieldTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = connect(db="mongoneotest")

    @classmethod
    def tearDownClass(cls):
        cls.db.drop_database("mongoneotest")

    def test_list_item_dereference(self):
        """Ensure that DBRef items in ListFields are dereferenced."""

        class User(Document):
            name = StringField()

        class Group(Document):
            members = ListField(ReferenceField(User))

        User.drop_collection()
        Group.drop_collection()

        for i in range(1, 51):
            user = User(name="user %s" % i)
            user.save()

        group = Group(members=User.objects)
        group.save()

        group = Group(members=User.objects)
        group.save()

        with query_counter() as q:
            assert q == 0

            group_obj = Group.objects.first()
            assert q == 1

            len(group_obj._data["members"])
            assert q == 1

            len(group_obj.members)
            assert q == 2

            _ = [m for m in group_obj.members]
            assert q == 2

        # Document select_related
        with query_counter() as q:
            assert q == 0

            group_obj = Group.objects.first().select_related()
            assert q == 2
            _ = [m for m in group_obj.members]
            assert q == 2

        # Queryset select_related
        with query_counter() as q:
            assert q == 0
            group_objs = Group.objects.select_related()
            assert q == 2
            for group_obj in group_objs:
                _ = [m for m in group_obj.members]
                assert q == 2

        User.drop_collection()
        Group.drop_collection()

    def test_list_item_dereference_dref_false(self):
        """Ensure that DBRef items in ListFields are dereferenced."""

        class User(Document):
            name = StringField()

        class Group(Document):
            members = ListField(ReferenceField(User, dbref=False))

        User.drop_collection()
        Group.drop_collection()

        for i in range(1, 51):
            user = User(name="user %s" % i)
            user.save()

        group = Group(members=User.objects)
        group.save()
        group.reload()  # Confirm reload works

        with query_counter() as q:
            assert q == 0

            group_obj = Group.objects.first()
            assert q == 1

            _ = [m for m in group_obj.members]
            assert q == 2
            assert group_obj._data["members"]._dereferenced

            # verifies that no additional queries gets executed
            # if we re-iterate over the ListField once it is
            # dereferenced
            _ = [m for m in group_obj.members]
            assert q == 2
            assert group_obj._data["members"]._dereferenced

        # Document select_related
        with query_counter() as q:
            assert q == 0

            group_obj = Group.objects.first().select_related()

            assert q == 2
            _ = [m for m in group_obj.members]
            assert q == 2

        # Queryset select_related
        with query_counter() as q:
            assert q == 0
            group_objs = Group.objects.select_related()
            assert q == 2
            for group_obj in group_objs:
                _ = [m for m in group_obj.members]
                assert q == 2

    def test_list_item_dereference_orphan_dbref(self):
        """Ensure that orphan DBRef items in ListFields are dereferenced."""

        class User(Document):
            name = StringField()

        class Group(Document):
            members = ListField(ReferenceField(User, dbref=False))

        User.drop_collection()
        Group.drop_collection()

        for i in range(1, 51):
            user = User(name="user %s" % i)
            user.save()

        group = Group(members=User.objects)
        group.save()
        group.reload()  # Confirm reload works

        # Delete one User so one of the references in the
        # Group.members list is an orphan DBRef
        User.objects[0].delete()
        with query_counter() as q:
            assert q == 0

            group_obj = Group.objects.first()
            assert q == 1

            _ = [m for m in group_obj.members]
            assert q == 2
            assert group_obj._data["members"]._dereferenced

            # verifies that no additional queries gets executed
            # if we re-iterate over the ListField once it is
            # dereferenced
            _ = [m for m in group_obj.members]
            assert q == 2
            assert group_obj._data["members"]._dereferenced

        User.drop_collection()
        Group.drop_collection()

    def test_list_item_dereference_dref_false_stores_as_type(self):
        """Ensure that DBRef items are stored as their type"""

        class User(Document):
            my_id = IntField(primary_key=True)
            name = StringField()

        class Group(Document):
            members = ListField(ReferenceField(User, dbref=False))

        User.drop_collection()
        Group.drop_collection()

        user = User(my_id=1, name="user 1").save()

        Group(members=User.objects).save()
        group = Group.objects.first()

        assert Group._get_collection().find_one()["members"] == [1]
        assert group.members == [user]

    def test_handle_old_style_references(self):
        """Ensure that DBRef items in ListFields are dereferenced."""

        class User(Document):
            name = StringField()

        class Group(Document):
            members = ListField(ReferenceField(User, dbref=True))

        User.drop_collection()
        Group.drop_collection()

        for i in range(1, 26):
            user = User(name="user %s" % i)
            user.save()

        group = Group(members=User.objects)
        group.save()

        group = Group._get_collection().find_one()

        # Update the model to change the reference
        class Group(Document):
            members = ListField(ReferenceField(User, dbref=False))

        group = Group.objects.first()
        group.members.append(User(name="String!").save())
        group.save()

        group = Group.objects.first()
        assert group.members[0].name == "user 1"
        assert group.members[-1].name == "String!"

    def test_migrate_references(self):
        """Example of migrating ReferenceField storage"""

        # Create some sample data
        class User(Document):
            name = StringField()

        class Group(Document):
            author = ReferenceField(User, dbref=True)
            members = ListField(ReferenceField(User, dbref=True))

        User.drop_collection()
        Group.drop_collection()

        user = User(name="Ross").save()
        group = Group(author=user, members=[user]).save()

        raw_data = Group._get_collection().find_one()
        assert isinstance(raw_data["author"], DBRef)
        assert isinstance(raw_data["members"][0], DBRef)
        group = Group.objects.first()

        assert group.author == user
        assert group.members == [user]

        # Migrate the model definition
        class Group(Document):
            author = ReferenceField(User, dbref=False)
            members = ListField(ReferenceField(User, dbref=False))

        # Migrate the data
        for g in Group.objects():
            # Explicitly mark as changed so resets
            g._mark_as_changed("author")
            g._mark_as_changed("members")
            g.save()

        group = Group.objects.first()
        assert group.author == user
        assert group.members == [user]

        raw_data = Group._get_collection().find_one()
        assert isinstance(raw_data["author"], ObjectId)
        assert isinstance(raw_data["members"][0], ObjectId)

    def test_recursive_reference(self):
        """Ensure that ReferenceFields can reference their own documents."""

        class Employee(Document):
            name = StringField()
            boss = ReferenceField("self")
            friends = ListField(ReferenceField("self"))

        Employee.drop_collection()

        bill = Employee(name="Bill Lumbergh")
        bill.save()

        michael = Employee(name="Michael Bolton")
        michael.save()

        samir = Employee(name="Samir Nagheenanajar")
        samir.save()

        friends = [michael, samir]
        peter = Employee(name="Peter Gibbons", boss=bill, friends=friends)
        peter.save()

        Employee(name="Funky Gibbon", boss=bill, friends=friends).save()
        Employee(name="Funky Gibbon", boss=bill, friends=friends).save()
        Employee(name="Funky Gibbon", boss=bill, friends=friends).save()

        with query_counter() as q:
            assert q == 0

            peter = Employee.objects.with_id(peter.id)
            assert q == 1

            peter.boss
            assert q == 2

            peter.friends
            assert q == 3

        # Document select_related
        with query_counter() as q:
            assert q == 0

            peter = Employee.objects.with_id(peter.id).select_related()
            assert q == 2

            assert peter.boss == bill
            assert q == 2

            assert peter.friends == friends
            assert q == 2

        # Queryset select_related
        with query_counter() as q:
            assert q == 0

            employees = Employee.objects(boss=bill).select_related()
            assert q == 2

            for employee in employees:
                assert employee.boss == bill
                assert q == 2

                assert employee.friends == friends
                assert q == 2

    def test_list_of_lists_of_references(self):
        class User(Document):
            name = StringField()

        class Post(Document):
            user_lists = ListField(ListField(ReferenceField(User)))

        class SimpleList(Document):
            users = ListField(ReferenceField(User))

        User.drop_collection()
        Post.drop_collection()
        SimpleList.drop_collection()

        u1 = User.objects.create(name="u1")
        u2 = User.objects.create(name="u2")
        u3 = User.objects.create(name="u3")

        SimpleList.objects.create(users=[u1, u2, u3])
        assert SimpleList.objects.all()[0].users == [u1, u2, u3]

        Post.objects.create(user_lists=[[u1, u2], [u3]])
        assert Post.objects.all()[0].user_lists == [[u1, u2], [u3]]

    def test_circular_reference(self):
        """Ensure you can handle circular references"""

        class Relation(EmbeddedDocument):
            name = StringField()
            person = ReferenceField("Person")

        class Person(Document):
            name = StringField()
            relations = ListField(EmbeddedDocumentField("Relation"))

            def __repr__(self):
                return "<Person: %s>" % self.name

        Person.drop_collection()
        mother = Person(name="Mother")
        daughter = Person(name="Daughter")

        mother.save()
        daughter.save()

        daughter_rel = Relation(name="Daughter", person=daughter)
        mother.relations.append(daughter_rel)
        mother.save()

        mother_rel = Relation(name="Daughter", person=mother)
        self_rel = Relation(name="Self", person=daughter)
        daughter.relations.append(mother_rel)
        daughter.relations.append(self_rel)
        daughter.save()

        assert "[<Person: Mother>, <Person: Daughter>]" == "%s" % Person.objects()

    def test_circular_reference_on_self(self):
        """Ensure you can handle circular references"""

        class Person(Document):
            name = StringField()
            relations = ListField(ReferenceField("self"))

            def __repr__(self):
                return "<Person: %s>" % self.name

        Person.drop_collection()
        mother = Person(name="Mother")
        daughter = Person(name="Daughter")

        mother.save()
        daughter.save()

        mother.relations.append(daughter)
        mother.save()

        daughter.relations.append(mother)
        daughter.relations.append(daughter)
        assert daughter._get_changed_fields() == ["relations"]
        daughter.save()

        assert "[<Person: Mother>, <Person: Daughter>]" == "%s" % Person.objects()

    def test_circular_tree_reference(self):
        """Ensure you can handle circular references with more than one level"""

        class Other(EmbeddedDocument):
            name = StringField()
            friends = ListField(ReferenceField("Person"))

        class Person(Document):
            name = StringField()
            other = EmbeddedDocumentField(Other, default=lambda: Other())

            def __repr__(self):
                return "<Person: %s>" % self.name

        Person.drop_collection()
        paul = Person(name="Paul").save()
        maria = Person(name="Maria").save()
        julia = Person(name="Julia").save()
        anna = Person(name="Anna").save()

        paul.other.friends = [maria, julia, anna]
        paul.other.name = "Paul's friends"
        paul.save()

        maria.other.friends = [paul, julia, anna]
        maria.other.name = "Maria's friends"
        maria.save()

        julia.other.friends = [paul, maria, anna]
        julia.other.name = "Julia's friends"
        julia.save()

        anna.other.friends = [paul, maria, julia]
        anna.other.name = "Anna's friends"
        anna.save()

        assert (
            "[<Person: Paul>, <Person: Maria>, <Person: Julia>, <Person: Anna>]"
            == "%s" % Person.objects()
        )

    def test_generic_reference(self):
        class UserA(Document):
            name = StringField()

        class UserB(Document):
            name = StringField()

        class UserC(Document):
            name = StringField()

        class Group(Document):
            members = ListField(GenericReferenceField())

        UserA.drop_collection()
        UserB.drop_collection()
        UserC.drop_collection()
        Group.drop_collection()

        members = []
        for i in range(1, 51):
            a = UserA(name="User A %s" % i)
            a.save()

            b = UserB(name="User B %s" % i)
            b.save()

            c = UserC(name="User C %s" % i)
            c.save()

            members += [a, b, c]

        group = Group(members=members)
        group.save()

        group = Group(members=members)
        group.save()

        with query_counter() as q:
            assert q == 0

            group_obj = Group.objects.first()
            assert q == 1

            _ = [m for m in group_obj.members]
            assert q == 4

            _ = [m for m in group_obj.members]
            assert q == 4

            for m in group_obj.members:
                assert "User" in m.__class__.__name__

        # Document select_related
        with query_counter() as q:
            assert q == 0

            group_obj = Group.objects.first().select_related()
            assert q == 4

            _ = [m for m in group_obj.members]
            assert q == 4

            _ = [m for m in group_obj.members]
            assert q == 4

            for m in group_obj.members:
                assert "User" in m.__class__.__name__

        # Queryset select_related
        with query_counter() as q:
            assert q == 0

            group_objs = Group.objects.select_related()
            assert q == 4

            for group_obj in group_objs:
                _ = [m for m in group_obj.members]
                assert q == 4

                _ = [m for m in group_obj.members]
                assert q == 4

                for m in group_obj.members:
                    assert "User" in m.__class__.__name__

    def test_generic_reference_orphan_dbref(self):
        """Ensure that generic orphan DBRef items in ListFields are dereferenced."""

        class UserA(Document):
            name = StringField()

        class UserB(Document):
            name = StringField()

        class UserC(Document):
            name = StringField()

        class Group(Document):
            members = ListField(GenericReferenceField())

        UserA.drop_collection()
        UserB.drop_collection()
        UserC.drop_collection()
        Group.drop_collection()

        members = []
        for i in range(1, 51):
            a = UserA(name="User A %s" % i)
            a.save()

            b = UserB(name="User B %s" % i)
            b.save()

            c = UserC(name="User C %s" % i)
            c.save()

            members += [a, b, c]

        group = Group(members=members)
        group.save()

        # Delete one UserA instance so that there is
        # an orphan DBRef in the GenericReference ListField
        UserA.objects[0].delete()
        with query_counter() as q:
            assert q == 0

            group_obj = Group.objects.first()
            assert q == 1

            _ = [m for m in group_obj.members]
            assert q == 4
            assert group_obj._data["members"]._dereferenced

            _ = [m for m in group_obj.members]
            assert q == 4
            assert group_obj._data["members"]._dereferenced

        UserA.drop_collection()
        UserB.drop_collection()
        UserC.drop_collection()
        Group.drop_collection()

    def test_list_field_complex(self):
        class UserA(Document):
            name = StringField()

        class UserB(Document):
            name = StringField()

        class UserC(Document):
            name = StringField()

        class Group(Document):
            members = ListField()

        UserA.drop_collection()
        UserB.drop_collection()
        UserC.drop_collection()
        Group.drop_collection()

        members = []
        for i in range(1, 51):
            a = UserA(name="User A %s" % i)
            a.save()

            b = UserB(name="User B %s" % i)
            b.save()

            c = UserC(name="User C %s" % i)
            c.save()

            members += [a, b, c]

        group = Group(members=members)
        group.save()

        group = Group(members=members)
        group.save()

        with query_counter() as q:
            assert q == 0

            group_obj = Group.objects.first()
            assert q == 1

            _ = [m for m in group_obj.members]
            assert q == 4

            _ = [m for m in group_obj.members]
            assert q == 4

            for m in group_obj.members:
                assert "User" in m.__class__.__name__

        # Document select_related
        with query_counter() as q:
            assert q == 0

            group_obj = Group.objects.first().select_related()
            assert q == 4

            _ = [m for m in group_obj.members]
            assert q == 4

            _ = [m for m in group_obj.members]
            assert q == 4

            for m in group_obj.members:
                assert "User" in m.__class__.__name__

        # Queryset select_related
        with query_counter() as q:
            assert q == 0

            group_objs = Group.objects.select_related()
            assert q == 4

            for group_obj in group_objs:
                _ = [m for m in group_obj.members]
                assert q == 4

                _ = [m for m in group_obj.members]
                assert q == 4

                for m in group_obj.members:
                    assert "User" in m.__class__.__name__

        UserA.drop_collection()
        UserB.drop_collection()
        UserC.drop_collection()
        Group.drop_collection()

    def test_map_field_reference(self):
        class User(Document):
            name = StringField()

        class Group(Document):
            members = MapField(ReferenceField(User))

        User.drop_collection()
        Group.drop_collection()

        members = []
        for i in range(1, 51):
            user = User(name="user %s" % i)
            user.save()
            members.append(user)

        group = Group(members={str(u.id): u for u in members})
        group.save()

        group = Group(members={str(u.id): u for u in members})
        group.save()

        with query_counter() as q:
            assert q == 0

            group_obj = Group.objects.first()
            assert q == 1

            _ = [m for m in group_obj.members]
            assert q == 2

            for _, m in group_obj.members.items():
                assert isinstance(m, User)

        # Document select_related
        with query_counter() as q:
            assert q == 0

            group_obj = Group.objects.first().select_related()
            assert q == 2

            _ = [m for m in group_obj.members]
            assert q == 2

            for k, m in group_obj.members.items():
                assert isinstance(m, User)

        # Queryset select_related
        with query_counter() as q:
            assert q == 0

            group_objs = Group.objects.select_related()
            assert q == 2

            for group_obj in group_objs:
                _ = [m for m in group_obj.members]
                assert q == 2

                for k, m in group_obj.members.items():
                    assert isinstance(m, User)

        User.drop_collection()
        Group.drop_collection()

    def test_dict_field(self):
        class UserA(Document):
            name = StringField()

        class UserB(Document):
            name = StringField()

        class UserC(Document):
            name = StringField()

        class Group(Document):
            members = DictField()

        UserA.drop_collection()
        UserB.drop_collection()
        UserC.drop_collection()
        Group.drop_collection()

        members = []
        for i in range(1, 51):
            a = UserA(name="User A %s" % i)
            a.save()

            b = UserB(name="User B %s" % i)
            b.save()

            c = UserC(name="User C %s" % i)
            c.save()

            members += [a, b, c]

        group = Group(members={str(u.id): u for u in members})
        group.save()
        group = Group(members={str(u.id): u for u in members})
        group.save()

        with query_counter() as q:
            assert q == 0

            group_obj = Group.objects.first()
            assert q == 1

            _ = [m for m in group_obj.members]
            assert q == 4

            _ = [m for m in group_obj.members]
            assert q == 4

            for k, m in group_obj.members.items():
                assert "User" in m.__class__.__name__

        # Document select_related
        with query_counter() as q:
            assert q == 0

            group_obj = Group.objects.first().select_related()
            assert q == 4

            _ = [m for m in group_obj.members]
            assert q == 4

            _ = [m for m in group_obj.members]
            assert q == 4

            for k, m in group_obj.members.items():
                assert "User" in m.__class__.__name__

        # Queryset select_related
        with query_counter() as q:
            assert q == 0

            group_objs = Group.objects.select_related()
            assert q == 4

            for group_obj in group_objs:
                _ = [m for m in group_obj.members]
                assert q == 4

                _ = [m for m in group_obj.members]
                assert q == 4

                for k, m in group_obj.members.items():
                    assert "User" in m.__class__.__name__

        Group.objects.delete()
        Group().save()

        with query_counter() as q:
            assert q == 0

            group_obj = Group.objects.first()
            assert q == 1

            _ = [m for m in group_obj.members]
            assert q == 1
            assert group_obj.members == {}

        UserA.drop_collection()
        UserB.drop_collection()
        UserC.drop_collection()
        Group.drop_collection()

    def test_dict_field_no_field_inheritance(self):
        class UserA(Document):
            name = StringField()
            meta = {"allow_inheritance": False}

        class Group(Document):
            members = DictField()

        UserA.drop_collection()
        Group.drop_collection()

        members = []
        for i in range(1, 51):
            a = UserA(name="User A %s" % i)
            a.save()

            members += [a]

        group = Group(members={str(u.id): u for u in members})
        group.save()

        group = Group(members={str(u.id): u for u in members})
        group.save()

        with query_counter() as q:
            assert q == 0

            group_obj = Group.objects.first()
            assert q == 1

            _ = [m for m in group_obj.members]
            assert q == 2

            _ = [m for m in group_obj.members]
            assert q == 2

            for k, m in group_obj.members.items():
                assert isinstance(m, UserA)

        # Document select_related
        with query_counter() as q:
            assert q == 0

            group_obj = Group.objects.first().select_related()
            assert q == 2

            _ = [m for m in group_obj.members]
            assert q == 2

            _ = [m for m in group_obj.members]
            assert q == 2

            for k, m in group_obj.members.items():
                assert isinstance(m, UserA)

        # Queryset select_related
        with query_counter() as q:
            assert q == 0

            group_objs = Group.objects.select_related()
            assert q == 2

            for group_obj in group_objs:
                _ = [m for m in group_obj.members]
                assert q == 2

                _ = [m for m in group_obj.members]
                assert q == 2

                for _, m in group_obj.members.items():
                    assert isinstance(m, UserA)

        UserA.drop_collection()
        Group.drop_collection()

    def test_generic_reference_map_field(self):
        class UserA(Document):
            name = StringField()

        class UserB(Document):
            name = StringField()

        class UserC(Document):
            name = StringField()

        class Group(Document):
            members = MapField(GenericReferenceField())

        UserA.drop_collection()
        UserB.drop_collection()
        UserC.drop_collection()
        Group.drop_collection()

        members = []
        for i in range(1, 51):
            a = UserA(name="User A %s" % i)
            a.save()

            b = UserB(name="User B %s" % i)
            b.save()

            c = UserC(name="User C %s" % i)
            c.save()

            members += [a, b, c]

        group = Group(members={str(u.id): u for u in members})
        group.save()
        group = Group(members={str(u.id): u for u in members})
        group.save()

        with query_counter() as q:
            assert q == 0

            group_obj = Group.objects.first()
            assert q == 1

            _ = [m for m in group_obj.members]
            assert q == 4

            _ = [m for m in group_obj.members]
            assert q == 4

            for _, m in group_obj.members.items():
                assert "User" in m.__class__.__name__

        # Document select_related
        with query_counter() as q:
            assert q == 0

            group_obj = Group.objects.first().select_related()
            assert q == 4

            _ = [m for m in group_obj.members]
            assert q == 4

            _ = [m for m in group_obj.members]
            assert q == 4

            for _, m in group_obj.members.items():
                assert "User" in m.__class__.__name__

        # Queryset select_related
        with query_counter() as q:
            assert q == 0

            group_objs = Group.objects.select_related()
            assert q == 4

            for group_obj in group_objs:
                _ = [m for m in group_obj.members]
                assert q == 4

                _ = [m for m in group_obj.members]
                assert q == 4

                for _, m in group_obj.members.items():
                    assert "User" in m.__class__.__name__

        Group.objects.delete()
        Group().save()

        with query_counter() as q:
            assert q == 0

            group_obj = Group.objects.first()
            assert q == 1

            _ = [m for m in group_obj.members]
            assert q == 1

        UserA.drop_collection()
        UserB.drop_collection()
        UserC.drop_collection()
        Group.drop_collection()

    def test_multidirectional_lists(self):
        class Asset(Document):
            name = StringField(max_length=250, required=True)
            path = StringField()
            title = StringField()
            parent = GenericReferenceField(default=None)
            parents = ListField(GenericReferenceField())
            children = ListField(GenericReferenceField())

        Asset.drop_collection()

        root = Asset(name="", path="/", title="Site Root")
        root.save()

        company = Asset(name="company", title="Company", parent=root, parents=[root])
        company.save()

        root.children = [company]
        root.save()

        root = root.reload()
        assert root.children == [company]
        assert company.parents == [root]

    def test_dict_in_dbref_instance(self):
        class Person(Document):
            name = StringField(max_length=250, required=True)

        class Room(Document):
            number = StringField(max_length=250, required=True)
            staffs_with_position = ListField(DictField())

        Person.drop_collection()
        Room.drop_collection()

        bob = Person.objects.create(name="Bob")
        bob.save()
        sarah = Person.objects.create(name="Sarah")
        sarah.save()

        room_101 = Room.objects.create(number="101")
        room_101.staffs_with_position = [
            {"position_key": "window", "staff": sarah},
            {"position_key": "door", "staff": bob.to_dbref()},
        ]
        room_101.save()

        room = Room.objects.first().select_related()
        assert room.staffs_with_position[0]["staff"] == sarah
        assert room.staffs_with_position[1]["staff"] == bob

    def test_document_reload_no_inheritance(self):
        class Foo(Document):
            meta = {"allow_inheritance": False}
            bar = ReferenceField("Bar")
            baz = ReferenceField("Baz")

        class Bar(Document):
            meta = {"allow_inheritance": False}
            msg = StringField(required=True, default="Blammo!")

        class Baz(Document):
            meta = {"allow_inheritance": False}
            msg = StringField(required=True, default="Kaboom!")

        Foo.drop_collection()
        Bar.drop_collection()
        Baz.drop_collection()

        bar = Bar()
        bar.save()
        baz = Baz()
        baz.save()
        foo = Foo()
        foo.bar = bar
        foo.baz = baz
        foo.save()
        foo.reload()

        assert isinstance(foo.bar, Bar)
        assert isinstance(foo.baz, Baz)

    def test_document_reload_reference_integrity(self):
        """
        Ensure reloading a document with multiple similar id
        in different collections doesn't mix them.
        """

        class Topic(Document):
            id = IntField(primary_key=True)

        class User(Document):
            id = IntField(primary_key=True)
            name = StringField()

        class Message(Document):
            id = IntField(primary_key=True)
            topic = ReferenceField(Topic)
            author = ReferenceField(User)

        Topic.drop_collection()
        User.drop_collection()
        Message.drop_collection()

        # All objects share the same id, but each in a different collection
        topic = Topic(id=1).save()
        user = User(id=1, name="user-name").save()
        Message(id=1, topic=topic, author=user).save()

        concurrent_change_user = User.objects.get(id=1)
        concurrent_change_user.name = "new-name"
        concurrent_change_user.save()
        assert user.name != "new-name"

        msg = Message.objects.get(id=1)
        msg.reload()
        assert msg.topic == topic
        assert msg.author == user
        assert msg.author.name == "new-name"

    def test_list_lookup_not_checked_in_map(self):
        """Ensure we dereference list data correctly"""

        class Comment(Document):
            id = IntField(primary_key=True)
            text = StringField()

        class Message(Document):
            id = IntField(primary_key=True)
            comments = ListField(ReferenceField(Comment))

        Comment.drop_collection()
        Message.drop_collection()

        c1 = Comment(id=0, text="zero").save()
        c2 = Comment(id=1, text="one").save()
        Message(id=1, comments=[c1, c2]).save()

        msg = Message.objects.get(id=1)
        assert 0 == msg.comments[0].id
        assert 1 == msg.comments[1].id

    def test_list_item_dereference_dref_false_save_doesnt_cause_extra_queries(self):
        """Ensure that DBRef items in ListFields are dereferenced."""

        class User(Document):
            name = StringField()

        class Group(Document):
            name = StringField()
            members = ListField(ReferenceField(User, dbref=False))

        User.drop_collection()
        Group.drop_collection()

        for i in range(1, 51):
            User(name="user %s" % i).save()

        Group(name="Test", members=User.objects).save()

        with query_counter() as q:
            assert q == 0

            group_obj = Group.objects.first()
            assert q == 1

            group_obj.name = "new test"
            group_obj.save()

            assert q == 2

    def test_list_item_dereference_dref_true_save_doesnt_cause_extra_queries(self):
        """Ensure that DBRef items in ListFields are dereferenced."""

        class User(Document):
            name = StringField()

        class Group(Document):
            name = StringField()
            members = ListField(ReferenceField(User, dbref=True))

        User.drop_collection()
        Group.drop_collection()

        for i in range(1, 51):
            User(name="user %s" % i).save()

        Group(name="Test", members=User.objects).save()

        with query_counter() as q:
            assert q == 0

            group_obj = Group.objects.first()
            assert q == 1

            group_obj.name = "new test"
            group_obj.save()

            assert q == 2

    def test_generic_reference_save_doesnt_cause_extra_queries(self):
        class UserA(Document):
            name = StringField()

        class UserB(Document):
            name = StringField()

        class UserC(Document):
            name = StringField()

        class Group(Document):
            name = StringField()
            members = ListField(GenericReferenceField())

        UserA.drop_collection()
        UserB.drop_collection()
        UserC.drop_collection()
        Group.drop_collection()

        members = []
        for i in range(1, 51):
            a = UserA(name="User A %s" % i).save()
            b = UserB(name="User B %s" % i).save()
            c = UserC(name="User C %s" % i).save()

            members += [a, b, c]

        Group(name="test", members=members).save()

        with query_counter() as q:
            assert q == 0

            group_obj = Group.objects.first()
            assert q == 1

            group_obj.name = "new test"
            group_obj.save()

            assert q == 2

    def test_objectid_reference_across_databases(self):
        # mongoneotest - Is default connection alias from setUp()
        # Register Aliases
        register_connection("testdb-1", "mongoneotest2")

        class User(Document):
            name = StringField()
            meta = {"db_alias": "testdb-1"}

        class Book(Document):
            name = StringField()
            author = ReferenceField(User)

        # Drops
        User.drop_collection()
        Book.drop_collection()

        user = User(name="Ross").save()
        Book(name="MongoNeo for pros", author=user).save()

        # Can't use query_counter across databases - so test the _data object
        book = Book.objects.first()
        assert not isinstance(book._data["author"], User)

        book.select_related()
        assert isinstance(book._data["author"], User)

    def test_non_ascii_pk(self):
        """
        Ensure that dbref conversion to string does not fail when
        non-ascii characters are used in primary key
        """

        class Brand(Document):
            title = StringField(max_length=255, primary_key=True)

        class BrandGroup(Document):
            title = StringField(max_length=255, primary_key=True)
            brands = ListField(ReferenceField("Brand", dbref=True))

        Brand.drop_collection()
        BrandGroup.drop_collection()

        brand1 = Brand(title="Moschino").save()
        brand2 = Brand(title="Денис Симачёв").save()

        BrandGroup(title="top_brands", brands=[brand1, brand2]).save()
        brand_groups = BrandGroup.objects().all()

        assert 2 == len([brand for bg in brand_groups for brand in bg.brands])

    def test_dereferencing_embedded_listfield_referencefield(self):
        class Tag(Document):
            meta = {"collection": "tags"}
            name = StringField()

        class Post(EmbeddedDocument):
            body = StringField()
            tags = ListField(ReferenceField("Tag", dbref=True))

        class Page(Document):
            meta = {"collection": "pages"}
            tags = ListField(ReferenceField("Tag", dbref=True))
            posts = ListField(EmbeddedDocumentField(Post))

        Tag.drop_collection()
        Page.drop_collection()

        tag = Tag(name="test").save()
        post = Post(body="test body", tags=[tag])
        Page(tags=[tag], posts=[post]).save()

        page = Page.objects.first()
        assert page.tags[0] == page.posts[0].tags[0]

    def test_select_related_follows_embedded_referencefields(self):
        class Song(Document):
            title = StringField()

        class PlaylistItem(EmbeddedDocument):
            song = ReferenceField("Song")

        class Playlist(Document):
            items = ListField(EmbeddedDocumentField("PlaylistItem"))

        Playlist.drop_collection()
        Song.drop_collection()

        songs = [Song.objects.create(title="song %d" % i) for i in range(3)]
        items = [PlaylistItem(song=song) for song in songs]
        playlist = Playlist.objects.create(items=items)

        with query_counter() as q:
            assert q == 0

            playlist = Playlist.objects.first().select_related()
            songs = [item.song for item in playlist.items]

            assert q == 2


if __name__ == "__main__":
    unittest.main()
