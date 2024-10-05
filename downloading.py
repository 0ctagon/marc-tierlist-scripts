from pytube import YouTube
from pytube.cli import on_progress
from yt_dlp import YoutubeDL
from pydub import AudioSegment
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TRCK, TDRC, TCON, COMM, APIC
import shlex
import subprocess
from pythumb import Thumbnail
import os
import sys
from database import get_live_code

dl_dir = "streams_dl"
icloud_dir = "mp3_playlists/icloud"


def extract_audio_segment(input_file, output_file, start_time, end_time):
    """
    Extracts a segment from an audio file and exports it as an MP3 file.

    Parameters:
    input_file (str): The path to the input audio file in webm format.
    output_file (str): The path to the output audio file in mp3 format.
    start_time (float): The start time of the segment to extract, in seconds.
    end_time (float): The end time of the segment to extract, in seconds.

    Writes:
    The extracted audio segment to the specified output file in mp3 format.
    """
    audio = AudioSegment.from_file(input_file, format="webm")
    segment = audio[start_time * 1000 : end_time * 1000]
    segment.export(output_file, format="mp3")


def format_stream_title(live_title):
    """
    Formats the live stream title by removing specific characters.

    Parameters:
    live_title (str): The original live stream title.

    Returns:
    str: The formatted live stream title with specified characters removed.
    """
    for c in ["|", ".", "'", "/"]:
        live_title = live_title.replace(c, "")
    return live_title


def get_stream_info(df, info, drop_on="live_title"):
    """
    Retrieves the first unique value of a specified column from a DataFrame.

    Parameters:
    df (pd.DataFrame): The DataFrame containing stream data.
    info (str): The column name from which to retrieve the value.
    drop_on (str): The column name to drop duplicates on. Default is "live_title".

    Returns:
    The first unique value from the specified column after dropping duplicates.
    """
    return list(df.drop_duplicates(drop_on)[info])[0]


def get_twitch_timing(formatted_timing):
    """
    Converts a formatted Twitch timing string into total seconds.

    Parameters:
    formatted_timing (str): The formatted timing string (e.g., "1h23m45s").

    Returns:
    int: The total time in seconds.
    """
    hours = int(formatted_timing[: formatted_timing.index("h")])
    minutes = int(formatted_timing[formatted_timing.index("h") + 1 : formatted_timing.index("m")])
    seconds = int(formatted_timing[formatted_timing.index("m") + 1 : formatted_timing.index("s")])
    return hours * 60 * 60 + minutes * 60 + seconds


def get_youtube_timing(URL):
    """
    Extracts the timing parameter from a YouTube URL and converts it to an integer.

    Parameters:
    URL (str): The YouTube URL containing the timing parameter.

    Returns:
    int: The timing parameter in seconds.
    """
    timing = URL[URL.index("t=") + 2 :]
    try:
        timing = timing[: timing.index("s")]
    except:
        pass
    return int(timing)


def check_timings_bug(timings):
    """
    Checks for bugs in the provided timings list.

    Parameters:
    timings (list): A list of tuples where each tuple contains a start time and an end time.

    Returns:
    bool: True if a bug is found in the timings, False otherwise.
    """
    if len(timings) == 1:
        return False
    else:
        start_time = timings[-1][0]
        end_time = timings[-1][1]
        if end_time <= start_time:
            return True
        for timing in timings[:-1]:
            if timing[1] > end_time:
                print("\n########## WARNING ##########\n")
            if timing[0] > start_time:
                return True
    return False


def get_date_for_mp3(htmlID):
    """
    Converts an htmlID to a formatted date string for an MP3 file.

    Parameters:
    htmlID (str): The htmlID to be converted.

    Returns:
    str: The formatted date string in the format "YYYY-MM-DD".
    """
    if len(htmlID) == 7:
        htmlID = htmlID[1:]
    else:
        htmlID = htmlID[1:-1]
    return f"20{htmlID[:2]}-{htmlID[2:4]}-{htmlID[4:]}"


