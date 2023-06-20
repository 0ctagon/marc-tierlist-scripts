#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import math
import os
import openpyxl
import numpy as np
import datetime
import pandas as pd
from xlsx2html import xlsx2html
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import calendar
import seaborn as sns


months_to_num = {"Jan":"01",
          "Feb":"02",
          "Mar":"03",
          "Apr":"04",
          "May":"05",
          "Jun":"06",
          "Jul":"07",
          "Aug":"08",
          "Sep":"09",
          "Oct":"10",
          "Nov":"11",
          "Dec":"12"}




class Song:
    def __init__(self, name, media, live_date, rank, genre, tempo, length, comment, choral, URL, when_ranked, live_title, live_comment):
        self.songID = self.get_songID(name)
        self.rank = self.format_rank(rank)
        self.htmlID = self.get_htmlID(live_date, media)
        self.length = self.format_length(length, self.songID)
        self.length_DT = self.get_length_DT(self.length)
        self.media = media
        self.date_str = self.get_date_str(self.htmlID, media)
        self.date_DT = datetime.datetime(year=int("20"+self.date_str[0:2]),month=int(self.date_str[2:4]),day=int(self.date_str[4:6]))
        self.date_YM_DT = datetime.datetime(year=self.date_DT.year,month=self.date_DT.month,day=1)
        self.name = self.format_name(name)
        self.tempo = self.format_tempo(tempo)
        self.comment = self.format_comment(comment)
        self.choral = self.format_choral(choral)
        self.genre = genre
        self.URL = URL
        self.when_ranked_DT = datetime.datetime(year=int("20"+str(when_ranked)[0:2]),month=int(str(when_ranked)[2:4]),day=int(str(when_ranked)[4:6]))
        self.when_ranked_YM_DT = datetime.datetime(year=self.when_ranked_DT.year,month=self.when_ranked_DT.month,day=1)
        self.live_title = live_title
        self.live_comment = self.format_live_comment(live_comment)


    def get_htmlID(self, live_date, media):
        if media in ["YouTube", "Live"]:
            day = f"0{live_date[4]}" if "," in live_date[4:6] else live_date[4:6]
            if media == "YouTube":
                return f"s{live_date[-2:]}{months_to_num[live_date[:3]]}{day}"
            else:
                return f"s{live_date[-2:]}{months_to_num[live_date[:3]]}{day}l"
        elif media == "Twitch":
            return f"s{live_date}"

    def get_date_str(self, htmlID, media):
        if media == "YouTube": return htmlID[1:]
        elif media in ["Live", "Twitch"]: return htmlID[1:-1]

    def get_length_DT(self, length):
        if (length not in [np.nan]) and len(length)>3:
            if length[1]=="'":
                return datetime.timedelta(minutes=int(length[0]), seconds=int(length[2]+length[3]))
            elif length[2]=="'":
                return datetime.timedelta(minutes=int(length[0]+length[1]), seconds=int(length[3]+length[4]))
            else:
                return datetime.timedelta(minutes=0, seconds=0)
        else:
            return datetime.timedelta(minutes=0, seconds=0)


    def format_tempo(self, tempo):
        if "into" in tempo:
            tempo = tempo.split(" into ")[0]

        if tempo in ["medium", "medium "]:
            return "Med"
        elif tempo in ["medium fast", "slow fast"]:
            return "Fmed"
        elif tempo in ["medium slow"]:
            return "Smed"
        elif tempo in ["fast", "fast af", "fast fast", "ultra fast", "ULTRA FAST", "jsp"]:
            return "Fast"
        elif tempo in ["slow", "slow ", "sloooow", "hors du temps (14'30 en vrai)", "out of time (14'30 in reality)", "-"]:
            return "Slow"
        else:
            print(tempo, "not defined")
            sys.exit()

    def format_comment(self, comment):
        for c in ["\n", '"']:
            comment = comment.replace(c, "")
        comment.replace("…","...")
        return comment

    def format_choral(self, choral):
        try:
            math.isnan(choral)
            choral = "-"
        except:
            pass
        choral=choral.replace('\n','')
        return choral

    def format_name(self, name):
        name = name.replace('"','')
        return name

    def get_songID(self, name):
        for c in ["-", " ", "  ", "'", "(", ")", ".", '"', ',', '&', ':', '!', '?', '\\', '/']:
            name = name.replace(c, "")
        if name[0].isdigit(): name = "n"+name
        return name

    def format_rank(self, rank):
        rank = rank.replace('-','I')
        if rank == "S I D": rank="D"
        return rank

    def format_length(self, length, songID):
        if songID == "Dramaticevent": length = "14'30"
        return length

    def format_live_comment(self, live_comment):
        if live_comment not in [np.nan]:
            return live_comment
        return "-"



def get_df_from_xls(xls_file, media, EN=False):
    song_list = []
    date_set = False
    wrkbk = openpyxl.load_workbook(xls_file)
    if not EN:
        sh = wrkbk["Sheet1"]
    else:
        sh = wrkbk["Sheet2"]

    line_start = 5
    for n_line, row in enumerate(sh.iter_rows(min_row=line_start, min_col=1, max_row=1500, max_col=10), line_start):
        line = []
        for cell in row:
            if cell.value is None:
                line.append(np.nan)
            else:
                line.append(cell.value)
        if row[2].value is not None:
            song_URL = row[2].hyperlink.target

        # print(line, date_set)

        title_or_date = line[0]
        song_name = line[2]
        if type(song_name)==int: song_name=str(song_name)
        song_rank = line[3]
        song_genre = line[4]
        song_tempo = line[5]
        song_length = line[6]
        song_comment = line[7]
        song_choral = line[8]

        try:
            math.isnan(song_name)
            continue
        except:
            try:
                math.isnan(title_or_date)
            except:
                if date_set == True: date_set = False
                else:
                    live_title = line[0]
                    live_comment = line[1]
                    song_date = sh.cell(n_line+1, 1).value
                    song_when_ranked = line[9]
                    if math.isnan(song_when_ranked): song_when_ranked = 990101
                    date_set = True
                    # print(live_title, live_comment, song_date, song_when_ranked)

        try:
            math.isnan(song_choral)
        except:
            if '"' in song_choral:
                song_choral = song_choral.replace('"',sh.cell(n_line-1, 9).value)

        song_list.append(Song(song_name, media, song_date, song_rank, song_genre, song_tempo, song_length, song_comment, song_choral, song_URL, song_when_ranked, live_title, live_comment))

    return pd.DataFrame([vars(v) for v in song_list])


