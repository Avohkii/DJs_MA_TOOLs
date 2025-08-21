from enum import Enum
import datetime

try:
  from ..mst_loaders import get_loader
except:
  from mst_loaders import get_loader

from .misc import BinaryIO, ProtocolException


class GamePlatform(Enum):
  xbox = 0
  playstation = 1
  gamecube = 2
  pc = 3


class MST:
  def __init__(self):
    self.platform = None
    self.package_size = 0
    self.file_count = 0
    self.majorVersion = 0
    self.minorVersion = 0
    self.subVersion = 0
    self.platformMask = 0
    self.suffix_unknowns = []
    self.files = []

  def __repr__(self):
    return 'MST({}, {} bytes, {} files)'.format(self.platform, self.package_size, self.file_count)

  def read(self, reader: BinaryIO, disable_formatting):
    header = reader.read_str(4) # FANG
    if header == 'FANG': # Xbox, PS2
      reader.little_endian = True
    elif header == 'GNAF':
      reader.little_endian = False
    else:
      raise ProtocolException()

    version, self.package_size, self.file_count = reader.read_fmt('III')

    self.subVersion = version & 0xFF
    self.minorVersion = (version >> 8) & 0xFF
    self.majorVersion = (version >> 16) & 0xFF
    self.platformMask = (version >> 24) & 0xFF

    if self.platformMask & 0x01:
        self.platform = GamePlatform.xbox
    elif self.platformMask & 0x10:
        self.platform = GamePlatform.gamecube
    elif self.platformMask & 0x20:
        self.platform = GamePlatform.playstation
    elif self.platformMask & 0x04:
        self.platform = GamePlatform.pc

    self.suffix_unknowns = reader.read_fmt('I' * 23)

    self.files = []
    for i in range(self.file_count):
      file = MSTEntry()
      file.read(reader, self.platform, self.majorVersion, self.minorVersion, self.subVersion, disable_formatting)
      self.files.append(file)
    return reader.little_endian



class MSTEntry:
  def __init__(self):
    self.name = None
    self.location = 0
    self.length = 0
    self.create_date = None
    self.unknown = 0
    self.loader = None

  def read(self, reader: BinaryIO, platform: GamePlatform, majorVersion, minorVersion, subVersion, disable_formatting):
    if majorVersion == 1 and minorVersion <= 7:
        name_length = 16
    elif platform == GamePlatform.playstation:
        name_length = 24
    else:
        name_length = 20

    self.name = reader.read_str(name_length).split('\0')[0] # important to re-add this when writing
    self.location, self.length, timestamp, self.unknown = reader.read_fmt('IIII')
    self.create_date = datetime.date.fromtimestamp(timestamp)
    ext = self.name.split('.')[-1].lower()
    self.loader = get_loader(ext, disable_formatting)(self)
