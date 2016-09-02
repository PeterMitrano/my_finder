from my_finder.util import responder


def add_item_location(item, location, db):
    # make sure we replace spaces with underscores
    item = item.replace(' ', '_')

    # save this to our database!
    # first grab whatever was there previously so we don't lose it
    if db.result.value is not None:
        data = db.result.value
        data.pop('userId')
    else:
        data = {}
    data[item] = location

    db.helper.setAll(data)
    item = item.replace('_', ' ')
    return responder.tell('Item is %s. Location is %s. Got it.' %
                          (item, location))


def handle(intent, slots, session_attributes, db):
    item = session_attributes['current_item']
    location = session_attributes['current_location']
    return add_item_location(item, location, db)