def get_unique_songID(df):
    print("\nMultiple songIDs format:")
    songIDs = []
    for index, row in df.iterrows():
        songID = row["songID"]
        songIDs.append(songID)
        if songIDs.count(songID)>1:
            print(f"Multiple {songID} ({songIDs.count(songID)})")
            df.at[index, "songID"] = songID+str(songIDs.count(songID))
    print("Done")
    return df


def print_simple_stats(df):
    print("\n_______ Simple stats _______")
    print(f'\nAny rank : ({len(df)})')
    print('S : ({0})'.format(len(df.query("rank=='S'"))))
    print('A+: ({0})'.format(len(df.query("rank=='A+'"))))
    print('A : ({0})'.format(len(df.query("rank=='A'"))))
    print('B+: ({0})'.format(len(df.query("rank=='B+'"))))
    print('B : ({0})'.format(len(df.query("rank=='B'"))))
    print('C+: ({0})'.format(len(df.query("rank=='C+'"))))
    print('C : ({0})'.format(len(df.query("rank=='C'"))))
    print('D : ({0})'.format(len(df.query("rank=='D'"))))
    print('Interlude: ({0})'.format(len(df.query("rank=='I'"))))

    print(f'\nNumber of Live Streams done: {len(df.groupby("htmlID"))} streams')
    print(f'Total music ranked: {len(df)} songs')
    print(f'Total music length ranked: {str(df["length_DT"].sum())}\n')
    print(f'Average music time per streams: {str(df["length_DT"].sum()/len(df.groupby("htmlID")))[7:15]}')
    print(f'Longest music time for a stream: {str(list(df[["length_DT","htmlID"]].groupby("htmlID").sum().max())[0])[7:15]}, {list(df[["length_DT","live_title"]].groupby("live_title").sum().idxmax())[0]}')
    if list(df[["length_DT","htmlID"]].groupby("htmlID").sum().idxmax())[0]!= "s201209": print("NEW RECORD!\n")
    else: print()
    print(f'Average song length: {str(df["length_DT"].sum()/len(df))[7:15]}')
    print(f'Longest song length: {str(df["length_DT"].max())[7:15]} with {df.loc[df["length_DT"].idxmax()]["name"]}\n')
    print(f'Average number of songs per stream: {len(df)/len(df.groupby("htmlID")):.2f} songs')
    print(f'Highest number of songs for a stream: {df[["length_DT","live_title"]].groupby("live_title").size().max()} songs, {df[["length_DT","live_title"]].groupby("live_title").size().idxmax()}')
    if df[["length_DT","htmlID"]].groupby("htmlID").size().idxmax()!= "s180211": print("NEW RECORD!\n")
    else: print()


    estimated_live_left = 108-len(df.groupby("htmlID"))
    print(f'Number of Live Stream left to rank (estimation): {estimated_live_left}')
    print(f'Number of songs left to rank (estimation): {estimated_live_left*(len(df)/len(df.groupby("htmlID"))):.0f}')
    print(f'Total music length left to rank (estimation): {str(estimated_live_left*(df["length_DT"].sum()/len(df.groupby("htmlID"))))[7:15]}\n')



num_to_months = {1:"Janvier",
          2:"Février",
          3:"Mars",
          4:"Avril",
          5:"Mai",
          6:"Juin",
          7:"Juillet",
          8:"Août",
          9:"Septembre",
          10:"Octobre",
          11:"Novembre",
          12:"Décembre"}

num_to_months_EN = {1:"January",
          2:"February",
          3:"March",
          4:"April",
          5:"May",
          6:"June",
          7:"July",
          8:"August",
          9:"September",
          10:"October",
          11:"November",
          12:"December"}


def get_date_verbose(date_DT, EN=False):
    if EN: num_to_months_used = num_to_months_EN
    else: num_to_months_used = num_to_months

    suffix = ""
    if EN:
        if date_DT.day in [1, 21, 31]: suffix = "st"
        elif date_DT.day in [2, 22]: suffix = "nd"
        elif date_DT.day in [3, 23]: suffix = "rd"
        else: suffix = "th"

    return f"{date_DT.day}{suffix} {num_to_months_used[date_DT.month]} {date_DT.year}"

def get_ranked_date_prompt(date_DT, EN=False):
    if EN:
        num_to_months_used = num_to_months_EN
        prompt = "Ranked around"
    else:
        num_to_months_used = num_to_months
        prompt = "Noté vers"

    return f"{prompt} {num_to_months_used[date_DT.month]} {date_DT.year}"


def get_live_code(url):
    if ".be" in url: live_code = url[url.index(".be")+4:]
    elif "live/" in url: live_code = url[url.index("live/")+5:url.index("live/")+5+11]
    elif "v=" in url: live_code = url[url.index("v=")+2:]
    if "t=" in live_code: live_code = live_code[:live_code.index("t=")-1]
    return live_code


