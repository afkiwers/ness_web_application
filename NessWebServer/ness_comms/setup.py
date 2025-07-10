from ness_comms.models import Zone

def setup():

    zone_names = [
        ["Unused", 1,  0x0100],
        ["Unused", 2,  0x0200],
        ["Unused", 3,  0x0400],
        ["Unused", 4,  0x0800],
        ["Unused", 5,  0x1000],
        ["Unused", 6,  0x2000],
        ["Unused", 7,  0x4000],
        ["Unused", 8,  0x8000],
        ["Unused", 9,  0x0001],
        ["Unused", 10, 0x0002],
        ["Unused", 11, 0x0004],
        ["Unused", 12, 0x0008],
        ["Unused", 13, 0x0010],
        ["Unused", 14, 0x0020],
        ["Unused", 15, 0x0040],
        ["Unused", 16, 0x0080],
    ]

    for zN in zone_names:
        try:
            Zone.objects.get_or_create(
                description=zN[0],
                zone_id=zN[1],
                zone_address=zN[2]
            )
        except Exception as exp:
            print(exp)

    return True


# make sure we populate the database!
setup()
