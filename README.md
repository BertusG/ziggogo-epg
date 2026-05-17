# ZiggoGo EPG

This script grabs EPG data from the ZiggoGo TV service and formats it into XMLTV format. This script is designed for use with
TVHeadend, but can also be used in standalone mode.

ZiggoGo EPG optimizes grabbing on TV information by using a cache database (implemented using SQLite). By reusing this cache
between runs, the amount of data downloading is severely reduced. This has 2 main advantages. First of all, grabbing is a lot
faster (except for the initial run, obviously) as a lot less requests to the Ziggo server need to be made. Secondly, because a
lot less request are being made to the Ziggo server, the impact of running ZiggoGo EPG on these servers will be limited.

Even though ZiggoGo EPG is optimized, it is not recommended to run this program more than twice a day. If more frequent XMLTV
generation is desired (for example, for testing purposes), use the `--generate-only` flag. See the [Usage](#usage) section for
more details.

> **This is a fork of [jbogers/ziggogo-epg](https://github.com/jbogers/ziggogo-epg)** with several bug fixes, performance
> improvements and a full Dutch-to-DVB genre mapping for TVHeadend and Plex. See the [Changes](#changes) section for details.

## Changes

The following changes have been made compared to the original repository:

### Bug fixes

- **Correct Dutch poster URL** (`ziggo-nl.yml`): The `epg_img_detail` URL was pointing to a Polish UPC server
  (`upctv.pl`) instead of the correct Dutch Ziggo server (`ziggogo.tv`).
- **Correct poster URL construction** (`ziggoepggrabber.py`): The poster URL was being built using the internal programme
  `id` instead of the `eventId` (which contains the full `crid+imi` string required by the image service). The code now
  also checks that `eventId` is present before attempting to build the URL.
- **Missing space in SQL INSERT statement** (`ziggoepggrabber.py`): A missing space between two string literals caused
  the SQL query to be malformed (`...endtime)VALUES...`), which would crash on first use.
- **Deprecated `utcfromtimestamp`** (`ziggoepggrabber.py`): Replaced the deprecated
  `datetime.datetime.utcfromtimestamp()` (removed in Python 3.12) with the timezone-aware
  `datetime.datetime.fromtimestamp(..., tz=datetime.timezone.utc)`.
- **`season`/`episode` type inconsistency** (`xmltvwriter.py`): `season` and `episode` were initialised as empty
  strings `""` but set to integers after a successful `int()` conversion. This made the `!= ""` comparison unreliable.
  Both are now initialised as `None` and checked with `is not None`, and the `xmltv_ns` episode string is built
  correctly for cases where only one of the two values is known.
- **Genre category accumulation** (`xmltvwriter.py`): TVHeadend accumulates genre categories on repeated EPG updates
  rather than replacing them. This was especially noticeable for programmes broadcast multiple times per week. Fixed by
  writing at most one `<category lang="en">` tag per programme, selecting the most specific DVB subcategory via a
  priority map (`DVB_PRIORITY`). This prevents unbounded genre accumulation across daily scraper runs.

### Performance improvements

- **Database index** (`ziggoepggrabber.py`): Added `CREATE INDEX IF NOT EXISTS` on the `programmedetails` table to
  speed up the `LEFT JOIN` that is executed on every run.
- **Metadata table for VACUUM scheduling** (`ziggoepggrabber.py`): The `VACUUM` operation (which rebuilds the entire
  database) was previously run after every single grab. It is now only run once every 7 days, tracked via a new
  `metadata` table in the database. On other days, `PRAGMA incremental_vacuum` is used instead. The 7-day interval is
  measured from the last actual VACUUM, so it works correctly regardless of how often or how irregularly the script runs.
- **Timezone-aware `segment_datetime`** (`ziggoepggrabber.py`): The `segment_datetime` used for building EPG segment
  URLs is now explicitly UTC-aware, consistent with the `grab_start` datetime it is derived from.

### Genre mapping

- **Full Dutch-to-DVB genre mapping** (`xmltvwriter.py`): Implemented the category translation that was listed as a
  TODO in the original repository. All Dutch genre names returned by the Ziggo API are now mapped to their official
  DVB/ETSI EN 300 468 English equivalents (e.g. `Paardensport` → `Equestrian`, `Voetbal` → `Football / Soccer`).
  A single `<category lang="en">` tag with the most specific DVB subcategory is written per programme, verified against
  TVHeadend's internal genre list. The mapping covers all 100+ genres returned by the Ziggo API, verified against the
  live cache database.

### API URL updates

- **Updated Ziggo API endpoints** (`ziggo-nl.yml`): The Ziggo API endpoints changed. Updated `epg_channel_list`,
  `epg_segment` and `epg_detail` URLs to the new endpoints (`spark-prod-nl.gnp.cloud.ziggogo.tv` and
  `staticqbr-prod-nl.gnp.cloud.ziggogo.tv`).

## TVHeadend mode

In this mode, TVHeadend will be asked to provide a list of known TV channels. The script will try to match these up to the
ZiggoGo EPG and only grab data for these channels. Once the EPG data has been grabbed, the resulting XMLTV data is directly
written to TVHeadend without creating an intermediate file.

The TVHeadend mode is the recommended mode for ZiggoGo EPG and is thus the default mode.

## Standalone mode

In this mode, the channel list will be read from an input file (recommended) or can be given per channel on the command line.
The XMLTV data will then be output to the file of choice.

For convenience, ZiggoGo EPG can output all known channels to a file. This file can be edited to the users desire and then used
as the input file.

## Requirements

Python 3.6+ is required to run this script. In addition, some external Python packages are used. These are listed in the
`requirements.txt` file. You can easily install these packages using the following command:

    pip install -r requirements.txt

## Usage

For a quick overview of all available options, run:

    ./ziggogoepg.py --help

ZiggoGo EPG supports the following basic options:

- `-h`, `--help`: Opens the program help and exits.
- `-s`, `--configuration`: Select the configuration to use. The default configuration is `ziggo-nl`. Currently supported
configurations are (see also [Adding configurations](#adding-configurations)):
  * `upc-pl`
  * `ziggo-nl`
- `-n`, `--scan-days`: Set the number of days to scan from the ZiggoGo servers. The default of 14 is the current maximum of
the servers. To reduce grabbing time, memory use and storage requirements, this value can be lowered.
- `-f`, `--file-mode`: Runs the grabber in file mode instead of the default TVHeadend mode. See the
[TVHeadend mode](#tvheadend-mode) and [Standalone mode](#standalone-mode) sections for a detailed explanation.

The following options are supported in TVHeadend mode:

- `--tvh-host`: Give the hostname of the TVHeadend server. Defaults to `localhost`.
- `--tvh-port`: Give the port number of the TVHeadend server. Defaults to `9981`.
- `--tvh-username`: The username to use for connecting to TVHeadend.
- `--tvh-password`: The password to use for connecting to TVHeadend. Note that this password can be seen on the command line.
- `--tvh-socket SOCKET`: The path to the xmltv socket of TVHeadend. Defaults to
  `/home/hts/.hts/tvheadend/epggrab/xmltv.sock`.

The following options are supported in standalone file mode:

- `--channel-file`: Sets the filename of the file to read (or write) the channel list from. Defaults to `channels.txt`.
- `-c`, `--channel`: Can be used instead of `--channel-file` to give a specific channel on the command line.
- `--write-channel-list`: Retrieves the currently known channels and writes them to the file specified by `--channel-file`.
  No EPG data will be grabbed. **Warning**: This will overwrite any existing file at that location.

The following options are supported by advanced users:

- `--timezone`: The timezone used for start and stop times in the XMLTV file. Defaults to the timezone in the configuration
  file. See <https://en.wikipedia.org/wiki/List_of_tz_database_time_zones> for valid values.
- `--database-location`: Alternative path (not filename) for the `ziggoepg_cache.sqlite` cache database.
- `--generate-only`: Generates XMLTV output from the existing cache without contacting the ZiggoGo servers. Useful for
  testing.

## Adding configurations

Configuration files are stored with the ZiggoGo EPG program in `.yml` (YAML) files. To create a new configuration it is easiest
to copy an existing one and name it accordingly for your region. In the configuration file, you can adjust the URLs used to
grab the EPG data and set an appropriate timezone for the resulting XMLTV file. Note that this grabber only works with
systems from Ziggo/UPC/Liberty Global.

The following configuration options are available:

- `urls`
  * `epg_channel_list`: The URL where the grabber can get the channel list.
  * `epg_segment`: The URL for program overview segments. Must contain exactly one `{}` placeholder for the segment id.
  * `epg_detail`: The URL for individual program details. Must contain exactly one `{}` placeholder for the program id.
  * `epg_img_detail`: The URL for program poster images. Must contain exactly two `{}` placeholders: the first for the
    `eventId` (the full `crid+imi` string) and the second for the `imageVersion`.
- `timezone`: The timezone used for XMLTV program entries. Must be supported by `pytz`.

## Acknowledgments

Inspiration for the script has been taken from <https://github.com/beralt/horepg>. While all code is new, some operational
ideas (like automatic channel matching with TVHeadend) came from this project.

Thank you [Beralt](https://github.com/beralt) for your hard work on [horepg](https://github.com/beralt/horepg)!

Also thanks to:

- [ldymek](https://github.com/ldymek) for providing the configuration information for `upc-pl`.