def output_html(df, EN=False):
    df = df.sort_values("date_DT", ascending=False).drop_duplicates(["htmlID"])

    parallax_line = ""
    parallax_bg_lines = ""
    for media, media_folder in [("YouTube", "yt"), ("Live", "live"), ("Twitch", "tw")]:
        media_suffix = ""
        if EN: media_suffix = "EN_"
        with open(f'data/{media_suffix}{media}.txt', 'w') as f:
            f.close()
        df_media = df.query(f"media=='{media}'")

        live_div = ""
        for live in df_media.itertuples():
            parallax_line += f".parallax{live.htmlID}, "
            if media=="Twitch":
                parallax_bg_lines += f'\t\t\t.parallax{live.htmlID} {{background-image:url("thumbnails/tw/{live.htmlID}.jpg");}}\n'
            else:
                parallax_bg_lines += f'\t\t\t.parallax{live.htmlID} {{background-image:url("https://i.ytimg.com/vi/{get_live_code(live.URL)}/maxresdefault.jpg");}}\n'

            live_div += f'\n\n\n\t\t\t<div class="parallax{live.htmlID}"; id="{live.htmlID}"></div>\n\n'
            live_div += f'\t\t\t<span>{live.live_title} &nbsp; <b>- {get_date_verbose(live.date_DT, EN)} -</b> &nbsp; <bb>{get_ranked_date_prompt(live.when_ranked_YM_DT, EN)}</bb></span>\n'
            if live.live_comment != "-":
                live_div += f'\t\t\t<p>{live.live_comment}</p>\n'
            live_div += '\t\t\t<br><br>\n'
            live_div += f'\t\t\t<div data-include="tables/{media_folder}/{live.htmlID}"></div>\n'
            live_div += '\t\t\t<br><br><br>'

        with open(f'data/{media_suffix}{media}.txt', 'w') as f:
            f.write(live_div)

    with open(f'data/parallax.txt', 'w') as f:
        f.write(parallax_line[:-2]+"\n"*5)
        f.write(parallax_bg_lines)



# DEPRECATED
def output_database(df, EN=False):
    if EN: databse_suffix = "EN_"
    else: databse_suffix = ""
    with open(f'data/{databse_suffix}database.txt', 'w') as f:
        f.close()
    songIDs = ""
    with open(f'data/{databse_suffix}database.txt', 'w') as f:
        for song in df.itertuples():
            f.write(f'\t\t\tconst {song.songID} = new Song("{song.htmlID}", "{song.name}", "{song.rank.replace("+","p")}", "{song.genre}", "{song.tempo}", "{song.length}", "{song.comment}", "{song.choral}", "{song.URL}");\n')
            songIDs += f"{song.songID}, "
        songIDs = songIDs[:-2]
        f.write(f"\t\t\tvar songList = [{songIDs}];")
    if not EN: print_streams_added(df, songIDs)


def print_streams_added(df, songIDs):
    with open(f'oldList.txt', 'r') as f:
        old_songIDs = f.readline().split(", ")
    songIDs = songIDs.split(", ")
    live_added = []
    for songID in list(set(songIDs)-set(old_songIDs)):
        live_title = df.query(f"songID=='{songID}'").iloc[-1]["live_title"]
        if live_title not in live_added:
            live_added.append(live_title)
    print(f"{len(live_added)} live added since last time: {live_added}")
    print("\n(Don't forget to update oldList!)\n")





def output_database_JSON(df, EN=False):
    if EN: database_suffix = "EN_"
    else: database_suffix = ""
    with open(f'data/{database_suffix}database.json', 'w') as f:
        f.close()
    songs = "["
    for song in df.itertuples():
            # "id" : "{song.songID}",
        songs += (f'''
        {{
            "id" : "{song.htmlID}",
            "name" : "{song.name}",
            "rank" : "{song.rank.replace("+","p")}",
            "genre" : "{song.genre}",
            "tempo" : "{song.tempo}",
            "length" : "{song.length}",
            "comment" : "{song.comment}",
            "choree" : "{song.choral}",
            "url" : "{song.URL}"
        }},\n''')
    songs = songs[:-2]+"\n]"
    with open(f'data/{database_suffix}database.json', 'w') as f:
        f.write(songs)









css_colors_dict = {"#FFCC00" : "S_bkg" ,
              "#E8D1FF" : "A_bkg",
              "#99FF99" : "B_bkg",
              "#CCECFF" : "C_bkg",
              "#C4C4C4" : "D_or_I_bkg",
              "#FF9900" : "S_rank",
              "#CC66FF" : "Ap_rank",
              "#CC99FF" : "A_rank",
              "#00FF00" : "Bp_rank",
              "#66FF99" : "B_rank",
              "#19D3FF" : "Cp_rank",
              "#53D2FF" : "C_rank",
              "#A6A6A6" : "D_or_I_rank"}

def get_style_info(style, info):
    styles = style.split(';')
    for style in styles:
        if info in style:
            return style.split(':')[1].strip()

def get_css_color(css_color, rank=False):
    style_div = f"""
    #{css_colors_dict[css_color]} {{
        font-family: Calibri, sans-serif;
        color: #000000;
        background-color: {css_color};
        border-bottom-color: #000000;
        border-bottom-style: solid;
        border-bottom-width: 1px;
        border-collapse: collapse;
        border-left-color: #000000;
        border-left-style: solid;
        border-left-width: 1px;
        border-right-color: #000000;
        border-right-style: solid;
        border-right-width: 1px;
        border-top-color: #000000;
        border-top-style: solid;
        border-top-width: 1px;
        text-align: center;"""
    if not rank:
        style_div += """
        font-size: 14.0px;
        }"""
    else:
        style_div += """
        font-size: 18.2px;
        font-weight: bold;
        }\n"""
    return style_div


