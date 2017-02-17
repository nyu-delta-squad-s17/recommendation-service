import json
import random
import re
import ast
import os

__location__ = os.path.realpath(
        os.path.join(os.getcwd(), os.path.dirname(__file__)))


def openJsonFile():
    jsonFile = open(os.path.join(__location__, "json-generator.json"), "r")
    products = json.load(jsonFile)
    jsonFile.close()
    return products


def getProductList():
    product_list = open(os.path.join(__location__, "dummy_product_names"), "r")
    le_list = [line.strip() for line in product_list]
    product_list.close
    return le_list

if __name__ == "__main__":

    result = {}
    products = openJsonFile()
    le_list = getProductList()

    for product in products:
        tmp_list = list(le_list)
        tmp_list.remove(str(product["product_name"]))

        def callback(matchobj):
            return random.choice(tmp_list)
        product = re.sub(r'mock', callback, str(product))
        product = ast.literal_eval(product)
        product = json.dumps(product)
        product = json.loads(product)
        result[product["product_name"]] = product
    with open(os.path.join(__location__, "../dummy_product_recomm.json"), "w")\
            as jsonFile:
        jsonFile.write(json.dumps(result, indent=4, sort_keys=True))
