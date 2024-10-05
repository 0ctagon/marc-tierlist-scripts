#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from utils import *
from plotting import *
import pandas as pd

df = get_df_from_xls("marc_tw.xlsx", "Twitch")
df = pd.concat([df, get_df_from_xls("marc_live.xlsx", "Live")], ignore_index=True)
df = pd.concat([df, get_df_from_xls("marc_yt.xlsx", "YouTube")], ignore_index=True)

df = get_unique_songID(df)

print_simple_stats(df)

filtered_df = df[~df["songID"].str.startswith("cut")].query("rank != 'I'").query("htmlID != 's200704l'")
filtered_df = filtered_df.sort_values("date_DT", ascending=False)

make_length_plot(filtered_df, plot_type="timing")
make_length_plot(filtered_df, plot_type="stream_length")

make_count_plot(filtered_df)
make_nsongs_plot(filtered_df)

make_streamtype_plot(filtered_df, plot_type="rank")
make_streamtype_plot(filtered_df, plot_type="tempo")

make_livetype_plot(filtered_df)
make_rank_length_streamtype(filtered_df)
make_tempo_nsong(filtered_df)

make_rank_plots(filtered_df, rank="high")
make_rank_plots(filtered_df, rank="mid")
make_rank_plots(filtered_df, rank="low")