def make_html_tables(df, EN=False):
    if EN:
        sheet = "Sheet2"
        table_folder = "tables/EN"
    else:
        sheet = "Sheet1"
        table_folder = "tables"

    medias = [("YouTube", "yt"), ("Twitch", "tw"), ("Live", "live")]
    # medias = [("YouTube", "yt"), ("Twitch", "tw")]
    # medias = [("Live", "live")]
    # medias = [("Twitch", "tw")]
    for media, media_folder in medias:
        df_media = df.query(f"media=='{media}'")
        df_media = df_media[["htmlID","live_title"]].groupby("htmlID", sort=False).size().reset_index().rename(columns={0:"nSongs"})
        # print(df_media)
        print(f"Making {media}")
        row_start = 4
        for live in df_media.itertuples():
            print(live.htmlID)
            row_end = row_start + live.nSongs - 1
            xlsx2html(f"marc_{media_folder}.xlsx", f'data/{table_folder}/{media_folder}/{live.htmlID}.htm', row_range=(row_start, row_end), sheet=sheet)
            row_start = row_end + 2

            # Reduce table size
            with open(f'data/{table_folder}/{media_folder}/{live.htmlID}.htm') as fp:
                soup = BeautifulSoup(fp, 'html.parser')
            td_elements = soup.find_all('td')
            css_colors = []
            for td in td_elements:
                bkg_color = get_style_info(td["style"], 'background-color')
                if bkg_color not in css_colors:
                    css_colors.append(bkg_color)

            style_str = ""
            for css_color in css_colors:
                # print(css_colors_dict[css_color])
                if "rank" in css_colors_dict[css_color]:
                    style_str += get_css_color(css_color, rank=True)
                else:
                    style_str += get_css_color(css_color)
            style = soup.new_tag('style')
            style.string = style_str
            soup.head.append(style)

            for td in td_elements:
                td['id'] = css_colors_dict[get_style_info(td["style"], 'background-color')]
                td['style'] = f"height: {get_style_info(td['style'], 'height')}"

            updated_html = str(soup)
            file_path = f'data/{table_folder}/{media_folder}/{live.htmlID}.htm'

            with open(file_path, 'w') as file:
                file.write(updated_html)
            # break







########################################################## PLOTTING ##########################################################



def make_timing_plot(df2):
    print_simple_stats(df2)
    # Convert timedelta values to minutes:seconds representation
    df2['length_minutes'] = df2['length_DT'].dt.seconds // 60
    df2['length_seconds'] = df2['length_DT'].dt.seconds % 60

    # Group by "date_YM_DT" and calculate the mean of length
    grouped = df2[['length_minutes', 'length_seconds', 'date_YM_DT']].groupby('date_YM_DT').mean()

    # Reset the index to convert the "date_YM_DT" column back to a regular column
    grouped = grouped.reset_index()

    # Convert date_YM_DT to string format
    grouped['date_YM_DT'] = grouped['date_YM_DT'].dt.strftime('%Y-%m-%d')

    # Create x-axis values as datetime objects
    dates = pd.to_datetime(grouped['date_YM_DT'])

    # Normalize the length values between 0 and 1
    normalized_lengths = (grouped['length_minutes'] - grouped['length_minutes'].min()) / (
            grouped['length_minutes'].max() - grouped['length_minutes'].min())

    # Create a colormap with a gradient from blue to yellow
    colormap = plt.cm.get_cmap('YlOrRd')

    # Plot the data as a bar plot with color gradient
    fig, ax = plt.subplots()

    # Calculate the width of each bar dynamically based on the number of days in the month
    widths = []
    for date in dates:
        month = date.month
        year = date.year
        num_days = calendar.monthrange(year, month)[1]
        widths.append(num_days)

    bars = ax.bar(dates, grouped['length_minutes'], color=colormap(normalized_lengths), width=widths)

    ax.set_xlabel('Date')
    ax.set_ylabel('Mean song length per stream (minute)')
    # ax.set_title('Average Length over Time')

    # Format x-axis ticks as dates
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    plt.xticks(rotation=45)

    # Add a colorbar to show the color gradient
    # sm = plt.cm.ScalarMappable(cmap=colormap, norm=plt.Normalize(vmin=grouped['length_minutes'].min(),
    #                                                             vmax=grouped['length_minutes'].max()))
    # sm.set_array([])  # Hack to create an empty array for the colorbar
    # cbar = plt.colorbar(sm, ax=ax)
    # cbar.set_label('Mean song length per stream (minute)')
    # cbar.ax.set_ylabel(cbar.ax.get_ylabel(), rotation=-90)
    # cbar.ax.yaxis.set_label_coords(3.5, 0.5)

    plt.tight_layout()
    # plt.show()
    plt.savefig("plots/live_song_length.png")


