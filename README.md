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

## API Resources
  - [GET /recommendations](#get-recommendations)
  - [GET /recommendations/[id]](#get-recommendations-id)
  - [POST /recommendations](#post-recommendations)
  - [PUT /recommendations/[id]](#put-recommendations-id)
  - [DELETE /recommendations/[id]](#delete-recommendations-id)
  - [PUT /recommendations/[id]/clicked](#put-recommendations-d)

### GET /recommendations
Example: http://0.0.0.0:5000/recommendations
Response body:
[
{
id: 1,
parent_product_id: 3,
priority: 66,
related_product_id: 2,
type: "x-sell"
},
{
id: 2,
parent_product_id: 1,
priority: 1,
related_product_id: 3,
type: "up-sell"
},
{
id: 3,
parent_product_id: 2,
priority: 4,
related_product_id: 4,
type: "up-sell"
}
]

Example: http://0.0.0.0:5000/recommendations?product-id=3
{
"id": 1,
"parent_product_id": 3,
"priority": 66,
"related_product_id": 2,
"type": "x-sell"
}

### GET /recommendations/[id]
Example: http://0.0.0.0:5000/recommendations/1
Response body:
{
id: 1,
parent_product_id: 3,
priority: 66,
related_product_id: 2,
type: "x-sell"
}

### POST /recommendations
Example: http://0.0.0.0:5000/recommendations
Response body:

### PUT /recommendations/[id]
Example: http://0.0.0.0:5000/recommendations/1
Response body:

### DELETE /recommendations/[id]
Example: http://0.0.0.0:5000/recommendations/1
Response body:

### PUT /recommendations/[id]/clicked
Example: http://0.0.0.0:5000/recommendations/1/clicked
Response body:
