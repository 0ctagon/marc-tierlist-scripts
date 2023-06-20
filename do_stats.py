#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from utils import *

df = get_df_from_xls("marc_tw.xlsx", "Twitch")
df = df.append(get_df_from_xls("marc_live.xlsx", "Live"), ignore_index=True)
df = df.append(get_df_from_xls("marc_yt.xlsx", "YouTube"), ignore_index=True)

df = get_unique_songID(df)


filtered_df = df[~df['songID'].str.startswith('cut')].query("rank != 'I'").query("htmlID != 's200704l'")
filtered_df = filtered_df.sort_values("date_DT", ascending=False)

# make_timing_plot(filtered_df)
# make_nsongs_plot(filtered_df)
# make_stream_length_plot(filtered_df)
# make_livetype_plot(filtered_df)

make_rank_plots(filtered_df)

# make_rank_nsong(filtered_df)
# make_rank_nsong_streamtype(filtered_df)
# make_rank_length_streamtype(filtered_df)

# make_tempo_nsong(filtered_df)
# make_tempo_nsong_streamtype(filtered_df)