def change_mp3_metadata(
    mp3_file,
    title,
    artist,
    album,
    track_number,
    recording_date,
    genre,
    comments=None,
    image_path=None,
):
    """
    Changes the metadata of an MP3 file.

    Parameters:
    mp3_file (str): The path to the MP3 file.
    title (str): The title of the track.
    artist (str): The artist of the track.
    album (str): The album name.
    track_number (str): The track number.
    recording_date (str): The recording date.
    genre (str): The genre of the track.
    comments (str, optional): Any comments to add to the metadata. Default is None.
    image_path (str, optional): The path to the album art image. Default is None.

    Modifies:
    The metadata of the specified MP3 file.
    """
    audio = ID3(mp3_file)

    # Modify the title metadata
    audio["TIT2"] = TIT2(encoding=3, text=title)
    # Modify the artist metadata
    audio["TPE1"] = TPE1(encoding=3, text=artist)
    # Modify the album metadata
    audio["TALB"] = TALB(encoding=3, text=album)
    # Modify the track number metadata
    audio["TRCK"] = TRCK(encoding=3, text=track_number)
    # Modify the recording date metadata
    audio["TDRC"] = TDRC(encoding=3, text=recording_date)
    # Modify the genre metadata
    audio["TCON"] = TCON(encoding=3, text=genre)
    # Modify the comments metadata
    if comments is not None:
        audio["COMM"] = COMM(encoding=3, lang="eng", desc="", text=comments)

    # Modify the album art metadata
    if image_path is not None:
        with open(image_path, "rb") as album_art:
            audio["APIC"] = APIC(
                encoding=3,
                mime="image/jpeg",
                type=3,
                desc="Cover",
                data=album_art.read(),
            )

    audio.save()


