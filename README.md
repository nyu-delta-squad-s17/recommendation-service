# recommendation-service
A relationship between two products (prod a, prod b)

This repo demonstrates how to create a simple RESTful service using Python Flask.
The resource model has uses a MySQL database hosted in a docker container. 

## Prerequisite Installation using Vagrant

The easiest way to use this code is with Vagrant and VirtualBox. if you don't have this software the first step is down download and install it.

Download [VirtualBox](https://www.virtualbox.org/)

Download [Vagrant](https://www.vagrantup.com/)

Clone the project to your development folder and create your Vagrant vm

    $ git clone https://github.com/nyu-delta-squad-s17/recommendation-service.git
    $ cd nyu-recommendations-s17
    $ vagrant up

Once the VM is up you can use it with:

    $ vagrant ssh
    $ cd /vagrant
    $ python server.py

When you are done, you can use `Ctrl+C` to stop the server and then exit and shut down the vm with:

    $ exit
    $ vagrant halt

If the VM is no longer needed you can remove it with:

    $ vagrant destroy