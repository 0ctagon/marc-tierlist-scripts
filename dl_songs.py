#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from utils import *

df = get_df_from_xls("marc_tw.xlsx", "Twitch")
df = df.append(get_df_from_xls("marc_yt.xlsx", "YouTube"), ignore_index=True)
df = df.append(get_df_from_xls("marc_live.xlsx", "Live"), ignore_index=True)

df = get_unique_songID(df)

# download_songs_from_streams(df, stream_titles=["Music Break No. 4 | Bored Certified"])
# download_songs_from_streams(df, stream_titles=["I'm feeling it.", "HARRY MACK IS ON THE STREAM"])

stream_titles = list(df.drop_duplicates("live_title")["live_title"])

download_songs_from_streams(df, stream_titles=stream_titles)