import csv
import os.path
from os import path
from geopy.geocoders import Nominatim

from neo4j import GraphDatabase
#import pandas as pd
from pip._vendor.distlib.compat import raw_input


class graph:

    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "Fivos99!"))

    def close(self):
        self.driver.close()
    def clear(self):
        with self.driver.session() as session:
            session.write_transaction(self.cl)
    @staticmethod
    def cl(tx):
        tx.run("MATCH(n) DETACH DELETE n")

    def add_shop(self, name, loc_latitude, loc_longitude, address,available_prod):
        with self.driver.session() as session:
            new_shop = session.write_transaction(self.shop, name, loc_latitude, loc_longitude, address,available_prod)

    @staticmethod
    def shop(tx, name, loc_latitude, loc_longitude, address,available_prod):
        result_add_shop = tx.run("CREATE (node:shop) "
                                 "SET node.name = $name , node.latitude = $latitude , node.longitude = $longitude , node.address = $address "
                                 "RETURN node.name + ',' + 'node.address' + ', from node ' + id(node)", name=name,address = address,
                                 latitude=loc_latitude, longitude=loc_longitude)

        for product in available_prod:
            if len(product) > 0:
                product[0] = product[0].strip()
                print("name of product ",product[0] )
                #tha tsekaroume an to proion uparxei gia na mhn iparxei to idio proion 2 fores
                all = tx.run(
                    "MATCH (n:product{name : $name_prod}) " 
                    "RETURN n.name ", name_prod=product[0])
                name_prod = []
                for record in all:
                    name_prod.append(record.values()[0])
                print("name", name_prod)
                if len(name_prod) == 0:
                    result_add_product = tx.run("CREATE (node_prod:product) "
                                                "SET node_prod.name = $name "
                                                "RETURN node_prod.name",
                                                name=product[0],
                                                )

                # add the relationship between product and shop
                result_add_relationship = tx.run("MATCH (a:shop{name:$name}), (b:product{name:$name_prod})  "
                                                 "CREATE (a)-[r:has{price : $price}]->(b) "
                                                 "RETURN a.name", name=name, name_prod=product[0], price = product[1])
                print(result_add_relationship.values(),"+++++++")

        return result_add_shop.single()[0]


if __name__ == "__main__":

    available_shops = csv.reader(open('shops.csv', encoding='utf-8'),
                                 delimiter=',')                      # exoume ena csv pou periexei ola ta onomata katastimatwn kathws kai diefthinsis
    product_list = [];                                                          # gia kathe ipokatastima exoume ta proionta se ena scv
    dbms = graph("bolt://localhost:7687", "neo4j", "Fivos99!")
    dbms.clear();

    for row in available_shops:
        # add shops in database
        name_of_csv = row[0]
        if path.exists("shops\\" +name_of_csv + ".csv"):
            available_products = csv.reader(open("shops\\" + name_of_csv + ".csv", encoding='utf-8'), delimiter=',')
        print(row[0])
        # vriskw  Latitude and Longitude tou katasthmatos
        geolocator = Nominatim(user_agent="main.py",timeout = 50)
        location = geolocator.geocode(row[1])

        latitude = location.latitude
        longitude = location.longitude
        print(row[1], latitude, longitude)

        dbms.add_shop(row[0], latitude, longitude, row[1],available_products)                              #prosthetoume to katasthma ston grafo mas

    dbms.close()

