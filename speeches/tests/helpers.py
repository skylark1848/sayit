from datetime import datetime, date, time, timedelta

from django.test import TestCase

from speeches.models import Section, Speech
from instances.models import Instance


class ParentInstanceMismatchError(Exception):
    pass


def create_sections( subsections, parent=None, instance=None):
    """
    Create a hierachy of sections and speeches. Very useful for setting up test data as needed.

    Note - used in external packages (pombola.south_africa), alter with care.

    create_sections([
        {
            'title': "Top level section",
            'subsections': [
                {   'title': "Nested section",
                    'subsections': [
                        {   'title': "Section with speeches",
                            'speeches': [ 4, date(2013, 3, 25), time(9, 0) ],
                        },
                        {   'title': "Bill on Silly Walks",
                            'speeches': [ 2, date(2013, 3, 25), time(12, 0) ],
                        },
                    ]
                },
                {
                    'title': "Another nested section (but completely empty)",
                    'subsections': []
                },
            ]
        },
    ])
    """

    # If given an instance and a parent check that they are compatible - we don't
    # want to end up with a hierarchy that spans instances and this would probably
    # mean that there is some confusion upstream that we should highlight.
    if instance and parent and instance != parent.instance:
        raise ParentInstanceMismatchError("The instance and parent.instance do not match")

    # If we have a parent then use the instance from that.
    if parent:
        instance = parent.instance

    # If we don't have an instance (which also means we had no parent) then create
    # one - this is very convenient in the test scripts.
    if not instance:
        instance, _ = Instance.objects.get_or_create(label='create-sections-instance')

    for subsection in subsections:
        s = Section.objects.create( instance=instance, title=subsection['title'], parent=parent )
        if 'subsections' in subsection:
            create_sections(subsection['subsections'], parent=s)
        if 'speeches' in subsection:
            num, d, t = subsection['speeches']
            for i in range(0, num):
                Speech.objects.create(
                    instance = instance,
                    section = s,
                    text = 'rhubarb rhubarb',
                    start_date = d,
                    start_time = t,
                )
                if t:
                    t = (datetime.combine(date.today(), t) + timedelta(minutes=10)).time()


class CeateSectionsTests(TestCase):
    def test_parent_instance_mismatch(self):
        foo_instance = Instance.objects.create(label="foo")
        bar_instance = Instance.objects.create(label="bar")
        foo_parent = Section.objects.create(instance=foo_instance, title="Foo Section")

        # Should run without exception
        create_sections([], parent=foo_parent, instance=foo_instance)
        create_sections([],                    instance=foo_instance)
        create_sections([], parent=foo_parent                      )
        create_sections([],                                        )

        # Should raise
        self.assertRaises(
            ParentInstanceMismatchError,
            create_sections,
            subsections = [],
            parent = foo_parent,
            instance = bar_instance
        )
