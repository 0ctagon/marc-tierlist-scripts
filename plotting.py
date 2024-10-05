import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import calendar
import seaborn as sns
import plothist
import numpy as np
import pandas as pd
import os
from database import css_colors_dict

os.makedirs("plots", exist_ok=True)

rank_list = ["S", "A+", "A", "B+", "B", "C+", "C", "D"]

# Youtube, Twitch, Live colors
custom_colors = [
    (255 / 255, 99 / 255, 71 / 255),
    (128 / 255, 54 / 255, 255 / 255),
    (70 / 255, 130 / 255, 180 / 255),
]


def make_length_plot(df, plot_type="timing"):
    """
    Generates a plot for song lengths or stream lengths.

    Parameters:
    df (pd.DataFrame): The DataFrame containing song data.
    plot_type (str): The type of plot to generate ('timing' or 'stream_length').
    """
    df["length_minutes"] = df["length_DT"].dt.seconds // 60
    df["length_seconds"] = df["length_DT"].dt.seconds % 60

    if plot_type == "timing":
        grouped = df[["length_minutes", "length_seconds", "date_YM_DT"]].groupby("date_YM_DT").mean()
        ylabel = "Mean song length / stream (min)"
        output_file = "plots/live_song_length.png"
    else:
        grouped = (
            df[["date_YM_DT", "length_DT"]].groupby("date_YM_DT").sum()
            / df.drop_duplicates("htmlID")[["date_YM_DT", "length_DT"]].groupby("date_YM_DT").count()
        )
        grouped["length_minutes"] = grouped["length_DT"].dt.seconds // 60
        grouped["length_seconds"] = grouped["length_DT"].dt.seconds % 60
        ylabel = "Mean stream length (min)"
        output_file = "plots/live_stream_length.png"

    grouped = grouped.reset_index()
    grouped["date_YM_DT"] = grouped["date_YM_DT"].dt.strftime("%Y-%m-%d")
    dates = pd.to_datetime(grouped["date_YM_DT"])
    normalized_lengths = (grouped["length_minutes"] - grouped["length_minutes"].min()) / (
        grouped["length_minutes"].max() - grouped["length_minutes"].min()
    )
    colormap = plt.cm.YlOrRd

    fig, ax = plt.subplots(figsize=(7, 5))
    widths = [calendar.monthrange(date.year, date.month)[1] for date in dates]
    plt.bar(
        dates,
        grouped["length_minutes"],
        color=colormap(normalized_lengths),
        width=widths,
    )

    ax.set_xlabel("Date")
    ax.set_ylabel(ylabel)
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    plt.xticks(rotation=45)
    plt.savefig(output_file, bbox_inches="tight")


def make_nsongs_plot(df):
    """
    Generates a bar plot for the number of songs per rank.

    Parameters:
    df (pd.DataFrame): The DataFrame containing song data.

    Writes:
    A bar plot saved as 'plots/rank_nsong.png' showing the number of songs for each rank.
    """
    values = [len(df.query(f"rank == '{rank}'")) for rank in rank_list]
    colors = [
        color
        for rank in rank_list
        for color, rank_key in css_colors_dict.items()
        if rank_key == f"{rank.replace('+','p')}_rank"
    ]
    fig, ax = plt.subplots()
    plt.bar(rank_list, values, color=colors)
    plt.xlabel("Rank")
    plt.ylabel("Number of songs")
    plt.savefig("plots/rank_nsong.png", bbox_inches="tight")


