#!/usr/bin/env python
import argparse
import shutil
import socketserver
import subprocess
from datetime import datetime
from http import server
from os import listdir
from os import mkdir
from os import path
from time import sleep

from picamera import PiCamera


def serve() -> None:
    class Handler(server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            location = path.join(path.expanduser('~'), 'timelapse')
            super().__init__(*args, directory=location, **kwargs)

    with socketserver.TCPServer(('', 8080), Handler) as httpd:
        print('listening at http://localhost:8080')
        httpd.serve_forever()


def playback() -> None:
    print('generating time lapse')
    location = path.join(path.expanduser('~'), 'timelapse')
    ffmpeg = shutil.which('ffmpeg')
    if ffmpeg is None:
        raise Exception('ffmpeg is required but not installed on the system')

    now = datetime.now().strftime('%d-%m-%Y-%H')
    video_path = path.join(location, f'timelapse-{now}.mp4')
    subprocess.call(
        [
            ffmpeg,
            '-framerate',
            '30',
            '-pattern_type',
            'glob',
            '-i',
            path.join(location, 'images', '*.jpg'),
            '-c:v',
            'libx264',
            '-r',
            '30',
            video_path,
        ],
    )

    print(f'finished: {video_path}')
    serve()


def capture() -> None:
    dirname = path.join(path.expanduser('~'), 'timelapse')
    mkdir(dirname)
    file_num: int = max(
        [
            int(path.splitext(path.basename(f))[0])
            for f in listdir(dirname)
            if f.endswith('.jpg')
        ],
    ) + 1

    # TODO: write time onto image
    now = datetime.now().strftime('%d-%m-%Y-%H-%M')
    location = path.join(dirname, 'images', now, f'{file_num}' + '.jpg')

    camera = PiCamera()
    camera.start_preview()
    sleep(5)
    camera.capture(location)
    camera.stop_preview()


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--capture', action='store_true', help='capture image and save to disk',
    )
    group.add_argument(
        '--playback', action='store_true', help='playback all images as a timelapse',
    )
    args = parser.parse_args()

    if args.capture:
        capture()
    elif args.playback:
        playback()

    return 0


if __name__ == '__main__':
    exit(main())
