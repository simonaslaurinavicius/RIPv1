'''
    File name: rip.py
    Author: Simonas Laurinavicius
    Email: simonas.laurinavicius@mif.stud.vu.lt
    Python Version: 3.7.6
    Purpose: 
        RIPv1 Routing Protocol simulation using mockup network.
        Made as a study project for my Computer Networking class at Vilnius University.
'''

# Standard library
import concurrent.futures

# Local modules
import interface
import router

def main():
    # Create a simple network, represented as a list
    network = interface.create_network()
    
    # Routers running as seperate threads
    with concurrent.futures.ThreadPoolExecutor() as executor:
        routers = [executor.submit(node.start) for node in network]

        interface.print_option_table(network, executor)

        while True:
            option = input("Enter option: ")
            interface.Options[option](network, executor)

if __name__ == "__main__":
    main()