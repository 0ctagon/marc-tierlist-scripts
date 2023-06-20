#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from utils import *

df = get_df_from_xls("marc_tw.xlsx", "Twitch")
df = df.append(get_df_from_xls("marc_live.xlsx", "Live"), ignore_index=True)
df = df.append(get_df_from_xls("marc_yt.xlsx", "YouTube"), ignore_index=True)

dfEN = get_df_from_xls("marc_tw.xlsx", "Twitch", EN=True)
dfEN = dfEN.append(get_df_from_xls("marc_live.xlsx", "Live", EN=True), ignore_index=True)
dfEN = dfEN.append(get_df_from_xls("marc_yt.xlsx", "YouTube", EN=True), ignore_index=True)

if len(df) != len(dfEN):
    print("IL MANQUE DES CHANSONS TRADUITES????????????/")
    sys.quit()

df = get_unique_songID(df)
dfEN = get_unique_songID(dfEN)

print_simple_stats(df)
print_simple_stats(dfEN)

output_html(df)
output_html(dfEN, EN=True)

output_database_JSON(df)
output_database_JSON(dfEN, EN=True)

make_html_tables(df)
make_html_tables(dfEN, EN=True)
