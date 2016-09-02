from my_finder.util import responder

def add_item_location(item, location, db_result):
    # make sure we replace spaces with underscores
    item = item.replace(' ', '_')

    # save this to our database!
    # first grab whatever was there previously so we don't lose it
    if db_result.value is not None:
        data = db_result.value
        data.pop('userId')
    else:
        data = {}
    data[item] = location

    db_result.setAll(data)
    return responder.tell('Item is %s. Location is %s. Got it.' %
                          (item, location))


def handle(intent, slots, session_attributes, db_result):
    item = session_attributes['current_item']
    location = session_attributes['current_location']
    return add_item_location(item, location, db_result)
