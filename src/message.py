'''
    File name: message.py
    Author: Simonas Laurinavicius
    Email: simonas.laurinavicius@mif.stud.vu.lt
    Python Version: 3.7.6
    Purpose: 
        Message module defines RIP communication formats.
'''

# Standard library
from dataclasses import dataclass, astuple
from typing import List

# RIP Message Format is described in RFC 2453 Section 3.6 [https://tools.ietf.org/html/rfc2453#section-3.6]
Command = {
    "Request": 1,
    "Response": 2
}

@dataclass
class Entry:
    AFI: bytes
    padding_1: bytes
    addr: bytes
    padding_2: bytes
    metric: bytes

    def __bytes__(self):
        return dataclass_to_bytes(self)

@dataclass
class Header:
    command: bytes
    version: bytes
    padding: bytes

    def __bytes__(self):
        return dataclass_to_bytes(self)

@dataclass
class Packet:
    header: Header
    entries: List[Entry]

    def __bytes__(self):
        bytes_ = self.header.__bytes__()
        for entry in self.entries:
            bytes_ += entry.__bytes__()

        return bytes_
        
    def add_entry(self, entry):
        (self.entries).append(entry)

def dataclass_to_bytes(dataclass_):
    bytes_ = b''
    for field in astuple(dataclass_):
        bytes_ += field
    return bytes_