def make_nsongs_plot(df2):
    # Group by "date_YM_DT" and calculate the mean of length
    grouped = df2[["date_YM_DT", "songID"]].groupby('date_YM_DT').count() / df2.drop_duplicates("htmlID")[["date_YM_DT","songID"]].groupby("date_YM_DT").count()


    # Reset the index to convert the "date_YM_DT" column back to a regular column
    grouped = grouped.reset_index()

    # Convert date_YM_DT to string format
    grouped['date_YM_DT'] = grouped['date_YM_DT'].dt.strftime('%Y-%m-%d')

    # Create x-axis values as datetime objects
    dates = pd.to_datetime(grouped['date_YM_DT'])

    # Normalize the length values between 0 and 1
    normalized_lengths = (grouped['songID'] - grouped['songID'].min()) / (
            grouped['songID'].max() - grouped['songID'].min())

    # Create a colormap with a gradient from blue to yellow
    colormap = plt.cm.get_cmap('Wistia')

    # Plot the data as a bar plot with color gradient
    fig, ax = plt.subplots()

    # Calculate the width of each bar dynamically based on the number of days in the month
    widths = []
    for date in dates:
        month = date.month
        year = date.year
        num_days = calendar.monthrange(year, month)[1]
        widths.append(num_days)

    bars = ax.bar(dates, grouped['songID'], color=colormap(normalized_lengths), width=widths)

    ax.set_xlabel('Date')
    ax.set_ylabel('Mean song number per stream')
    # ax.set_title('Average Length over Time')

    # Format x-axis ticks as dates
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    plt.xticks(rotation=45)

    # Add a colorbar to show the color gradient
    # sm = plt.cm.ScalarMappable(cmap=colormap, norm=plt.Normalize(vmin=grouped['songID'].min(),
    #                                                             vmax=grouped['songID'].max()))
    # sm.set_array([])  # Hack to create an empty array for the colorbar
    # cbar = plt.colorbar(sm, ax=ax)
    # cbar.set_label('Mean song number per stream')
    # cbar.ax.set_ylabel(cbar.ax.get_ylabel(), rotation=-90)
    # cbar.ax.yaxis.set_label_coords(3.5, 0.5)

    plt.tight_layout()
    # plt.show()
    plt.savefig("plots/live_song_number.png")


def make_livetype_plot(df2):
    # Group by "date_YM_DT" and calculate the count of htmlIDs for each media type
    grouped1 = df2.query("media == 'YouTube'").drop_duplicates("htmlID")[["date_YM_DT", "htmlID"]].groupby('date_YM_DT').count()
    grouped2 = df2.query("media == 'Twitch'").drop_duplicates("htmlID")[["date_YM_DT", "htmlID"]].groupby('date_YM_DT').count()
    grouped3 = df2.query("media == 'Live'").drop_duplicates("htmlID")[["date_YM_DT", "htmlID"]].groupby('date_YM_DT').count()
    grouped1 = grouped1.reset_index()
    grouped2 = grouped2.reset_index()
    grouped3 = grouped3.reset_index()
    # Combine the date columns of all groups and take unique values

    grouped1['date_YM_DT'] = grouped1['date_YM_DT'].dt.strftime('%Y-%m-%d')
    grouped2['date_YM_DT'] = grouped2['date_YM_DT'].dt.strftime('%Y-%m-%d')
    grouped3['date_YM_DT'] = grouped3['date_YM_DT'].dt.strftime('%Y-%m-%d')

    # Combine the date columns of all groups and take unique values
    dates = pd.concat([grouped1['date_YM_DT'], grouped2['date_YM_DT'], grouped3['date_YM_DT']]).unique()

    dates_for_plot = pd.to_datetime(dates)
    widths = []
    for date in dates_for_plot:
        month = date.month
        year = date.year
        num_days = calendar.monthrange(year, month)[1]
        widths.append(num_days-7)
    # Create empty arrays to store the song counts for each media type
    songs1 = []
    songs2 = []
    songs3 = []

    # Iterate through the unique dates and retrieve the corresponding song counts for each media type
    for date in dates:
        if date in str(grouped1['date_YM_DT']):
            songs1.append(grouped1[grouped1['date_YM_DT'] == date]['htmlID'].iloc[0])
        else:
            songs1.append(0)

        if date in str(grouped2['date_YM_DT']):
            songs2.append(grouped2[grouped2['date_YM_DT'] == date]['htmlID'].iloc[0])
        else:
            songs2.append(0)

        if date in str(grouped3['date_YM_DT']):
            songs3.append(grouped3[grouped3['date_YM_DT'] == date]['htmlID'].iloc[0])
        else:
            songs3.append(0)

    # Convert the arrays to numpy arrays
    songs1 = np.array(songs1)
    songs2 = np.array(songs2)
    songs3 = np.array(songs3)

    # Define custom RGB colors for each media type
    colors = [(255/255, 99/255, 71/255), (128/255, 54/255, 255/255), (255/255, 170/255, 155/255)]  # Blue, Green, Red

    # Plot the data as a stacked bar plot
    fig, ax = plt.subplots()

    bars1 = ax.bar(dates_for_plot, songs1, color=colors[0], width=widths, edgecolor='black', linewidth=0.4)
    bars2 = ax.bar(dates_for_plot, songs2, bottom=songs1, color=colors[1], width=widths, edgecolor='black', linewidth=0.4)
    bars3 = ax.bar(dates_for_plot, songs3, bottom=songs1 + songs2, color=colors[2], width=widths, edgecolor='black', linewidth=0.4)

    ax.set_xlabel('Date')
    ax.set_ylabel('Number of streams')
    # ax.set_title('Stacked Bar Plot with Media Types')

    # Format x-axis ticks as dates
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    plt.xticks(rotation=45)

    # Create custom legend handles
    legend_handles = [plt.Rectangle((0, 0), 1, 1, color=color) for color in colors]
    legend_labels = ['YouTube', 'Twitch', 'Public']

    plt.legend(legend_handles, legend_labels, loc='upper right')

    plt.tight_layout()
    # plt.show()
    plt.savefig("plots/nstreams_stacked_bar_plot.png")





