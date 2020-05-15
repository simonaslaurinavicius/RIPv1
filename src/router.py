'''
    File name: router.py
    Author: Simonas Laurinavicius
    Email: simonas.laurinavicius@mif.stud.vu.lt
    Python Version: 3.7.6
    Purpose: 
        Router module models a Router running on a network.
'''

# Standard library
from dataclasses import dataclass

import socket
import time
import threading
import random

# Local modules
import table
import message

@dataclass
class Neighbor:
    name: str
    ip_addr: str
    output_port: int
    input_port: int

class Router:

    UPDATE_TIMER = 5.0 #  Every 30 seconds, the RIP process is awakened to send an unsolicited Response message containing the complete routing table.
    MAX_OFFSET = 8.0 # Maximum value for timer offset
    GARBARE_TIMER = 120 # Garbage Collection Timer is 120 seconds
    INFINITY_METRIC = 16 # Max hop count + 1
    DEFAULT_COST = 1 # Cost from router to neighbor
    NEXT_ENTRY = 20 # Index increment for next entry in a request
    AFI_IDX = slice(0, 2) # Index for AFI field
    IP_IDX = slice(4, 8) # Index for IP field
    METRIC_IDX = slice(16, 20) # Index for metric field

    # 2-byte and 4-byte sized padding for generating RIP packets and entries
    PADDING_2 = b"\x00\x00"
    PADDING_4 = b"\x00\x00\x00\x00" 
  
    AFI_INET = b"\x00\x02"  # For RIP-1 only AF_INET(2) is generally supported     

    def __init__(self, name, ip_addr, output_port, input_port):
        self.table = table.RoutingTable([])
        self.name = name
        self.ip_addr = ip_addr
        self.output_port = output_port
        self.input_port = input_port
        self.neighbors = []

        self.update_timer = None    # We initialize update_timer after we start the router and send routing request for the first time
        self.alive = True
        self.output_socket = None
        self.input_socket = None

    def __eq__(self, other):
        return self.ip_addr == other.ip_addr

    def add_neighbor(self, router):
        neighbor = Neighbor(router.name, router.ip_addr, router.output_port, router.input_port)
        (self.neighbors).append(neighbor)
        (self.table).check_entry(router.ip_addr, self.DEFAULT_COST, None, router=self)  # Metric of a neighbor is 1, next-hop is ommited

    # We use name to delete router from neighbors
    def delete_neighbor(self, router_name):
        for neighbor in self.neighbors:
            if neighbor.name == router_name:
                (self.neighbors).remove(neighbor)

    def print_routing_table(self):
        print(self.name, " ROUTING TABLE")
        (self.table).print()

    def start_update_timer(self):
        random_offset = random.randrange(0, self.MAX_OFFSET, 1)

        # False stands for triggered update argument in send_response method
        self.update_timer = threading.Timer((self.UPDATE_TIMER + random_offset), self.output_response, [False])
        self.update_timer.start()

    def create_socket(self, port):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        except:
            print("Router", self.name, " create_socket() socket(): ", e)

        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            if port == self.input_port:
                sock.settimeout(self.UPDATE_TIMER + 5)
            else:
                sock.settimeout(self.MAX_OFFSET)
        except OSError as e:
            print("Router", self.name, " create_socket() setsockopt(): ", e)

        try:
            sock.bind(("localhost", port))
        except OSError as e:
            print("Router", self.name, " create_socket() bind(): ", e)

        return sock

    def start(self):
        print("Router ", self.name, " started...")

        # Create communication sockets
        self.output_socket = self.create_socket(self.output_port)
        self.input_socket = self.create_socket(self.input_port)

        # Wait till you're connected to the network
        while not self.neighbors and self.alive:
            time.sleep(0.1)

        # Send request for the whole table once you're connected to the network
        self.output_request()

        self.start_update_timer()

        # Listen for other routers
        while self.alive:
            self.listen()

        self.disable()
        print("Router ", self.name, " stopped working...")

    def disable(self):
        (self.table).cancel_timers()
        (self.update_timer).cancel()
        self.neighbors = []
        (self.output_socket).close()
        (self.input_socket).close()
        

    def listen(self):
        (data, addr) = (self.input_socket).recvfrom(512)
        
        # We use neighbor port to imitate neighbor address
        neighbor_output_port = addr[1]

        # Renew directly connected routers manually
        self.renew_directly_connected(neighbor_output_port)

        command_received = data[0]

        if command_received == message.Command["Request"]:
            self.process_request(data[4:])
        elif command_received == message.Command["Response"]:
            self.process_response(data[4:], neighbor_output_port)

    def renew_directly_connected(self, port):
        addr = self.port_to_addr(port)
        entry = (self.table).get_entry(addr)
        entry.restart_timer(self.table, self)

    def split_entries(self, entries):
        for i in range(0, len(entries), self.NEXT_ENTRY):
            yield entries[i:i + self.NEXT_ENTRY]

