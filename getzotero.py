#!/usr/bin/env python3

import argparse
from configparser import ConfigParser
from pathlib import Path
import subprocess
import sys
from shutil import  copyfileobj, rmtree
import tarfile
from tempfile import mkdtemp
from urllib.request import urlopen
from urllib.error import HTTPError


URLS = {
    'x86_64': 'https://www.zotero.org/download/client/dl?channel=release&platform=linux-x86_64',
    'i686': 'https://www.zotero.org/download/client/dl?channel=release&platform=linux-i686',
}
FILENAME = 'zotero.tar.bz2'
ZOTERO_SUBDIR = 'Zotero_linux-{arch}'
INI_FILE = 'application.ini'
VERSION_SECTION = 'App', 'Version'

DEB_CONTROL = \
'''Package: zotero
Version: {version}
Architecture: {arch}
Maintainer: Vadim Velikodniy <vadim@velikodniy.name>
Section: science
Priority: optional
Homepage: https://zotero.org
Description: Zotero
  Zotero is a free reference manager
'''

DESKTOP_FILE = \
'''[Desktop Entry]
Name=Zotero
Comment="Open-source reference manager"
Exec=/opt/zotero/zotero
Icon='zotero.ico'
Icon=accessories-dictionary
Type=Application
Categories=Office;
StartupNotify=true
Terminal=false
'''

ARCH_TRANSLATE = {
    'x86_64': 'amd64',
    'i686': 'i386',
}

DEB_FILE = 'zotero_{version}_{arch}.deb'


def get_archive(tmp_dir, arch):
    if arch not in URLS:
        archs = ', '.join(str, URLS.keys())
        sys.exit('This architecture is not suppoerted. Use one of: {archs}'.format(archs=archs))
    url = URLS[arch]
    try:
        print('Downloading...', end='', flush=True)
        with urlopen(url) as response:
            with open(str(tmp_dir / FILENAME), 'wb') as zotero_file:
                copyfileobj(response, zotero_file)
        print('done', flush=True)
    except HTTPError:
        print()
        sys.exit('Cannot download: {url}'.format(url=url))


def extract_archive(tmp_dir):
    print('Extracting...', end='', flush=True)
    tar_name = tmp_dir / FILENAME
    with tarfile.open(str(tmp_dir / FILENAME)) as tar:
        tar.extractall(str(tmp_dir))
    tar_name.unlink()
    print('done', flush=True)


def get_version(zotero_dir):
    ini_file = zotero_dir / INI_FILE
    parser = ConfigParser()
    with open(str(ini_file)) as f:
        parser.read_file(f)
    version = parser.get(*VERSION_SECTION)
    print('Version: {version}'.format(version=version))
    return version


def prepare_dir(tmp_dir, zotero_dir):
    print('Preparing dirs...', end='', flush=True)
    opt_dir = tmp_dir / 'opt'
    opt_dir.mkdir()
    zotero_dir.rename(opt_dir / 'zotero')
    print('done', flush=True)


def create_deb_files(tmp_dir, version, arch):
    debian_dir = tmp_dir / 'DEBIAN'
    debian_dir.mkdir()
    with open(str(debian_dir / 'control'), 'w') as f:
        f.write(DEB_CONTROL.format(version=version, arch=arch))
    desktop_dir = tmp_dir / 'usr' / 'share' / 'applications'
    desktop_dir.mkdir(parents=True)
    with open(str(desktop_dir / 'zotero.desktop'), 'w') as f:
        f.write(DESKTOP_FILE)


def build_deb(tmp_dir, version, arch):
    print('Building deb...', flush=True)
    subprocess.run([
        'dpkg-deb',
        '--build',
        str(tmp_dir),
        DEB_FILE.format(arch=arch, version=version)
    ])
    print('Building done', flush=True)


def main(arch):
    tmp_dir = Path(mkdtemp(prefix='getzotero_')).resolve()
    get_archive(tmp_dir, arch)
    extract_archive(tmp_dir)
    zotero_dir = tmp_dir / ZOTERO_SUBDIR.format(arch=arch)
    version = get_version(zotero_dir)
    prepare_dir(tmp_dir, zotero_dir)
    create_deb_files(tmp_dir, version, ARCH_TRANSLATE[arch])
    build_deb(tmp_dir, version, ARCH_TRANSLATE[arch])
    rmtree(str(tmp_dir))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("arch", choices=['x86_64', 'i686'])
    args = parser.parse_args()
    main(args.arch)
