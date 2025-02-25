#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from utils import *
from downloading import *

df = get_df_from_xls("marc_tw.xlsm", "Twitch")
df = df.append(get_df_from_xls("marc_yt.xlsm", "YouTube"), ignore_index=True)
df = df.append(get_df_from_xls("marc_live.xlsm", "Live"), ignore_index=True)

df = get_unique_IDs(df)

# download_songs_from_streams(df, stream_titles=["Music Break No. 4 | Bored Certified"])
# download_songs_from_streams(df, stream_titles=["I'm feeling it.", "HARRY MACK IS ON THE STREAM"])

stream_titles = list(df.drop_duplicates("live_title")["live_title"])

# download_songs_from_streams(df, stream_titles=stream_titles, make_playlist_rank=[["S"], ["S", "Ap"], ["S", "Ap", "A"]])
# dl_thumbnail(df, stream_titles=stream_titles)
# mv_thumbnail_to_icloud(df, stream_titles=stream_titles)
mv_mp3_to_icloud(df, stream_titles=stream_titles, ranks=["A"])
