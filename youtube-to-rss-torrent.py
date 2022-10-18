#!/usr/bin/env python3

import os
import re
import subprocess
import json
from hashlib import sha1, sha256
from pathlib import Path
from bencoder import encode, decode
from furl import furl
from bep_0052_torrent_creator import Torrent
from rfeed import *
from datetime import datetime
import xml.dom.minidom
import argparse

default_piece_length = 65536


def download_videos(youtube_url, config_location, videos_dir):
    subprocess.run([
        'youtube-dl',
        '--write-info-json',
        '--embed-subs',
        '--download-archive', 'downloaded.txt',
        '--config-location', Path(config_location).absolute(),
        youtube_url
    ],
        capture_output=False,
        cwd=videos_dir
    )


def create_torrents(videos_dir, torrents_dir):
    return [
        create_torrent(info_file_path=Path(videos_dir) / filename, videos_dir=videos_dir, torrents_dir=torrents_dir)
        for filename in os.listdir(videos_dir)
        if filename.endswith('.info.json')
    ]


def create_torrent(info_file_path, videos_dir, torrents_dir):
    info_file = open(info_file_path, 'r')
    info = json.load(info_file)

    torrent_filename = Path(torrents_dir) / (info['_filename'] + '.torrent')

    if not Path(torrent_filename).exists():
        torrent_file = open(torrent_filename, 'wb')
        torrent = Torrent(path=Path(videos_dir) / info['_filename'], piece_length=default_piece_length)

        # Strip any non-ASCII characters from the torrent name
        torrent.name = re.sub(
            pattern=r'[^\x00-\x7f]',
            repl=r'',
            string=info['_filename']
        )
        torrent_data = torrent.create(tracker='', hybrid=True)
        torrent_file.write(encode(torrent_data))
        torrent_file.close()

        infohash_sha1 = torrent.info_hash_v1()
        infohash_sha256 = torrent.info_hash_v2()

        print('Created torrent file', Path(torrent_filename).absolute())
    else:
        print('Skipping torrent file creation,', Path(torrent_filename).absolute(), "already exists")

        torrent_file = open(torrent_filename, 'rb')
        torrent_data = decode(torrent_file.read())
        infohash_sha1 = sha1(encode(torrent_data[b'info'])).hexdigest()
        infohash_sha256 = sha256(encode(torrent_data[b'info'])).hexdigest()

    torrent_file.close()

    magnet_link = furl('magnet:')
    magnet_link.add([
        ['dn', info['title']],
        ['xt', 'urn:btih:' + infohash_sha1],
        ['xt', 'urn:btmh:1220' + infohash_sha256]
    ])

    return {
        'torrent_filename': torrent_filename,
        'magnet_link': magnet_link.url,
        'title': info['title'],
        'description': info['description'],
        'link': info['webpage_url'],
        'publication_date': datetime.strptime(info['upload_date'], '%Y%m%d'),
        'webpage_url': info['webpage_url'],
        'channel_title': info['channel'],
        'channel_link': info['channel_url']
    }


def create_feed(torrent_info_collection, feed_filename, ):
    title = next(info['channel_title'] for info in torrent_info_collection if info['channel_title'] != '')
    link = next(info['channel_link'] for info in torrent_info_collection if info['channel_title'] != '')

    feed = Feed(
        title=title,
        description='',
        link=link,
        generator='',
        items=sorted(
            [create_feed_item(info) for info in torrent_info_collection],
            key=lambda item: item.pubDate,
            reverse=True
        ),
    )

    rss_xml = feed.rss()
    rss_file = open(feed_filename, mode='w+')
    rss_file.write(xml.dom.minidom.parseString(rss_xml).toprettyxml())
    rss_file.close()

    print('Created RSS feed file', Path(feed_filename).absolute())


def create_feed_item(info):
    return Item(
        title=info['title'],
        link=info['link'],
        description=info['description'],
        guid=Guid(info['link']),
        pubDate=info['publication_date'],
        enclosure=Enclosure(url=info['magnet_link'], length=0, type='application/x-bittorrent'),
    )


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='YouTube to RSS torrent creator')
    parser.add_argument('url', help='YouTube channel or playlist URL to download videos from')
    parser.add_argument('--videos-dir', '-v', default='videos/',
                        help='The directory to store downloaded videos and metadata in')
    parser.add_argument('--torrents-dir', '-t', default='torrents/',
                        help='The directory to store generated torrent files in')
    parser.add_argument('--feed-file', '-f', default='feed.xml', help='The filename for the generated RSS feed')
    parser.add_argument('--youtubedl-config', '-c', default='youtubedl-config.conf',
                        help='The youtube-dl config file to use')
    args = parser.parse_args()

    url = args.url
    videos_dir = args.videos_dir
    torrents_dir = args.torrents_dir
    youtubedl_config = args.youtubedl_config
    feed_file = args.feed_file

    if not os.path.exists(videos_dir):
        os.makedirs(videos_dir)

    if not os.path.exists(torrents_dir):
        os.makedirs(torrents_dir)

    download_videos(youtube_url=url, config_location=youtubedl_config, videos_dir=videos_dir)
    torrent_info_collection = create_torrents(videos_dir=videos_dir, torrents_dir=torrents_dir)
    create_feed(torrent_info_collection=torrent_info_collection, feed_filename=feed_file)