def make_count_plot(df):
    """
    Generates a plot for the number of songs or the number of songs per rank.

    Parameters:
    df (pd.DataFrame): The DataFrame containing song data.
    plot_type (str): The type of plot to generate ('nsongs' or 'rank_nsong').
    """
    grouped = (
        df[["date_YM_DT", "songID"]].groupby("date_YM_DT").count()
        / df.drop_duplicates("htmlID")[["date_YM_DT", "songID"]].groupby("date_YM_DT").count()
    )
    ylabel = "Mean song number / stream"
    output_file = "plots/live_song_number.png"

    grouped = grouped.reset_index()
    grouped["date_YM_DT"] = grouped["date_YM_DT"].dt.strftime("%Y-%m-%d")
    dates = pd.to_datetime(grouped["date_YM_DT"])
    normalized_lengths = (grouped["songID"] - grouped["songID"].min()) / (
        grouped["songID"].max() - grouped["songID"].min()
    )
    colormap = plt.cm.Wistia

    fig, ax = plt.subplots()
    widths = [calendar.monthrange(date.year, date.month)[1] for date in dates]
    ax.bar(dates, grouped["songID"], color=colormap(normalized_lengths), width=widths)

    ax.set_xlabel("Date")
    ax.set_ylabel(ylabel)
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    plt.xticks(rotation=45)
    plt.savefig(output_file, bbox_inches="tight")


def make_livetype_plot(df):
    """
    Generates a stacked bar plot for the number of streams per media type over time.

    Parameters:
    df (pd.DataFrame): The DataFrame containing stream data.

    Writes:
    A stacked bar plot saved as 'plots/nstreams_stacked_bar_plot.png' showing the number of streams per media type.
    """
    # Define media types and colors
    media_types = ["YouTube", "Twitch", "Live"]
    colors = custom_colors

    # Group by "date_YM_DT" and calculate the count of htmlIDs for each media type
    grouped = {
        media: df.query(f"media == '{media}'")
        .drop_duplicates("htmlID")[["date_YM_DT", "htmlID"]]
        .groupby("date_YM_DT")
        .count()
        .reset_index()
        for media in media_types
    }

    # Format dates
    for media in media_types:
        grouped[media]["date_YM_DT"] = grouped[media]["date_YM_DT"].dt.strftime("%Y-%m-%d")

    # Combine the date columns of all groups and take unique values
    dates = pd.concat([grouped[media]["date_YM_DT"] for media in media_types]).unique()
    dates_for_plot = pd.to_datetime(dates)
    widths = [calendar.monthrange(date.year, date.month)[1] - 7 for date in dates_for_plot]

    # Create arrays to store the stream counts for each media type
    songs = {media: [] for media in media_types}

    # Retrieve the corresponding stream counts for each media type
    for date in dates:
        for media in media_types:
            if date in grouped[media]["date_YM_DT"].values:
                songs[media].append(grouped[media][grouped[media]["date_YM_DT"] == date]["htmlID"].iloc[0])
            else:
                songs[media].append(0)

    # Convert the arrays to numpy arrays
    songs = {media: np.array(songs[media]) for media in media_types}

    # Plot the data as a stacked bar plot
    fig, ax = plt.subplots()

    bottom = np.zeros(len(dates_for_plot))
    for i, media in enumerate(media_types):
        bar = ax.bar(
            dates_for_plot,
            songs[media],
            bottom=bottom,
            color=colors[i],
            width=widths,
            edgecolor="black",
            linewidth=0.4,
        )
        bottom += songs[media]
        ymax = max(bottom)

    ax.set_xlabel("Date")
    ax.set_ylabel("Number of streams")
    ax.set_ylim(0, ymax + 1)

    # Format x-axis ticks as dates
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    plt.xticks(rotation=45)

    # Create custom legend handles
    legend_handles = [plt.Rectangle((0, 0), 1, 1, color=color) for color in colors]
    legend_labels = media_types

    plt.legend(legend_handles, legend_labels, loc="upper right")

    # Save the plot
    plt.savefig("plots/nstreams_stacked_bar_plot.png", bbox_inches="tight")


