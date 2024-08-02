# o3_auto_encode

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![Python 3.10-3.12](https://img.shields.io/badge/python-3.10%20|%203.11%20|%203.12-blue.svg)](https://www.python.org/downloads/release/python-3110/)


Automated tool for recombining split air unit clips into one file and reducing overall video file size.


DJI air unit encodes videos to a FAT32 file system and is limited to files of ~3GB.
If a video file is larger than this limit the video is split up into multiple clips bellow this limit.

o3_auto_encode will concatenate and re-encode these clips to one file.
This will yield a final video file smaller than the sum of all the clips depending on encoding settings.



TODO add quick start, docker setup, etc.
