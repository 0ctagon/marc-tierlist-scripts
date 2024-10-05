#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from utils import *
from database import *
import pandas as pd

dfFR = get_df_from_xls("marc_tw.xlsx", "Twitch")
dfFR = pd.concat([dfFR, get_df_from_xls("marc_live.xlsx", "Live")], ignore_index=True)
dfFR = pd.concat([dfFR, get_df_from_xls("marc_yt.xlsx", "YouTube")], ignore_index=True)

dfEN = get_df_from_xls("marc_tw.xlsx", "Twitch", EN=True)
dfEN = pd.concat([dfEN, get_df_from_xls("marc_live.xlsx", "Live", EN=True)], ignore_index=True)
dfEN = pd.concat([dfEN, get_df_from_xls("marc_yt.xlsx", "YouTube", EN=True)], ignore_index=True)

if len(dfFR) != len(dfEN):
    raise Exception("Miss translation in the English database")

for df_ in [dfFR, dfEN]:
    df_ = get_unique_songID(df_)

    print_simple_stats(df_)

    output_html(df_, EN=True if df_ is dfEN else False)

    output_database_JSON(df_, EN=True if df_ is dfEN else False)

    make_html_tables(df_, EN=True if df_ is dfEN else False)
