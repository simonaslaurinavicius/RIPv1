'''
    File name: table.py
    Author: Simonas Laurinavicius
    Email: simonas.laurinavicius@mif.stud.vu.lt
    Python Version: 3.7.6
    Purpose: 
        Table module models a Routing Table and an Entry of a Table.
'''

# Standard library
from dataclasses import dataclass
from typing import List

import threading
import time

@dataclass
class TableEntry:
    addr: str
    metric: int
    next_hop: str
    route_change: bool
    timer: threading.Timer # Internal timer for Garbage Collection
    time_renewed: float # Timestamp for parsing ttl field when printing the routing table
    TIMEOUT: float = 180.0
    GARBAGE_COLLECT: float = 120.0

    def start_timer(self, table, router):
        self.timer = threading.Timer(self.TIMEOUT, self.garbage_process, [table, router])
        (self.timer).start()
    
    def restart_timer(self, table, router):
        (self.timer).cancel()
        self.start_timer(table, router)
        self.time_renewed = time.perf_counter()

    def garbage_process(self, table, router):
        # Initialize Garbage Collection Timer
        self.timer = threading.Timer(self.GARBAGE_COLLECT, self.deletion_process, [table])
        (self.timer).start()

        # Set route metric to infinity 
        (self.metric) = table.INFINITY_METRIC

        # Send Triggered Update
        (self.route_change) = True
        router.output_response(triggered_update=True)

    def deletion_process(self, table):
        table.delete_entry(self)

    def update_entry(self, next_hop, new_metric, table, router):

        # Check if it's from the same router, if yes always update metric to new metric
        if self.next_hop == next_hop:
            self.metric = new_metric
            self.route_change = True
            self.restart_timer(table, router)

        # If not from the same router, check whether the metric is better than current one, if yes update it, if no keep the old entry
        elif self.next_hop != next_hop and self.metric > new_metric:
            self.next_hop = next_hop
            self.metric = new_metric
            self.route_change = True
            self.restart_timer(table, router)
    
    def parse_ttl(self):
        ttl = max(self.TIMEOUT - (time.perf_counter() - self.time_renewed), 0)
        return int(ttl)


@dataclass
class RoutingTable:
    entries: List[TableEntry]
    INFINITY_METRIC: int = 16

    def print(self):
        for entry in self.entries:
            if entry.next_hop is None:
                route_learned = 'C '
                next_hop = "directly connected"
            else:
                route_learned = 'R '
                next_hop = entry.next_hop
            ttl = entry.parse_ttl()
            if ttl == 0:
                ttl = "Garbage collection started"

            print(route_learned, entry.addr, " [", entry.metric, "] via ", next_hop, " ttl: ", ttl)
        
    def add_entry(self, dest_addr, metric, next_hop, router):
        entry = TableEntry(dest_addr, metric, next_hop, True, None, time.perf_counter())
        entry.start_timer(self, router)
        (self.entries).append(entry)

    def delete_entry(self, entry):
        (self.entries).remove(entry)

    def check_entry(self, dest_addr, new_metric, next_hop, router):
        new_entry = True

        for entry in self.entries: 

            # If entry exists
            if entry.addr == dest_addr:
                entry.update_entry(next_hop, new_metric, self, router)
                new_entry = False

        if new_entry:
            self.add_entry(dest_addr, new_metric, next_hop, router)

    def get_entry(self, addr):
        for entry in self.entries:
            if entry.addr == addr:
                return entry

    def cancel_timers(self):
        for entry in self.entries:
            (entry.timer).cancel()
    
    def unset_flags(self):
        for entry in self.entries:
            entry.route_change = False