def make_stream_length_plot(df2):
    # Convert timedelta values to minutes:seconds representation
    df2['length_minutes'] = df2['length_DT'].dt.seconds // 60
    df2['length_seconds'] = df2['length_DT'].dt.seconds % 60

    # Group by "date_YM_DT" and calculate the mean of length
    grouped = df2[["date_YM_DT", "length_DT"]].groupby('date_YM_DT').sum() / df2.drop_duplicates("htmlID")[["date_YM_DT","length_DT"]].groupby("date_YM_DT").count()

    # Reset the index to convert the "date_YM_DT" column back to a regular column
    grouped = grouped.reset_index()

    # Group by "date_YM_DT" and calculate the mean of length
    grouped['length_minutes'] = grouped['length_DT'].dt.seconds // 60
    grouped['length_seconds'] = grouped['length_DT'].dt.seconds % 60


    # Convert date_YM_DT to string format
    grouped['date_YM_DT'] = grouped['date_YM_DT'].dt.strftime('%Y-%m-%d')

    # Create x-axis values as datetime objects
    dates = pd.to_datetime(grouped['date_YM_DT'])

    # Normalize the length values between 0 and 1
    normalized_lengths = (grouped['length_minutes'] - grouped['length_minutes'].min()) / (
            grouped['length_minutes'].max() - grouped['length_minutes'].min())

    # Create a colormap with a gradient from blue to yellow
    colormap = plt.cm.get_cmap('YlOrRd')

    # Plot the data as a bar plot with color gradient
    fig, ax = plt.subplots()

    # Calculate the width of each bar dynamically based on the number of days in the month
    widths = []
    for date in dates:
        month = date.month
        year = date.year
        num_days = calendar.monthrange(year, month)[1]
        widths.append(num_days)

    bars = ax.bar(dates, grouped['length_minutes'], color=colormap(normalized_lengths), width=widths)

    ax.set_xlabel('Date')
    ax.set_ylabel('Mean stream length (minute)')
    # ax.set_title('Average Length over Time')

    # Format x-axis ticks as dates
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    plt.xticks(rotation=45)

    # Add a colorbar to show the color gradient
    # sm = plt.cm.ScalarMappable(cmap=colormap, norm=plt.Normalize(vmin=grouped['length_minutes'].min(),
    #                                                             vmax=grouped['length_minutes'].max()))
    # sm.set_array([])  # Hack to create an empty array for the colorbar
    # cbar = plt.colorbar(sm, ax=ax)
    # cbar.set_label('Mean stream length (minute)')
    # cbar.ax.set_ylabel(cbar.ax.get_ylabel(), rotation=-90)
    # cbar.ax.yaxis.set_label_coords(3.3, 0.5)

    plt.tight_layout()
    # plt.show()
    plt.savefig("plots/live_stream_length.png")



def make_rank_plots(filtered_df):
    # percentage_df = filtered_df[["date_YM_DT", "when_ranked_YM_DT", "rank"]].query("rank == 'S' or rank == 'A+' or rank == 'A'").groupby(['date_YM_DT', 'when_ranked_YM_DT']).count() / filtered_df[["date_YM_DT", "when_ranked_YM_DT", "rank"]].groupby(['date_YM_DT', 'when_ranked_YM_DT']).count()
    # percentage_df = filtered_df[["date_YM_DT", "when_ranked_YM_DT", "rank"]].query("rank == 'B' or rank == 'B+'").groupby(['date_YM_DT', 'when_ranked_YM_DT']).count() / filtered_df[["date_YM_DT", "when_ranked_YM_DT", "rank"]].groupby(['date_YM_DT', 'when_ranked_YM_DT']).count()
    percentage_df = filtered_df[["date_YM_DT", "when_ranked_YM_DT", "rank"]].query("rank == 'C' or rank == 'C+' or rank == 'D'").groupby(['date_YM_DT', 'when_ranked_YM_DT']).count() / filtered_df[["date_YM_DT", "when_ranked_YM_DT", "rank"]].groupby(['date_YM_DT', 'when_ranked_YM_DT']).count()

    filtered_df = filtered_df[['date_YM_DT', 'when_ranked_YM_DT']]


    # Merge the percentage data with the filtered_df DataFrame
    filtered_df = pd.merge(filtered_df, percentage_df, on=['date_YM_DT', 'when_ranked_YM_DT'], how="left")

    # Convert 'date_YM_DT' to month-year format
    filtered_df['date_YM_DT'] = filtered_df['date_YM_DT'].dt.strftime('%Y-%m')
    filtered_df['when_ranked_YM_DT'] = filtered_df['when_ranked_YM_DT'].dt.strftime('%Y-%m')

    # Pivot the filtered DataFrame to create a 2D grid for the heatmap
    pivot_df = filtered_df.pivot_table(index='when_ranked_YM_DT', columns='date_YM_DT', values="rank")

    # Set up the plot
    fig, ax = plt.subplots(figsize=(10, 8))

    # Create the heatmap using seaborn
    # sns.heatmap(pivot_df, annot=True, fmt='.0%', linewidths=0, cmap="YlOrRd", ax=ax)
    # sns.heatmap(pivot_df, annot=True, fmt='.0%', linewidths=0, cmap="YlGn", ax=ax)
    sns.heatmap(pivot_df, annot=True, fmt='.0%', linewidths=0, cmap="Blues", ax=ax)
    ax.invert_yaxis()
    # Add grid lines below the data
    ax.set_axisbelow(True)

    # Customize the grid lines
    ax.grid(True, linestyle='--', linewidth=0.5, color='gray', axis='both', zorder=0)

    # Add a colorbar
    cbar = ax.collections[0].colorbar
    # cbar.set_label('Percentage of songs with rank S, A+ or A in the stream')
    # cbar.set_label('Percentage of songs with rank B+ or B in the stream')
    cbar.set_label('Percentage of songs with rank C+, C or D in the stream')
    cbar.ax.set_ylabel(cbar.ax.get_ylabel(), rotation=-90)
    cbar.ax.yaxis.set_label_coords(2.6, 0.5)

    # Set the axis labels
    ax.set_xlabel('Date of the stream')
    ax.set_ylabel('Date when I ranked the stream')
    plt.xticks(rotation=80)

    # Adjust the x-axis tick labels
    # x_ticks = range(0, len(pivot_df.columns), 2)  # Select every 3rd index
    # x_labels = pivot_df.columns[::2]  # Select every 3rd label
    # ax.set_xticks(x_ticks)
    # ax.set_xticklabels(x_labels, rotation=45, ha='right')

    # Show the plot
    plt.tight_layout()
    plt.show()



