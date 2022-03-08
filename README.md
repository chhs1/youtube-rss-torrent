# YouTube to RSS Torrent creator

[Blog post](https://chhs1.github.io/blog/2022/03/08/youtube-rss-torrent.html)

Wouldn't it be great to publish video content, but not have to pay for all the infrastructure necessary to deliver it to
your subscribers? By combining youtube-dl, RSS feeds, and BitTorrent, we can deliver our video content with the power of
a peer-to-peer network.

## Usage

```text
usage: youtube-to-rss-torrent.py [-h] [--videos-dir VIDEOS_DIR] [--torrents-dir TORRENTS_DIR] [--feed-file FEED_FILE] [--youtubedl-config YOUTUBEDL_CONFIG] url

YouTube to RSS torrent creator

positional arguments:
url                   YouTube channel or playlist URL to download videos from

optional arguments:
-h, --help            show this help message and exit
--videos-dir VIDEOS_DIR, -v VIDEOS_DIR
The directory to store downloaded videos and metadata in
--torrents-dir TORRENTS_DIR, -t TORRENTS_DIR
The directory to store generated torrent files in
--feed-file FEED_FILE, -f FEED_FILE
The filename for the generated RSS feed
--youtubedl-config YOUTUBEDL_CONFIG, -c YOUTUBEDL_CONFIG
The youtube-dl config file to use
```

## Local feed hosting for test purposes

If you wish to quickly test your new `feed.xml` file, you can use Python to host it. Run in your working directory,
and `http://localhost:8000/feed.xml` should point to your RSS feed.

```shell
$ python -m http.server
Serving HTTP on 0.0.0.0 port 8000 (http://0.0.0.0:8000/) ...
```

## youtube-dl configuration

You may specify additional configuration for youtube-dl to use in the `youtubedl-config.conf` file. One suggested
addition is to select `--format worst`, if you wish to download videos quickly as a test. By default, youtube-dl will
use `--format best`.