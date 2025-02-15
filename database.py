from xlsx2html import xlsx2html
from bs4 import BeautifulSoup
import json
from pythumb import Thumbnail
import subprocess
from magic import *
import os
import yaml

num_to_months = {
    1: "Janvier",
    2: "Février",
    3: "Mars",
    4: "Avril",
    5: "Mai",
    6: "Juin",
    7: "Juillet",
    8: "Août",
    9: "Septembre",
    10: "Octobre",
    11: "Novembre",
    12: "Décembre",
}

num_to_months_EN = {
    1: "January",
    2: "February",
    3: "March",
    4: "April",
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
    10: "October",
    11: "November",
    12: "December",
}


css_colors_dict = {
    "#FFCC00": "S_bkg",
    "#E8D1FF": "A_bkg",
    "#99FF99": "B_bkg",
    "#CCECFF": "C_bkg",
    "#C4C4C4": "D_or_I_bkg",
    "#FF9900": "S_rank",
    "#CC66FF": "Ap_rank",
    "#CC99FF": "A_rank",
    "#00FF00": "Bp_rank",
    "#66FF99": "B_rank",
    "#19D3FF": "Cp_rank",
    "#53D2FF": "C_rank",
    "#A6A6A6": "D_or_I_rank",
    "#A6A6A6": "I_rank",
    "#A6A6A6": "D_rank",
}

tempo_txt_dict = {
    "Med": "medium",
    "Fast": "fast",
    "Slow": "slow",
    "Fmed": "medium fast",
    "Smed": "medium slow",
}


def get_date_verbose(date_DT, EN=False):
    """
    Returns a verbose date string in either English or another language.

    Parameters:
    date_DT (datetime.datetime): The date to be formatted.
    EN (bool): A flag to determine if the date should be formatted in English.
               If False, uses the French language.

    Returns:
    str: The formatted date string.
    """
    # Select the appropriate month mapping based on the language flag
    if EN:
        num_to_months_used = num_to_months_EN
    else:
        num_to_months_used = num_to_months

    suffix = ""
    # Determine the appropriate suffix for the day if in English
    if EN:
        if date_DT.day in [1, 21, 31]:
            suffix = "st"
        elif date_DT.day in [2, 22]:
            suffix = "nd"
        elif date_DT.day in [3, 23]:
            suffix = "rd"
        else:
            suffix = "th"

    # Return the formatted date string
    return f"{date_DT.day}{suffix} {num_to_months_used[date_DT.month]} {date_DT.year}"


def get_live_code(url):
    """
    Extracts the live code from a given URL.

    Parameters:
    url (str): The URL from which to extract the live code.

    Returns:
    str: The extracted live code.
    """
    # Extract the live code based on different URL patterns
    if ".be" in url:
        live_code = url[url.index(".be") + 4 :]
    elif "live/" in url:
        live_code = url[url.index("live/") + 5 : url.index("live/") + 5 + 11]
    elif "v=" in url:
        live_code = url[url.index("v=") + 2 :]

    # Remove any time parameter from the live code
    if "t=" in live_code:
        live_code = live_code[: live_code.index("t=") - 1]

    return live_code


def get_date_short(htmlID):
    """
    Extracts the date string from the htmlID based on the media type.

    Parameters:
    htmlID (str): The htmlID of the song.

    Returns:
    str: The extracted date string.
    """
    if any(char.isupper() for char in htmlID):
        # Remove uppercase letters from htmlID
        htmlID = "".join(char for char in htmlID if not char.isupper())

    if "l" in htmlID or "t" in htmlID:
        date = htmlID[1:-1]
    else:
        date = htmlID[1:]
    date = "20" + date[:2] + "-" + date[2:4] + "-" + date[4:]
    return date


