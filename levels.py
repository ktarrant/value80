import datetime
from collections import OrderedDict

VALUE_AREAS = {
    "ESZ7": OrderedDict([
        (datetime.date(year=2017, month=11, day=22), { "VAH": 2600, "VAL": 2594.5 }),
        (datetime.date(year=2017, month=11, day=21), { "VAH": 2583.25, "VAL": 2578.25 }),
        (datetime.date(year=2017, month=11, day=20), { "VAH": 2582.25, "VAL": 2578.25 }),
        (datetime.date(year=2017, month=11, day=17), { "VAH": 2589.25, "VAL": 2576.75}),
        (datetime.date(year=2017, month=11, day=16), { "VAH": 2569.25, "VAL": 2562.25}),
        (datetime.date(year=2017, month=11, day=15), { "VAH": 2578, "VAL": 2571 }),
        (datetime.date(year=2017, month=11, day=14), { "VAH": 2584, "VAL": 2577.5 }),
        (datetime.date(year=2017, month=11, day=13), { "VAH": 2580.75, "VAL": 2575.25 }),
        (datetime.date(year=2017, month=11, day=10), { "VAH": 2584, "VAL": 2572.5 }),
        (datetime.date(year=2017, month=11, day=9), { "VAH": 2592.25, "VAL": 2584.75 }),
        (datetime.date(year=2017, month=11, day=8), { "VAH": 2590.5, "VAL": 2583.5 }),
        (datetime.date(year=2017, month=11, day=7), { "VAH": 2589.75, "VAL": 2584.75 }),
        (datetime.date(year=2017, month=11, day=6), { "VAH": 2585, "VAL": 2577.5 }),
        (datetime.date(year=2017, month=11, day=3), { "VAH": 2576, "VAL": 2568.5 }),
        (datetime.date(year=2017, month=11, day=2), { "VAH": 2581.5, "VAL": 2574 }),
        (datetime.date(year=2017, month=11, day=1), { "VAH": 2574.25, "VAL": 2571.25 }),
    ]),
}