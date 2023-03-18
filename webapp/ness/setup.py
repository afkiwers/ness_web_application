from ness.models import Zone
from django.db.models import Q


def setup():

    zone_names = [
        ["Main Floor PIRS", 1, 0x0100],
        ["Upstairs PIR", 2, 0x0200],
        ["Garage PIR", 3, 0x0400],
        ["Free", 4, 0x0800],
        ["Backyard Door", 5, 0x1000],
        ["Main Front Door", 6, 0x2000],
        ["Garage Back Door", 7, 0x4000],
        ["Smoke Alarms", 8, 0x8000],
        ["Sliding Door Balcony", 9, 0x0001],
        ["Guest Room Window", 10, 0x0002],
        ["Pantry Window", 11, 0x0004],
        ["Free", 12, 0x0008],
        ["Lower Front Door", 13, 0x0010],
        ["Garage Roller Door", 14, 0x0020],
        ["Free", 15, 0x0040],
        ["Free", 16, 0x0080],
    ]

    for zN in zone_names:
        Zone.objects.get_or_create(
            description=zN[0],
            zone_id=zN[1],
            zone_address=zN[2]
        )

    return True


# make sure we populate the database!
setup()