def output_newdatabase_JSON(df, EN=False):
    """
    Generates a JSON representation of the song database and writes it to a file.

    Parameters:
    df (pd.DataFrame): The DataFrame containing song data.
    EN (bool): A flag to determine if the JSON file should be in English.
               If False, uses French.

    Writes:
    JSON content to a file named 'newdatabase.json' or 'EN_newdatabase.json' based on the language flag.
    """

    albums = []
    current_live = {"title": None}

    # Iterate through each song in the DataFrame and generate JSON content
    for n_song, song in enumerate(df.itertuples()):
        new_live_title = song.live_title
        if new_live_title != current_live["title"]:
            print(f"Processing new live: {new_live_title}")
            if current_live.get("title") is not None:
                albums.append(current_live)

            current_live = {
                "id": song.htmlID,
                "title": song.live_title,
                "date": get_date_verbose(song.date_DT, EN),
                "date_DT": song.date_DT,
                "date_short": get_date_short(song.htmlID),
                "when_ranked": get_date_verbose(song.when_ranked_DT, EN),
                "comment": song.live_comment,
                "picture_link": None,
                "songs": [],
            }

            # If the thumbnail is not in data/thumbnails.yaml, update the htmlID : picture_link in the file
            with open("data/thumbnails.yaml", "r") as f:
                thumbnails = yaml.safe_load(f)

            if song.htmlID not in thumbnails:
                if "twitch" in song.URL:
                    current_live["picture_link"] = subprocess.run(
                        [
                            "youtube-dl",
                            "--get-thumbnail",
                            song.URL,
                        ],
                        check=True,
                        capture_output=True,
                        text=True,
                    ).stdout
                else:
                    current_live["picture_link"] = Thumbnail(
                        f"https://www.youtube.com/watch?v={get_live_code(song.URL)}"
                    ).fetch(url=True)

                thumbnails[song.htmlID] = current_live["picture_link"]
                with open("data/thumbnails.yaml", "w") as f:
                    yaml.dump(thumbnails, f)

            current_live["picture_link"] = thumbnails[song.htmlID]

        current_live["songs"].append(
            {
                "name": song.name,
                "rank": song.rank,
                "genre": song.genre,
                "length": song.length,
                "tempo": tempo_txt_dict[song.tempo],
                "comment": song.comment,
                "choree": song.choral,
                "url": song.URL,
            }
        )

    if current_live is not None:
        albums.append(current_live)

    # Sort albums by date
    albums = sorted(albums, key=lambda x: x["date_DT"])

    # remove date_DT
    for album in albums:
        del album["date_DT"]

    albums.reverse()

    data = {"albums": albums}

    # Write the generated JSON content to the database file
    os.makedirs(folder, exist_ok=True)
    if EN:
        with open(database_en, "w") as f:
            json.dump(data, f, indent=4)
        print(f"Database saved to {database_en}")
    else:
        with open(database_fr, "w") as f:
            json.dump(data, f, indent=4)
        print(f"Database saved to {database_fr}")


def get_HOF_info(songsName, df):
    HOF_info = []

    for songName in songsName:
        found = False
        print(f"Searching for {songName}")
        for n_song, song in enumerate(df.itertuples()):
            if song.name == songName:
                HOF_info.append((song.htmlID, song.name))
                found = True
        if not found:
            HOF_info.append(f"{songName} not found in the database")
    for info in HOF_info:
        print(info)
    return HOF_info


#### OLD FUNCTIONS, kept for legacy


def get_ranked_date_prompt(date_DT, EN=False):
    """
    Returns a prompt string indicating the ranked date in either English or another language.

    Parameters:
    date_DT (datetime.datetime): The date to be formatted.
    EN (bool): A flag to determine if the prompt should be in English.
               If False, uses the default language.

    Returns:
    str: The formatted prompt string.
    """
    # Select the appropriate month mapping and prompt based on the language flag
    if EN:
        num_to_months_used = num_to_months_EN
        prompt = "Ranked around"
    else:
        num_to_months_used = num_to_months
        prompt = "Noté vers"

    # Return the formatted prompt string
    return f"{prompt} {num_to_months_used[date_DT.month]} {date_DT.year}"


