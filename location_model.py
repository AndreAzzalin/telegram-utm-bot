import utm


class ChatLocations:
    def __init__(self, chat_id):
        self.chat_id = chat_id
        self.location_list = {}
        self.tracking_active = False

    def update_location(self, user_id, name, coords, timestamp):
        loc_item = LocationItem(name, coords, timestamp)
        self.location_list[user_id] = loc_item

    def __str__(self):
        llist = [str(loc) for loc in self.location_list.values()]
        if not llist:
            return 'No location info available yet'
        return '\n\n'.join(llist)


class LocationItem:
    def __init__(self, name, coords, timestamp):
        self.user_name = name
        self.latitude = coords[0]
        self.longitude = coords[1]
        self.timestamp = timestamp

    def __str__(self):
        return '{user}: {coords} - {timestamp}'.format(user=self.user_name,
                                                       coords=latlong_to_utm(self.latitude, self.longitude),
                                                       timestamp=self.timestamp.strftime("%H:%M:%S"))


def latlong_to_utm(lat, long):
    utm_coords = utm.from_latlon(lat, long)
    return '{zone}{letter} {e:.0f}E {n:.0f}N'.format(zone=utm_coords[2], letter=utm_coords[3], e=utm_coords[0], n=utm_coords[1])