def make_rank_nsong(df):
    # Define the categories and their corresponding values
    ranks = ['S', 'A+', 'A', 'B+', 'B', 'C+', 'C', 'D']
    values = []
    fig, ax = plt.subplots()

    for rank in ranks:
        values.append(len(df.query(f"rank == '{rank}'")))


    # Define the colors for each bar using hex color codes
    colors = ['#FF9900', '#CC66FF', '#CC99FF', '#00FF00', '#66FF99', '#19D3FF', '#53D2FF', '#A6A6A6']

    # Plot the bar graph with custom colors
    plt.bar(ranks, values, color=colors)

    # Set labels and title
    plt.xlabel('Rank')
    plt.ylabel('Number of songs')
    # plt.title('Bar Graph')

    # Rotate the x-axis labels if needed
    # plt.xticks(rotation=45)

    # Display the plot
    plt.savefig("plots/rank_nsong.png")
    # plt.show()


def make_rank_nsong_streamtype(df):
    categories = ['S', 'A+', 'A', 'B+', 'B', 'C+', 'C', 'D']
    values = []
    fig, ax = plt.subplots()

    for rank in categories:
        rank_values = []
        for media in ["YouTube", "Twitch", "Live"]:
            rank_values.append(len(df.query(f"rank == '{rank}' and media == '{media}'"))*100/len(df.query(f"media == '{media}'")))
        values.append(rank_values)
    colors = []
    for i in range(len(categories)):
        colors.append([(255/255, 99/255, 71/255), (128/255, 54/255, 255/255), (255/255, 170/255, 155/255)])

    num_bars = len(values[0])
    bar_width = 0.7
    x = np.arange(len(categories))

    for i, category in enumerate(categories):
        offset = -bar_width/3

        for j in range(num_bars):
            plt.bar(x[i] + offset + j * bar_width / num_bars, values[i][j], width=bar_width / num_bars,
                    color=colors[i][j])

    plt.ylabel('Percentage')
    plt.xlabel('Rank')

    legend_handles = [plt.Rectangle((0, 0), 1, 1, color=color) for color in colors[0]]

    plt.legend(legend_handles, ['YouTube', 'Twitch', 'Public'], loc="upper right")
    plt.xticks(x, categories)
    plt.savefig("plots/rank_nsong_streamtype.png")
    # plt.show()


def make_rank_length_streamtype(df):
    categories = ['S', 'A+', 'A', 'B+', 'B', 'C+', 'C', 'D']
    values = []

    for rank in categories:
        rank_values = []
        for media in ["YouTube", "Twitch", "Live"]:
            rank_values.append(df.query(f"rank == '{rank}' and media =='{media}' ")["length_DT"].mean())
        values.append(rank_values)
    colors = []
    for i in range(len(categories)):
        colors.append([(255/255, 99/255, 71/255), (128/255, 54/255, 255/255), (255/255, 170/255, 155/255)])

    fig, ax = plt.subplots()
    num_bars = len(values[0])
    bar_width = 0.7
    x = np.arange(len(categories))
    # print(values)

    for i, category in enumerate(categories):
        offset = -bar_width/3

        for j in range(num_bars):
            numerical_value = values[i][j].total_seconds() / 60
            plt.bar(x[i] + offset + j * bar_width / num_bars, numerical_value, width=bar_width / num_bars,
                    color=colors[i][j])

    plt.xlabel('Rank')
    plt.ylabel('Mean song length (minute)')

    legend_handles = [plt.Rectangle((0, 0), 1, 1, color=color) for color in colors[0]]

    plt.legend(legend_handles, ['YouTube', 'Twitch', 'Public'], loc="upper right")
    plt.xticks(x, categories)
    plt.savefig("plots/rank_length_streamtype.png")
    # plt.show()



def make_tempo_nsong(df):
    # Define the categories and their corresponding values
    tempos = ['Slow or Smed', "Med", "Fmed or Fast"]
    values = []
    fig, ax = plt.subplots()

    # for tempo in tempos:
    #     values.append(len(df.query(f"tempo == '{tempo}'")))

    values.append(len(df.query(f"tempo == 'Slow' or tempo == 'Smed'")))
    values.append(len(df.query(f"tempo == 'Med'")))
    values.append(len(df.query(f"tempo == 'Fmed' or tempo == 'Fast'")))


    # Define the colors for each bar using hex color codes
    colors = ['#000000']

    # Plot the bar graph with custom colors
    plt.bar(tempos, values, color=colors)

    # Set labels and title
    plt.xlabel('Tempo')
    plt.ylabel('Number of songs')
    # plt.title('Bar Graph')

    # Rotate the x-axis labels if needed
    # plt.xticks(rotation=45)

    # Display the plot
    plt.savefig("plots/tempo_nsong.png")
    # plt.show()


