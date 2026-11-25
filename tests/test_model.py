from resources.lib.twitch.tv import model


def items(start, count):
    return [{'id': str(i), 'kind': 'live'} for i in range(start, start + count)]


def shelf(title, the_items, cursor=None, avatars=False):
    return {'list': 'x', 'params': {}, 'title': title, 'avatars': avatars, 'items': the_items, 'cursor': cursor}


def page(shelves):
    return {'title': 'Page', 'shelves': shelves, 'header': None, 'message': ''}


def test_shelves_become_rows():
    screen = model.Screen({'page': 'home'}, lambda desc: page([shelf('A', items(0, 3), 'c'), shelf('B', items(3, 2))]),
                          None).open()
    assert [(r.title, len(r.items), r.cursor) for r in screen.rows] == [('A', 3, 'c'), ('B', 2, None)]
    assert not screen.can_grow()


def test_single_list_is_cut_into_a_grid_and_grows():
    batches = {'c1': (items(10, 6), 'c2'), 'c2': (items(16, 4), None)}
    screen = model.Screen({'page': 'categories'}, lambda desc: page([shelf('Top', items(0, 10), 'c1')]),
                          lambda the_shelf, cursor: batches[cursor]).open()
    assert [len(r.items) for r in screen.rows] == [4, 4, 2]
    assert screen.rows[0].title == 'Top' and screen.rows[1].title == ''
    screen.ensure(1)  # two rows below the second: one batch is enough
    assert [len(r.items) for r in screen.rows] == [4, 4, 4, 4]
    screen.ensure(2)
    assert [len(r.items) for r in screen.rows] == [4, 4, 4, 4, 4]
    assert not screen.can_grow()


def test_grid_stops_on_a_batch_with_nothing_new():
    screen = model.Screen({'page': 'categories'}, lambda desc: page([shelf('Top', items(0, 4), 'c1')]),
                          lambda the_shelf, cursor: (items(0, 4), 'c2')).open()
    screen.ensure(0)
    assert len(screen.rows) == 1 and not screen.can_grow()


def test_row_scrolls_on_without_repeats():
    screen = model.Screen({'page': 'home'}, lambda desc: page([shelf('A', items(0, 3), 'c'), shelf('B', items(3, 1))]),
                          lambda the_shelf, cursor: (items(2, 3), None)).open()
    fresh = screen.more_items(screen.rows[0])
    assert [i['id'] for i in fresh] == ['3', '4']
    assert screen.rows[0].cursor is None
    assert screen.more_items(screen.rows[0]) == []


def test_local_screen_builds_again_on_refresh():
    calls = []
    screen = model.LocalScreen('Search', lambda: calls.append(1) or [model.Row('R', [])]).open()
    screen.refresh()
    assert len(calls) == 2 and screen.title == 'Search'