# TODO: this thing needs refactoring
def download_songs_from_streams(df, stream_titles=[], make_songs=True, make_playlist_rank=None):
    """
    Downloads songs from specified streams and processes them into individual MP3 files.

    Parameters:
    df (pd.DataFrame): The DataFrame containing song data.
    stream_titles (list): A list of stream titles to download songs from.
    make_songs (bool): A flag to determine if individual songs should be processed. Default is True.
    make_playlist_rank (list): A list of ranks to create playlists for. Default is None.

    Writes:
    MP3 files for each song in the specified streams and optionally creates playlists based on ranks.
    """
    for stream_title in stream_titles:
        df_stream = df.query(f'live_title=="{stream_title}"')
        stream_title = format_stream_title(stream_title)
        stream_title = f'{get_stream_info(df_stream, "htmlID")[1:]} {stream_title}'
        stream_dir = f"{dl_dir}/{stream_title}"
        os.makedirs(stream_dir, exist_ok=True)

        stream_media = get_stream_info(df_stream, "media")
        if stream_media == "Twitch":
            file_format = "mkv"
        else:
            file_format = "webm"

        # Download the stream if it doesn't already exist
        if not os.path.exists(f"{stream_title}.{file_format}"):
            if not os.path.exists(f"{stream_dir}/{stream_title}.{file_format}"):
                print(f"Start DL {stream_title}.")
                live_first_url = get_stream_info(df_stream, "URL")
                live_code = get_live_code(live_first_url)
                if live_code == "EuYRPNdy2b0":
                    live_code = "1t_ML-2QJTQ"
                if stream_media in [
                    "YouTube",
                    "Live",
                ]:  # TODO: Change if Live also on Twitch (soon)
                    # YouTube(live_first_url, on_progress_callback=on_progress).streams.filter(only_audio=True).order_by('abr').desc().first().download(filename=f"{stream_title}.webm")
                    os.system(f'yt-dlp -f "ba" -o "{stream_title}.webm" --force-overwrites "{live_code}"')
                else:
                    os.system(f'twitch-dl download "{live_first_url}" -q audio_only -o "{stream_title}.mkv"')
                print(f"{stream_title} DL.")

        # Move the downloaded file to the stream directory if not already there
        if not os.path.exists(f"{stream_dir}/{stream_title}.{file_format}"):
            os.system(f'mv "{stream_title}.{file_format}" "{stream_dir}/{stream_title}.{file_format}"')
            print(f"{stream_title} correctly moved.")

        k_song = 0
        last_end_time = 0
        timings = []

        # Skip streams that are too long to be processed
        if not make_songs or stream_title in [
            "201209 ONE MILLION SUBS LIVE STREAM",  # Too long
            "180211 5,000 SUBSCRIBER SPECIAL PT 1 (FULL STREAM)",  # Too long
            "171217 December 17, 2017 (FULL STREAM)",  # Invalid data??
            "170708 BORED CERTIFIED: EPISODE 3 (FULL STREAM)",  # Too long
            "170629 BORED CERTIFIED: EPISODE 2",  # Invalid data
            "180212l 5,000 SUBSCRIBER SPECIAL PT 2 (FULL STREAM)",  # Too long
        ]:
            print(f"{stream_title} skipped.\n")
            continue

        print(f"Start downloading songs from {stream_title}.")
        n_songs = len(df_stream)

        # Create playlist folders if specified
        if make_playlist_rank is not None:
            playlist_folders = []
            for ranks in make_playlist_rank:
                playlist_folders.append("".join(ranks))
                os.makedirs(f"mp3_playlists/{''.join(ranks)}", exist_ok=True)

        # Process each song in the stream
        for index, song in df_stream.iterrows():
            k_song += 1
            song_name = f'{k_song}. {df.iloc[index]["name"]}'.replace("/", "")
            if os.path.exists(f"{stream_dir}/{song_name}.mp3"):
                if make_playlist_rank is not None:
                    for k, ranks in enumerate(make_playlist_rank):
                        playlist_folder = playlist_folders[k]
                        for rank in ranks:
                            rank = rank.replace("p", "+")
                            if df.iloc[index]["rank"] == rank:
                                new_song_name = (
                                    get_stream_info(df_stream, "htmlID")[1:] + " " + " ".join(song_name.split(" ")[1:])
                                )
                                os.system(
                                    f'ln -s "{stream_dir}/{song_name}.mp3" "mp3_playlists/{playlist_folder}/{new_song_name}.mp3"'
                                )
                                print(f"Added mp3_playlists/{playlist_folder}/{new_song_name}.mp3.")
                # print(f'{song_name} skipped.')
                continue

            if index + 1 < n_songs:
                next_song = df.iloc[index + 1]

            # Determine the start and end times for the song
            try:
                if stream_media in ["YouTube", "Live"]:
                    start_time = get_youtube_timing(song.URL)
                else:
                    start_time = get_twitch_timing(song.URL[song.URL.index("t=") + 2 :])
            except ValueError:
                start_time = 0

            if index + 1 < n_songs and next_song["name"][0] == "-":
                if stream_media in ["YouTube", "Live"]:
                    end_time = get_youtube_timing(next_song["URL"])
                else:
                    end_time = get_twitch_timing(next_song["URL"][next_song["URL"].index("t=") + 2 :])
            else:
                end_time = start_time + song.length_DT.seconds + 3

            print(f"{song_name} - [{start_time} : {end_time}]")
            timings.append([start_time, end_time])

            # Check for timing bugs
            if check_timings_bug(timings):
                print(
                    f"Timing bug? Song URL: {song.URL}\nSong length [s]: {song.length_DT.seconds}\nNext song URL: {next_song['URL']}\nNext song name: {next_song['name']}"
                )
                raise Exception("Timing bug found.")

            # Extract the audio segment and change the metadata
            extract_audio_segment(
                f"{stream_dir}/{stream_title}.{file_format}",
                f"{stream_dir}/{song_name}.mp3",
                start_time,
                end_time,
            )
            change_mp3_metadata(
                f"{stream_dir}/{song_name}.mp3",
                df.iloc[index]["name"],
                "Marc Rebillet",
                song.live_title,
                f"{k_song}/{len(df_stream)}",
                get_date_for_mp3(song.htmlID),
                song.genre,
            )
            last_end_time = end_time
            print("  :)")
        print(" ::)\n")
    print("Done.")