def make_tempo_nsong_streamtype(df):
    categories = [['Slow', 'Smed'], ["Med"], ["Fmed", "Fast"]]
    values = []
    fig, ax = plt.subplots()

    for tempo in categories:
        tempo_values = []
        for media in ["YouTube", "Twitch", "Live"]:
            tempo_values.append(len(df.query(f"tempo in {tempo} and media == '{media}'"))*100/len(df.query(f"media == '{media}'")))
        values.append(tempo_values)
    colors = []
    for i in range(len(categories)):
        colors.append([(255/255, 99/255, 71/255), (128/255, 54/255, 255/255), (255/255, 170/255, 155/255)])

    num_bars = len(values[0])
    bar_width = 0.7
    x = np.arange(len(categories))

    for i, category in enumerate(categories):
        offset = -bar_width/3

        for j in range(num_bars):
            plt.bar(x[i] + offset + j * bar_width / num_bars, values[i][j], width=bar_width / num_bars,
                    color=colors[i][j])

    plt.ylabel('Percentage')
    plt.xlabel('tempo')

    legend_handles = [plt.Rectangle((0, 0), 1, 1, color=color) for color in colors[0]]

    plt.legend(legend_handles, ['YouTube', 'Twitch', 'Public'], loc="upper right")
    plt.xticks(x, categories)
    plt.savefig("plots/tempo_nsong_streamtype.png")
    # plt.show()








########################################################## DL ##########################################################
from pytube import YouTube
from pytube.cli import on_progress
from pydub import AudioSegment

dl_dir = "streams_dl"


def extract_audio_segment(input_file, output_file, start_time, end_time):
    audio = AudioSegment.from_file(input_file, format="webm")
    segment = audio[start_time * 1000:end_time * 1000]
    segment.export(output_file, format='mp3')

def format_stream_title(live_title):
    for c in ["|", ".", "'"]:
        live_title = live_title.replace(c, "")
    return live_title

def get_stream_info(df, info, drop_on="live_title"):
    return list(df.drop_duplicates(drop_on)[info])[0]

def get_twitch_timing(formatted_timing):
    hours = int(formatted_timing[:formatted_timing.index("h")])
    minutes = int(formatted_timing[formatted_timing.index("h")+1:formatted_timing.index("m")])
    seconds = int(formatted_timing[formatted_timing.index("m")+1:formatted_timing.index("s")])
    return hours*60*60 + minutes*60 + seconds

def download_songs_from_streams(df, stream_titles=[]):
    for stream_title in stream_titles:
        df_stream = df.query(f'live_title=="{stream_title}"')
        stream_title = format_stream_title(stream_title)
        stream_title = f'{get_stream_info(df_stream, "htmlID")} {stream_title}'
        stream_dir = f"{dl_dir}/{stream_title}"
        os.makedirs(stream_dir, exist_ok=True)

        stream_media = get_stream_info(df_stream, "media")
        if stream_media == "Twitch":
            file_format = "mkv"
        else:
            file_format = "webm"

        if not os.path.exists(f"{stream_title}.{file_format}"):
            if not os.path.exists(f"{stream_dir}/{stream_title}.{file_format}"):
                print(f"Start DL {stream_title}.")
                live_first_url = get_stream_info(df_stream, "URL")
                if stream_media in ["YouTube", "Live"]: # TODO: Change if Live also on Twitch (soon)
                    YouTube(live_first_url, on_progress_callback=on_progress).streams.filter(only_audio=True).order_by('abr').desc().first().download(filename=f"{stream_title}.webm")
                    # If video download (not implemented)
                    # YouTube(f'http://youtube.com/watch?v={live_code}', on_progress_callback=on_progress).streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first().download()
                else:
                    os.system(f'twitch-dl download {live_first_url} -q audio_only -o "{stream_title}.mkv"')
                print(f'{stream_title} DL.')

        # No need
        # if stream_media == "Twitch" and os.path.exists(f"{formatted_stream_title}.{file_format}"):
        #     print(f'Converting {stream_title} mkv to webm.')
        #     os.system(f'ffmpeg -i "{stream_title}.mkv"  -vn -c:a libopus -b:a 128k {stream_title}.webm') # TODo: not hardcoded bitrate

        if not os.path.exists(f"{stream_dir}/{stream_title}.{file_format}"):
            os.system(f'mv "{stream_title}.{file_format}" "{stream_dir}/{stream_title}.{file_format}"')
            print(f'{stream_title} correctly moved.')

        k_song = 0
        print(f'Start downloading songs from {stream_title}.')
        for index, song in df_stream.iterrows():
            k_song+=1
            song_name = f'{k_song}. {df.iloc[index]["name"]}'
            if os.path.exists(f"{stream_dir}/{song_name}.mp3"):
                print(f'{song_name} skipped.')
                continue
            try:
                if stream_media in ["YouTube", "Live"]:
                    start_time = int(song.URL[song.URL.index("t=")+2:])
                else:
                    start_time = get_twitch_timing(song.URL[song.URL.index("t=")+2:])
            except ValueError:
                start_time = 0
            next_song = df.iloc[index+1]
            if next_song["name"][0] == "-":
                if stream_media in ["YouTube", "Live"]:
                    end_time = int(next_song["URL"][next_song["URL"].index("t=")+2:])
                else:
                    start_time = get_twitch_timing(next_song["URL"][next_song["URL"].index("t=")+2:])
            else:
                end_time = start_time + song.length_DT.seconds+3
            # print(song.URL)
            print(f"{song_name} - [{start_time} : {end_time}]")
            extract_audio_segment(f"{stream_dir}/{stream_title}.{file_format}", f"{stream_dir}/{song_name}.mp3", start_time, end_time)
            print(f"  - DL")
    print("Done.")