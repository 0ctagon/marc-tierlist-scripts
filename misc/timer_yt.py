# -*- coding: utf-8 -*-
"""
This script calculates the duration between two timestamps entered by the user.

Accepted input formats:
1. Plain seconds (e.g., '732' → 732 seconds)
2. YouTube timestamp URLs (e.g., 'https://youtu.be/...?...t=732s' → 732 seconds)
3. Special input "o" to reuse the last end timestamp as the new start time.

- It rounds up the last digit if greater than 5.
- The process repeats until the user inputs "q", "quit", "stop", or "a" to exit.
"""
import sys
import datetime


def if_quit(x):
    if x in ["q", "quit", "stop", "a"]:
        sys.exit()


a, b = "", ""
old = ""
while True:
    a = input("Begining: \t")
    if_quit(a)

    if a == "o":
        t1 = t2
    else:
        if list(a)[-1] == "s":
            a = a[:-1]

        if a[0] != "h":
            t1 = int(a)
        else:
            t1 = int(a[a.index("t=") + 2 :])

    print(datetime.timedelta(seconds=t1))

    b = input("End stp: \t")
    if_quit(b)

    if list(b)[-1] == "s":
        b = b[:-1]

    if b[0] != "h":
        t2 = int(b)
    else:
        t2 = int(b[b.index("t=") + 2 :])
    print(datetime.timedelta(seconds=t2))
    print()

    if int(t1) > int(t2):
        sys.exit()

    timer = str(datetime.timedelta(seconds=t2 - t1))[2:]

    # if int(timer[0]) == 0: timer = timer[1:]

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


# https://youtu.be/O4Ko7NW2yQo?t=7
# https://youtu.be/O4Ko7NW2yQo?t=404