def make_rank_plots(df, rank="high"):
    """
    Generates a heatmap plot for the percentage of songs with specified ranks over time.

    Parameters:
    df (pd.DataFrame): The DataFrame containing song data.
    rank (str): The rank category to plot ('high', 'mid', 'low').

    Writes:
    A heatmap plot saved as 'plots/rank_heatmap_{rank}.png' showing the percentage of songs with specified ranks.
    """
    rank_queries = {
        "high": "rank == 'S' or rank == 'A+' or rank == 'A'",
        "mid": "rank == 'B+' or rank == 'B'",
        "low": "rank == 'C+' or rank == 'C' or rank == 'D'",
    }
    cmap = {"high": "YlOrRd", "mid": "YlGn", "low": "Blues"}
    rank_txt = {"high": "S, A+ or A", "mid": "B+ or B", "low": "C+, C or D"}

    if rank not in rank_queries:
        raise ValueError(f"Invalid rank: {rank}")

    query = rank_queries.get(rank, "rank == 'S' or rank == 'A+' or rank == 'A'")
    percentage_df = (
        df[["date_YM_DT", "when_ranked_YM_DT", "rank"]]
        .query(query)
        .groupby(["date_YM_DT", "when_ranked_YM_DT"])
        .count()
        / df[["date_YM_DT", "when_ranked_YM_DT", "rank"]].groupby(["date_YM_DT", "when_ranked_YM_DT"]).count()
    )

    df = df[["date_YM_DT", "when_ranked_YM_DT"]]

    # Merge the percentage data with the df DataFrame
    df = pd.merge(df, percentage_df, on=["date_YM_DT", "when_ranked_YM_DT"], how="left")

    # Multiply rank column by 100 to get percentage values
    df["rank"] = df["rank"] * 100

    # Convert 'date_YM_DT' to month-year format
    df["date_YM_DT"] = df["date_YM_DT"].dt.strftime("%Y-%m")
    df["when_ranked_YM_DT"] = df["when_ranked_YM_DT"].dt.strftime("%Y-%m")

    # Pivot the filtered DataFrame to create a 2D grid for the heatmap
    pivot_df = df.pivot_table(index="when_ranked_YM_DT", columns="date_YM_DT", values="rank")

    # Set up the plot
    fig, ax = plt.subplots(figsize=(23, 9))

    # Create the heatmap using seaborn
    sns.heatmap(pivot_df, annot=True, fmt=".0f", linewidths=0, cmap=cmap[rank], ax=ax)

    ax.invert_yaxis()
    # Add grid lines below the data
    ax.set_axisbelow(True)

    # Customize the grid lines
    ax.grid(True, linestyle="--", linewidth=0.5, color="gray", axis="both", zorder=0)

    # Add a colorbar
    cbar = ax.collections[0].colorbar
    cbar.set_label(f"Percentage of songs with rank {rank_txt[rank]} in the stream")

    cbar.ax.set_ylabel(cbar.ax.get_ylabel(), rotation=-90)
    cbar.ax.yaxis.set_label_coords(2.6, 0.5)

    # Set the axis labels
    ax.set_xlabel("Date of the stream")
    ax.set_ylabel("Date when I ranked the stream")
    plt.xticks(rotation=80)

    ax.set_xticklabels(ax.get_xticklabels())
    ax.set_yticklabels(ax.get_yticklabels())

    # Show the plot
    fig.savefig(f"plots/rank_heatmap_{rank}.png", bbox_inches="tight")