def output_html(df, EN=False):
    """
    Generates HTML content for different media types and writes it to text files.

    Parameters:
    df (pd.DataFrame): The DataFrame containing song data.
    EN (bool): A flag to determine if the content should be in English.
               If False, uses the default language.

    Writes:
    HTML content to text files for each media type and a parallax configuration file.
    """
    # Sort the DataFrame by date and remove duplicates based on htmlID
    df = df.sort_values("date_DT", ascending=False).drop_duplicates(["htmlID"])

    parallax_line = ""
    parallax_bg_lines = ""

    # Iterate through each media type and generate HTML content
    for media, media_folder in [("YouTube", "yt"), ("Live", "live"), ("Twitch", "tw")]:
        media_suffix = "EN_" if EN else ""

        # Clear the content of the media-specific file
        with open(f"data/{media_suffix}{media}.txt", "w") as f:
            f.close()

        # Filter the DataFrame for the current media type
        df_media = df.query(f"media=='{media}'")

        live_div = ""
        # Generate HTML content for each live entry
        for live in df_media.itertuples():
            parallax_line += f".parallax{live.htmlID}, "
            if media == "Twitch":
                parallax_bg_lines += f'\t\t\t.parallax{live.htmlID} {{background-image:url("thumbnails/tw/{live.htmlID}.jpg");}}\n'
            else:
                parallax_bg_lines += f'\t\t\t.parallax{live.htmlID} {{background-image:url("https://i.ytimg.com/vi/{get_live_code(live.URL)}/maxresdefault.jpg");}}\n'

            live_div += f'\n\n\n\t\t\t<div class="parallax{live.htmlID}"; id="{live.htmlID}"></div>\n\n'
            live_div += f"\t\t\t<span>{live.live_title} &nbsp; <b>- {get_date_verbose(live.date_DT, EN)} -</b> &nbsp; <bb>{get_ranked_date_prompt(live.when_ranked_YM_DT, EN)}</bb></span>\n"
            if live.live_comment != "-":
                live_div += f"\t\t\t<p>{live.live_comment}</p>\n"
            live_div += "\t\t\t<br><br>\n"
            live_div += f'\t\t\t<div data-include="tables/{media_folder}/{live.htmlID}"></div>\n'
            live_div += "\t\t\t<br><br><br>"

        # Write the generated HTML content to the media-specific file
        with open(f"data/{media_suffix}{media}.txt", "w") as f:
            f.write(live_div)

    # Write the parallax configuration to a file
    with open(f"data/parallax.txt", "w") as f:
        f.write(parallax_line[:-2] + "\n" * 5)
        f.write(parallax_bg_lines)


def output_database_JSON(df, EN=False):
    """
    Generates a JSON representation of the song database and writes it to a file.

    Parameters:
    df (pd.DataFrame): The DataFrame containing song data.
    EN (bool): A flag to determine if the JSON file should be in English.
               If False, uses the default language.

    Writes:
    JSON content to a file named 'database.json' or 'EN_database.json' based on the language flag.
    """
    # Determine the suffix for the database file based on the language flag
    database_suffix = "EN_" if EN else ""

    # Clear the content of the database file
    with open(f"data/{database_suffix}database.json", "w") as f:
        f.close()

    songs = "["

    # Iterate through each song in the DataFrame and generate JSON content
    for song in df.itertuples():
        songs += f"""
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
        }},\n"""

    # Remove the trailing comma and newline, and close the JSON array
    songs = songs[:-2] + "\n]"

    # Write the generated JSON content to the database file
    with open(f"data/{database_suffix}database.json", "w") as f:
        f.write(songs)


# Make the HTML tables from the Excel files
def get_style_info(style, info):
    """
    Extracts the value of a specific style attribute from a style string.

    Parameters:
    style (str): The style string containing multiple style attributes separated by semicolons.
    info (str): The specific style attribute to extract the value for.

    Returns:
    str: The value of the specified style attribute, or None if the attribute is not found.
    """
    styles = style.split(";")
    for style in styles:
        if info in style:
            return style.split(":")[1].strip()


