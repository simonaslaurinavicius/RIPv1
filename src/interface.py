'''
    File name: interface.py
    Author: Simonas Laurinavicius
    Email: simonas.laurinavicius@mif.stud.vu.lt
    Python Version: 3.7.6
    Purpose: 
        Interface module defines various functions used for program API.
'''

# Standard library
import sys

# Local modules
import router

def print_option_table(network, executor):
    print("OPTIONS")
    print("1 - Add Router")
    print("2 - Add Link")
    print("3 - Delete Link")
    print("4 - Show Routing Table")
    print("5 - Show All Tables")
    print("6 - Exit")

def create_network():
    network = []

    startup_file = open("../startup/startup.conf", 'r')
    routers_info = startup_file.readlines()

    for router_info in routers_info:
        router_info = router_info.strip('\n')
        add_router(router_info, network)

    startup_file.close()

    # Adding directly-connected networks as specified in RFC-2453 Page 19 [https://tools.ietf.org/html/rfc2453#page-19]
    links_file = open("../startup/links.conf", 'r')
    links_info = links_file.readlines()

    for link in links_info:
        add_link(link, network)

    links_file.close()

    return network

def parse_link(link, network):
    link = link.replace('R', '')
    names = link.split('-')
    router_1 = network[int(names[0])]
    router_2 = network[int(names[1])]

    return (router_1, router_2)

def add_link(link, network):
    neighbors = parse_link(link, network)

    neighbors[0].add_neighbor(neighbors[1])
    neighbors[1].add_neighbor(neighbors[0])

def delete_link(link, network):
    neighbors = parse_link(link, network)
    
    neighbors[0].delete_neighbor(neighbors[1].name)
    neighbors[1].delete_neighbor(neighbors[0].name)

def add_router(router_name, network):
        router_nr = router_name.replace('R', '')
        ip_addr = "192.0.2." + router_nr
        output_port = 7200 + int(router_nr)
        input_port = 8200 + int(router_nr)
        router_ = router.Router(router_name, ip_addr, output_port, input_port)
        network.append(router_) 

def show_table(router_name, network):
    for node in network:
        if node.name == router_name:
            node.print_routing_table()

def option_add_router(network, executor):
    router_name = input("Enter name of the new router: ")
    add_router(router_name, network)
    executor.submit((network[-1].start))

def option_add_link(network, executor):
    link = input("Enter link info: ")
    add_link(link, network)

def option_delete_link(network, executor):
    link = input("Enter link to delete: ")
    delete_link(link, network)
    for node in network:
        print(node.name)
        for neighbor in node.neighbors:
            print(neighbor)

def option_show_table(network, executor):
    router_name = input("Enter router name: ")
    show_table(router_name, network)

def option_show_all_tables(network, executor):
    for node in network:
        show_table(node.name, network)

def exit_program(network, executor):
    for node in network:
        node.alive = False

    print("Shutting down routers, please wait...")
    executor.shutdown(wait=True)
    sys.exit()

Options = {
    '1': option_add_router,
    '2': option_add_link,
    '3': option_delete_link,
    '4': option_show_table,
    '5': option_show_all_tables,
    '6': exit_program,
    '?': print_option_table
}