def dl_thumbnail(df, stream_titles):
    """
    Downloads thumbnails for specified streams.

    Parameters:
    df (pd.DataFrame): The DataFrame containing stream data.
    stream_titles (list): A list of stream titles to download thumbnails for.

    Writes:
    Thumbnails to the specified directory for each stream.
    """
    for stream_title in stream_titles:
        df_stream = df.query(f'live_title=="{stream_title}"')
        stream_title = format_stream_title(stream_title)
        stream_title = f'{get_stream_info(df_stream, "htmlID")[1:]} {stream_title}'
        stream_dir = f"{dl_dir}/{stream_title}"
        live_url = get_stream_info(df_stream, "URL")

        # Download the thumbnail if it doesn't already exist
        if not os.path.exists(f"{stream_dir}/{stream_title}.jpg"):
            print(f"Doing thumbnail {stream_title} {live_url}")
            if "twitch" in live_url:
                subprocess.run(
                    [
                        "youtube-dl",
                        "--write-thumbnail",
                        "--skip-download",
                        "--output",
                        f"{stream_title}",
                        live_url,
                    ],
                    check=True,
                )
            else:
                # continue
                live_code = get_live_code(live_url)
                print(live_code)
                t = Thumbnail(f"https://www.youtube.com/watch?v={live_code}")
                t.fetch()
                t.save(f".", filename=stream_title)
            subprocess.run(
                f'mv {shlex.quote(f"{stream_title}.jpg")} {shlex.quote(f"{stream_dir}/{stream_title}.jpg")}',
                shell=True,
            )
            print(f"{stream_title} thumbnail DL.")
        else:
            print(f"{stream_title} thumbnail already downloaded.")


def mv_thumbnail_to_icloud(df, stream_titles):
    """
    Moves thumbnails for specified streams to the iCloud directory.

    Parameters:
    df (pd.DataFrame): The DataFrame containing stream data.
    stream_titles (list): A list of stream titles whose thumbnails need to be moved.

    Moves:
    Thumbnails from the local directory to the iCloud directory.
    """
    for stream_title in stream_titles:
        df_stream = df.query(f'live_title=="{stream_title}"')
        stream_title = format_stream_title(stream_title)
        stream_title = f'{get_stream_info(df_stream, "htmlID")[1:]} {stream_title}'
        stream_dir = f"{dl_dir}/{stream_title}"

        # Check if the thumbnail exists and move it to the iCloud directory
        if os.path.exists(f"{stream_dir}/{stream_title}.jpg"):
            os.system(f'cp "{stream_dir}/{stream_title}.jpg" "{icloud_dir}/thumbnails/{stream_title}.jpg"')
            print(f"{stream_title} thumbnail moved.")
        else:
            print(f"{stream_title} thumbnail not found.")


def mv_mp3_to_icloud(df, stream_titles, ranks):
    """
    Moves MP3 files for specified streams to the iCloud directory and updates their metadata.

    Parameters:
    df (pd.DataFrame): The DataFrame containing song data.
    stream_titles (list): A list of stream titles whose MP3 files need to be moved.
    ranks (list): A list of ranks to filter the songs by.

    Moves:
    MP3 files from the local directory to the iCloud directory and updates their metadata.
    """
    for stream_title in stream_titles:
        df_stream = df.query(f'live_title=="{stream_title}"')
        stream_title = format_stream_title(stream_title)
        stream_title = f'{get_stream_info(df_stream, "htmlID")[1:]} {stream_title}'
        stream_dir = f"{dl_dir}/{stream_title}"

        k_song = 0
        # Process each song in the stream
        for index, song in df_stream.iterrows():
            k_song += 1
            song_name = f'{k_song}. {df.iloc[index]["name"]}'.replace("/", "")
            if os.path.exists(f"{stream_dir}/{song_name}.mp3"):
                rank = df.iloc[index]["rank"]
                if rank not in ranks:
                    continue
                os.makedirs(f"{icloud_dir}/{rank}", exist_ok=True)

                new_song_name = get_stream_info(df_stream, "htmlID")[1:] + " " + " ".join(song_name.split(" ")[1:])
                os.system(f'cp "{stream_dir}/{song_name}.mp3" "{icloud_dir}/{rank}/{new_song_name}.mp3"')
                change_mp3_metadata(
                    f"{icloud_dir}/{rank}/{new_song_name}.mp3",
                    df.iloc[index]["name"],
                    f"Marc Rebillet; tier {rank}",
                    song.live_title,
                    f"{k_song}/{len(df_stream)}",
                    get_date_for_mp3(song.htmlID),
                    song.genre,
                    image_path=f"{icloud_dir}/thumbnails/{stream_title}.jpg",
                )
                print(f"Added {icloud_dir}/{rank}/{new_song_name}.mp3.")