def make_streamtype_plot(df, plot_type="rank"):
    """
    Generates a plot for the number of songs per rank or tempo for each stream type.

    Parameters:
    df (pd.DataFrame): The DataFrame containing song data.
    plot_type (str): The type of plot to generate ('rank' or 'tempo').
    """
    if plot_type == "rank":
        categories = rank_list
        ylabel = "Percentage"
        output_file = "plots/rank_nsong_streamtype.png"
        category_ticks = categories
    else:
        categories = [["Slow", "Smed"], ["Med"], ["Fmed", "Fast"]]
        ylabel = "Percentage"
        output_file = "plots/tempo_nsong_streamtype.png"
        category_ticks = ["Slow or Smed", "Med", "Fmed or Fast"]

    values = []
    for category in categories:
        category_values = []
        for media in ["YouTube", "Twitch", "Live"]:
            if plot_type == "rank":
                category_values.append(
                    len(df.query(f"rank == '{category}' and media == '{media}'"))
                    * 100
                    / len(df.query(f"media == '{media}'"))
                )
            else:
                category_values.append(
                    len(df.query(f"tempo in {category} and media == '{media}'"))
                    * 100
                    / len(df.query(f"media == '{media}'"))
                )
        values.append(category_values)

    colors = [custom_colors for _ in range(len(categories))]
    fig, ax = plt.subplots()
    num_bars = len(values[0])
    bar_width = 0.7
    x = np.arange(len(categories))

    ymax = 0
    for i, category in enumerate(categories):
        offset = -bar_width / 3
        for j in range(num_bars):
            bar = plt.bar(
                x[i] + offset + j * bar_width / num_bars,
                values[i][j],
                width=bar_width / num_bars,
                color=colors[i][j],
            )
            max_height = max([rect.get_height() for rect in bar])
            if max_height > ymax:
                ymax = max_height

    plt.ylabel(ylabel)
    plt.xlabel("Rank" if plot_type == "rank" else "Tempo")
    if plot_type != "rank":
        plt.ylim(0, ymax + ymax * 0.15)
    legend_handles = [plt.Rectangle((0, 0), 1, 1, color=color) for color in colors[0]]
    plt.legend(legend_handles, ["YouTube", "Twitch", "Live"], loc="upper right")
    plt.xticks(x, category_ticks)
    plt.savefig(output_file, bbox_inches="tight")


def make_rank_length_streamtype(df):
    """
    Generates a bar plot showing the mean song length for each rank and media type.

    Parameters:
    df (pd.DataFrame): The DataFrame containing song data.

    Writes:
    A bar plot saved as 'plots/rank_length_streamtype.png' showing the mean song length for each rank and media type.
    """
    values = []

    # Calculate mean song length for each rank and media type
    for rank in rank_list:
        rank_values = []
        for media in ["YouTube", "Twitch", "Live"]:
            rank_values.append(df.query(f"rank == '{rank}' and media =='{media}' ")["length_DT"].mean())
        values.append(rank_values)

    # Assign colors for each category
    colors = []
    for i in range(len(rank_list)):
        colors.append(custom_colors)

    fig, ax = plt.subplots()
    num_bars = len(values[0])
    bar_width = 0.7
    x = np.arange(len(rank_list))

    # Plot the data as a bar plot
    for i, category in enumerate(rank_list):
        offset = -bar_width / 3
        for j in range(num_bars):
            numerical_value = values[i][j].total_seconds() / 60
            plt.bar(
                x[i] + offset + j * bar_width / num_bars,
                numerical_value,
                width=bar_width / num_bars,
                color=colors[i][j],
            )

    plt.xlabel("Rank")
    plt.ylabel("Mean song length (minute)")

    # Create custom legend handles
    legend_handles = [plt.Rectangle((0, 0), 1, 1, color=color) for color in colors[0]]

    plt.legend(legend_handles, ["YouTube", "Twitch", "Live"], loc="upper right")
    plt.xticks(x, rank_list)
    plt.savefig("plots/rank_length_streamtype.png", bbox_inches="tight")


def make_tempo_nsong(df):
    """
    Generates a bar plot showing the number of songs for each tempo category.

    Parameters:
    df (pd.DataFrame): The DataFrame containing song data.

    Writes:
    A bar plot saved as 'plots/tempo_nsong.png' showing the number of songs for each tempo category.
    """
    # Define the categories and their corresponding values
    tempos = ["Slow or Smed", "Med", "Fmed or Fast"]
    values = []
    fig, ax = plt.subplots()

    # Calculate the number of songs for each tempo category
    values.append(len(df.query(f"tempo == 'Slow' or tempo == 'Smed'")))
    values.append(len(df.query(f"tempo == 'Med'")))
    values.append(len(df.query(f"tempo == 'Fmed' or tempo == 'Fast'")))

    # Plot the bar graph with custom colors
    plt.bar(tempos, values)

    # Set labels and title
    plt.xlabel("Tempo")
    plt.ylabel("Number of songs")
    # plt.title('Bar Graph')

    # Rotate the x-axis labels if needed
    # plt.xticks(rotation=45)

    plt.savefig("plots/tempo_nsong.png", bbox_inches="tight")