def get_css_color(css_color, rank=False):
    """
    Generates a CSS style block for a given color and optional rank.

    Parameters:
    css_color (str): The background color to be used in the CSS style.
    rank (bool): A flag to determine if the style is for a rank.
                 If False, uses a smaller font size. If True, uses a larger font size and bold font weight.

    Returns:
    str: The generated CSS style block.
    """
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

    # Add font size and weight based on the rank flag
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
    """
    Generates HTML tables from an Excel file and writes them to files.

    Parameters:
    df (pd.DataFrame): The DataFrame containing song data.
    EN (bool): A flag to determine if the content should be in English.
               If False, uses the default language.

    Writes:
    HTML tables to files for each media type.
    """
    # Determine the sheet and table folder based on the language flag
    if EN:
        sheet = "Sheet2"
        table_folder = "tables/EN"
    else:
        sheet = "Sheet1"
        table_folder = "tables"

    medias = [("YouTube", "yt"), ("Twitch", "tw"), ("Live", "live")]

    # Iterate through each media type and generate HTML tables
    for media, media_folder in medias:
        df_media = df.query(f"media=='{media}'")
        df_media = (
            df_media[["htmlID", "live_title"]]
            .groupby("htmlID", sort=False)
            .size()
            .reset_index()
            .rename(columns={0: "nSongs"})
        )
        print(f"Making {media}")
        row_start = 4

        # Generate HTML table for each live entry
        for live in df_media.itertuples():
            print(live.htmlID)
            row_end = row_start + live.nSongs - 1
            xlsx2html(
                f"marc_{media_folder}.xlsx",
                f"data/{table_folder}/{media_folder}/{live.htmlID}.htm",
                row_range=(row_start, row_end),
                sheet=sheet,
            )
            row_start = row_end + 2

            # Read the generated HTML content from the file
            with open(f"data/{table_folder}/{media_folder}/{live.htmlID}.htm") as fp:
                soup = BeautifulSoup(fp, "html.parser")
            td_elements = soup.find_all("td")
            css_colors = []

            # Collect unique background colors from table cells
            for td in td_elements:
                bkg_color = get_style_info(td["style"], "background-color")
                if bkg_color not in css_colors:
                    css_colors.append(bkg_color)

            # Generate custom CSS styles for the collected colors
            style_str = ""
            for css_color in css_colors:
                if "rank" in css_colors_dict[css_color]:
                    style_str += get_css_color(css_color, rank=True)
                else:
                    style_str += get_css_color(css_color)
            style = soup.new_tag("style")
            style.string = style_str
            soup.head.append(style)

            # Update table cell styles and IDs
            for td in td_elements:
                td["id"] = css_colors_dict[
                    get_style_info(td["style"], "background-color")
                ]
                td["style"] = f"height: {get_style_info(td['style'], 'height')}"

            # Write the updated HTML content to the file
            updated_html = str(soup)
            file_path = f"data/{table_folder}/{media_folder}/{live.htmlID}.htm"

            with open(file_path, "w") as file:
                file.write(updated_html)


### DEPRECATED: old and fastidious way to generate the database


def output_database(df, EN=False):
    """
    Generates JavaScript code to create Song objects and writes it to a text file.

    Parameters:
    df (pd.DataFrame): The DataFrame containing song data.
    EN (bool): A flag to determine if the content should be in English.
               If False, uses the French language.

    Writes:
    JavaScript code to a file named 'database.txt' or 'EN_database.txt' based on the language flag.
    """
    # Determine the suffix for the database file based on the language flag
    databse_suffix = "EN_" if EN else ""

    # Clear the content of the database file
    with open(f"data/{databse_suffix}database.txt", "w") as f:
        f.close()

    songIDs = ""

    # Write JavaScript code to create Song objects and a song list
    with open(f"data/{databse_suffix}database.txt", "w") as f:
        for song in df.itertuples():
            f.write(
                f'\t\t\tconst {song.songID} = new Song("{song.htmlID}", "{song.name}", "{song.rank.replace("+","p")}", "{song.genre}", "{song.tempo}", "{song.length}", "{song.comment}", "{song.choral}", "{song.URL}");\n'
            )
            songIDs += f"{song.songID}, "
        songIDs = songIDs[:-2]
        f.write(f"\t\t\tvar songList = [{songIDs}];")

    # Print streams added if not in English
    if not EN:
        print_streams_added(df, songIDs)


def print_streams_added(df, songIDs):
    """
    Prints the number of new live streams added since the last update.

    Parameters:
    df (pd.DataFrame): The DataFrame containing song data.
    songIDs (str): A comma-separated string of song IDs.

    Prints:
    The number of new live streams added and their titles.
    """
    # Read the old list of song IDs from the file
    with open(f"oldList.txt", "r") as f:
        old_songIDs = f.readline().split(", ")

    # Split the new song IDs into a list
    songIDs = songIDs.split(", ")

    live_added = []

    # Determine the new song IDs that were added
    for songID in list(set(songIDs) - set(old_songIDs)):
        live_title = df.query(f"songID=='{songID}'").iloc[-1]["live_title"]
        if live_title not in live_added:
            live_added.append(live_title)

    # Print the number of new live streams added and their titles
    print(f"{len(live_added)} live added since last time: {live_added}")
    print("\n(Don't forget to update oldList!)\n")
