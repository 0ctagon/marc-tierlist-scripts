# -*- coding: utf-8 -*-
"""
This script calculates the duration between two timestamps entered by the user.

Accepted input formats:
1. MMSS format (e.g., '0732' → 7 minutes, 32 seconds)
2. HMMSS format (e.g., '10732' → 1 hour, 7 minutes, 32 seconds)
3. Twitch timestamp URLs (e.g., 'https://www.twitch.tv/videos/...?t=00h00m07s' → 7 seconds)


- It rounds up the last digit if greater than 5.
- The process repeats until the user inputs "q", "quit", "stop", or "a" to exit.
"""
import sys
import datetime


def if_quit(x):
    if x in ["q", "quit", "stop", "a"]:
        sys.exit()


a, b = "", ""
while True:
    a = input("Begining: \t")
    if_quit(a)

    if len(a) == 4:
        t1 = datetime.timedelta(minutes=int(a[:2]), seconds=int(a[2:4]))
    elif len(a) == 5:
        t1 = datetime.timedelta(
            hours=int(a[:1]), minutes=int(a[1:3]), seconds=int(a[3:5])
        )
    else:
        a = a[a.index("?t=") + 3 :]
        t1 = datetime.timedelta(
            hours=int(a[: a.index("h")]),
            minutes=int(a[a.index("h") + 1 : a.index("m")]),
            seconds=int(a[a.index("m") + 1 : a.index("s")]),
        )
    print(t1)

    a = input("End stp: \t")
    if_quit(a)

    if len(a) == 4:
        t2 = datetime.timedelta(minutes=int(a[:2]), seconds=int(a[2:4]))
    elif len(a) == 5:
        t2 = datetime.timedelta(
            hours=int(a[:1]), minutes=int(a[1:3]), seconds=int(a[3:5])
        )
    else:
        a = a[a.index("?t=") + 3 :]
        t2 = datetime.timedelta(
            hours=int(a[: a.index("h")]),
            minutes=int(a[a.index("h") + 1 : a.index("m")]),
            seconds=int(a[a.index("m") + 1 : a.index("s")]),
        )
    print(t2)
    print()

    timer = str(t2 - t1)[2:]

    ltimer = list(timer)
    if int(timer[-1]) > 5:
        ltimer[-2] = str(int(ltimer[-2]) + 1)
        if int(ltimer[-2]) == 6:
            ltimer[-2] = "0"
            if int(ltimer[-4]) == 9:
                ltimer[-5] = str(int(ltimer[-5]) + 1)
                ltimer[-4] = "0"
            else:
                ltimer[-4] = str(int(ltimer[-4]) + 1)

    ltimer[-1] = str(0)
    timer = "".join(ltimer)

    print(f"Time: \t {timer}")
    print()
    print("------------------------------------------------")
    print()
