from ness.models import Event, EventType, Zone, ApplicableArea, OutputEventData
from django.db.models import Q

def setup():

    event_names = [
        ["Zone or User EVENTS", 0x00, 0x09],
        ["System EVENTS", 0x10, 0x19],
        ["Area EVENTS", 0x20, 0x30],
        ["Result EVENTS", 0x31, 0x32],
    ]

    for eN in event_names:
        EventType.objects.get_or_create(
            name = eN[0],
            range_begin = eN[1],
            range_end = eN[2]
        )

    even_descriptions = [
        ["Unsealed", 0x00],
        ["Sealed", 0x01],
        ["Alarm", 0x02],
        ["Alarm Restore", 0x03],
        ["Manual Exclude", 0x04],
        ["Manual Include", 0x05],
        ["Auto Exclude", 0x06],
        ["Auto Include", 0x07],
        ["Tamper Unsealed", 0x08],
        ["Tamper Normal", 0x09],
        ["Power Failure", 0x010],
        ["Power Normal", 0x11],
        ["Battery Failure", 0x12],
        ["Battery Normal", 0x13],
        ["Report Failure", 0x14], 
        ["Report Normal", 0x15],
        ["Supervision Failure", 0x16],
        ["Supervision Normal", 0x17],
        ["Real Time Clock", 0x19],
        ["Entry Delay Start", 0x20],
        ["Entry Delay End", 0x21],
        ["Exit Delay Start", 0x22],
        ["Exit Delay End", 0x23],
        ["Armed Away", 0x24],
        ["Armed Home", 0x25],
        ["Armed Day", 0x26],
        ["Armed Night", 0x27],
        ["Armed Vacation", 0x28],
        ["Armed Highest", 0x2e],
        ["Disarmed", 0x2f],
        ["Arming delayed", 0x30],
        ["Output On", 0x31],
        ["Output Off", 0x32],
    ]

    for eD in even_descriptions:
        try:
            Event.objects.get_or_create(
                description = eD[0],
                event_id = eD[1],
                event_type = EventType.objects.get(Q(range_begin__lte=eD[1]), Q(range_end__gte=eD[1]))
            )
        except Exception as exp:
            print(exp)
    

    zone_names = [
        ["Main Floor PIRS", 1],
        ["Upstairs PIR", 2],
        ["Garage PIR", 3],
        ["Free", 4],
        ["Backyard Door", 5],
        ["Main Front Door", 6],
        ["Garage Back Door", 7],
        ["Smoke Alarms", 8],        
        ["Sliding Door Balcony", 9],
        ["Guest Room Window - Mid-stairs", 10],
        ["Pantry Window", 11],
        ["Free", 12],
        ["Lower Front Door", 13],
        ["Garage Roller Door", 14],
        ["Free", 15],
        ["Free", 16],
    ]

    for zN in zone_names:
        Zone.objects.get_or_create(
            description = zN[0],
            zone_id = zN[1],
        )


    applicable_areas = [
        ["No Area", 0x00],
        ["Area 1", 0x01],
        ["Area 2", 0x02],
        ["Monitor", 0x03],
        ["Day", 0x04],
        ["24 hr", 0x80],
        ["Fire", 0x81],
        ["Panic", 0x82],
        ["Medical", 0x83],
        ["Duress", 0x84],
        ["Radio Detector", 0x91],
        ["Radio Key", 0x92],
        ["Door 1", 0xA1],
        ["Door 2", 0xA2],
        ["Door 3", 0xA3],
    ]

    for aN in applicable_areas:
        ApplicableArea.objects.get_or_create(
            description = aN[0],
            area_id = aN[1],
        )


    # try:
    #     data = OutputEventData.objects.all()
    #     data.update(byte_command=97, data="000000")
    # except Exception as exp:
    #     print(exp)

    return True


# make sure we populate the database!
setup()