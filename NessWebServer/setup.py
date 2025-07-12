from ness_comms.models import Zone
from nessclient.event import ZoneUpdate
# create 16 zones with as default



def create_default_zones():
    if len(Zone.objects.all()) == 0:

        Zone.objects.all().delete()

        zone_list = [
            "MAIN FLOOR PIRS",
            "UPSTAIRS PIRS",
            "GARAGE PIRS",
            "SMOKE MAIN FLOOR",
            "BACKYARD DOOR",
            "MAIN FRONT DOOR",
            "GARAGE BACK DOOR",
            "SMOKES UPSTAIRS",
            "SLIDING DOOR BAL",
            "GUEST ROOM WINDOW",
            "PANTRY WINDOW",
            "SMOKE DOWNSTAIRS",
            "LOWER FRONT DOOR",
            "GARAGE ROLLER DOOR",
            "BALCONY UPSTAIRS",
            "Unnamed Zone"
        ]

        try:
            for zone_idx in range(0, 17):
                zone = Zone.objects.create(name=f"{zone_list[zone_idx]}", address=list(ZoneUpdate.Zone)[zone_idx].value)
        except Exception as ex:
            print(ex)

    else:
        print("Zone already exists")