# INPUT PROCESSING
# More on that can be found in RFC 2453 Section 3.9 [https://tools.ietf.org/html/rfc2453#section-3.9]
    def check_entire_request(self, entries):
        
        # Numeric values
        AFI_value = int.from_bytes(entries[self.AFI_IDX], byteorder="big")
        metric_value = int.from_bytes(entries[self.METRIC_IDX], byteorder="big")

        if len(entries) == 20:
            if AFI_value == 0 and metric_value == self.INFINITY_METRIC:
                return True
        else:
            return False


    # Currently we stick to the situation where routers will send the requests only when trying to fill in their routing tables,
    #   check for entire table is added while thinking about extending the project, where requests might come from particular router
    def process_request(self, entries):
        # Check if you need to send an entire routing table
        send_entire_table = self.check_entire_request(entries)

        if send_entire_table:
            self.output_response(triggered_update=False)

    def process_response(self, entries, neighbor_output_port):
        for entry in self.split_entries(entries):
            destination_ip = socket.inet_ntoa(entry[self.IP_IDX])   # Turn Destination IP to human-readable IP format

            # If neighbor sends me route to myself, ignore it
            if destination_ip == self.ip_addr:
                continue

            metric = int.from_bytes(entry[self.METRIC_IDX], byteorder="big")

            # If metric larger or equals infinity, it means network is unreachable, ignore it
            if metric >= self.INFINITY_METRIC:
                continue
 
            updated_metric = min(metric + self.DEFAULT_COST, self.INFINITY_METRIC)

            neighbor_addr = self.port_to_addr(neighbor_output_port) # Turn neighbor port to mock IP address we use in Routing Table

            (self.table).check_entry(destination_ip, updated_metric, neighbor_addr, self)

    # Turn port number to mock IP address
    def port_to_addr(self, port):
        router_nr = port - 7200
        network = "192.0.2."
        host = str(router_nr)
        addr = network + host
        return addr

# OUTPUT PROCESSING
# More on that can be found in RFC 2453 Section 3.10 [https://tools.ietf.org/html/rfc2453#section-3.10]

    def generate_header(self, command):
        command_ = command
        version = b"\x01"

        header = message.Header(command_, version, self.PADDING_2)

        return header

    def output_request(self):
        header = self.generate_header(command=b"\x01") # 1 - stands for Request Command

        # If there is exactly entry in the request, and it has an AFI of 0, and a metric of infinity (i.e., 16) - this is a request to send the entire routing table.
        AFI = b"\x00\x00" 
        metric = (self.INFINITY_METRIC).to_bytes(4, byteorder="big")

        ip_addr = socket.inet_aton(self.ip_addr)

        entry = message.Entry(AFI, self.PADDING_2, ip_addr, self.PADDING_4 * 2, metric)
        request_packet = message.Packet(header, [entry]).__bytes__()
        for neighbor in self.neighbors:
            self.send_packet(request_packet, neighbor.input_port)

    # More on Split Horizon and Poison Reverse can be found in RFC 2453 Section 3.4.3 [https://tools.ietf.org/html/rfc2453#section-3.4.3]
    def split_horizon(self, neighbor_addr, entry):
        if entry.next_hop == neighbor_addr:
            # Poison Reverse
            metric = (self.INFINITY_METRIC).to_bytes(4, byteorder="big")
        else:
            metric = (entry.metric).to_bytes(4, byteorder="big")

        return metric

    def fill_entry(self, entry, neighbor_addr):
        metric = self.split_horizon(neighbor_addr, entry)
        ip_addr = socket.inet_aton(entry.addr)
        entry = message.Entry(self.AFI_INET, self.PADDING_2, ip_addr, self.PADDING_4 * 2, metric)
        return entry

    # We stick to Triggered Updates only for deleted routes
    # More on Triggered Updates can be found in RFC 2453 Section 3.4.4 [https://tools.ietf.org/html/rfc2453#section-3.4.4]
    def output_response(self, triggered_update):
        header = self.generate_header(command=b"\x02")

        for neighbor in self.neighbors:
            neighbor_addr = self.port_to_addr(neighbor.output_port)
            entries = []

            for table_entry in (self.table).entries:
                if triggered_update and table_entry.route_change == False: 
                    continue
                entry = self.fill_entry(table_entry, neighbor_addr)
                entries.append(entry)

            response_packet = message.Packet(header, entries).__bytes__()
            self.send_packet(response_packet, neighbor.input_port)

        if not triggered_update:
            self.start_update_timer()
        # If Triggered Update was sent, set Route Change Flags to False
        else:
            (self.table).unset_flags()

    def send_packet(self, packet, neighbor_port):
        try:
            (self.output_socket).sendto(packet, ("localhost", neighbor_port))
        except OSError as e:
            print("Router ", self.name, " send_packet() sendto: ", e)


    
