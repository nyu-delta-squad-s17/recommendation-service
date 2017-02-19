import json
import random
import os
import uuid

__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))


def openJsonFile():
    jsonFile = open(os.path.join(__location__, "json-generator.json"), "r")
    products = json.load(jsonFile)
    jsonFile.close()
    return products


def getProductList():
    product_list_file = open(
        os.path.join(__location__, "dummy_product_names"), "r")
    prod_list = [line.strip() for line in product_list_file]
    product_list_file.close()
    return prod_list


def productIDMapper(prod_list):
    result_dict = {}
    prod_count = 0
    for product in prod_list:
        result_dict[product] = str(uuid.uuid4())[:8]
        prod_count += 1
    return result_dict, prod_count

if __name__ == "__main__":

    result = {}
    products = openJsonFile()
    prod_dict, prod_count = productIDMapper(getProductList())


    for product in products:
        product["id"] = prod_dict[product["name"]]
        tmp_prod_dict = dict(prod_dict)

        def getRandomProd():
            return random.choice(tmp_prod_dict.keys())
        for recs in product["recommendations"]:
            new_rec = getRandomProd()
            recs["name"] = new_rec
            tmp_prod_dict.pop(new_rec, None)
            recs["id"] = prod_dict[new_rec]
        result[product["id"]] = product

    with open(os.path.join(__location__, "../dummy_product_recomm.json"), "w")\
            as jsonFile:
        jsonFile.write(json.dumps(result, indent=4, sort_keys=True))
