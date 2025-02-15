#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from utils import *
from database import *
import pandas as pd
import argparse

parser = argparse.ArgumentParser()
parser.add_argument(
    "--only",
    nargs="+",
    choices=["yt", "tw", "live"],
    default=["yt", "tw", "live"],
    help="only process the specified platform(s): yt (YouTube), tw (Twitch), live (Live). Default is all platforms.",
)
parser.add_argument("--en", action="store_true", help="process the English database.")
parser.add_argument("--stats", action="store_true", help="print simple statistics.")

args = parser.parse_args()

df = pd.DataFrame()
for platform in args.only:
    df = pd.concat(
        [df, get_df_from_xls(f"marc_{platform}.xlsm", EN=args.en)], ignore_index=True
    )

df = get_unique_IDs(df)

print_simple_stats(df)
if args.stats:
    sys.exit()

output_newdatabase_JSON(df, EN=args.en)

# get_HOF_info(song_names, df)
