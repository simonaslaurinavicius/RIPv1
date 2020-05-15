# RIPv1 Routing Protocol simulation in Python

Made as a study project for my Computer Networking class at Vilnius University.  
Goal of the project was to implement chosen Routing Protocol on your own and understand what solutions people came up with, while
trying to deal with quite a dynamic system - computer network.

![RIPv1 Demo](demo/demo.gif)

## Table of contents
* [Requirements](#requirements)
* [Setup](#setup)
* [Run](#run)
* [Usage](#testing)
* [License](#license)
* [References](#references)

## Requirements
Project requires:
* Python version: 3.7 or newer
 
## Setup
To install Python go to [Python Downloads](https://www.python.org/downloads/)  

## Run
Navigate to **src** folder locally and run:
```sh
python3 rip.py
```

## Usage
This section specifies what kind of input is expected from program's API.

#### Add Router / Show Routing Table
<router_name> ::= "R" <digit>
<digit> ::= [0-9]

#### Add/Delete Link
<link> ::= <router_name> "-" <router_name>

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details

## References
* [RFC 2453](https://tools.ietf.org/html/rfc2453)

