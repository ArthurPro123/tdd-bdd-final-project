# Copyright 2016, 2023 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Test cases for Product Model

Test cases can be run with:
    nosetests
    coverage report -m

While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_models.py:TestProductModel

"""
import os
import logging
import unittest
from decimal import Decimal
from service.models import Product, Category, db, DataValidationError
from service import app
from tests.factories import ProductFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)


######################################################################
#  P R O D U C T   M O D E L   T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestProductModel(unittest.TestCase):
    """Test Cases for Product Model"""

    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        Product.init_db(app)

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.close()

    def setUp(self):
        """This runs before each test"""
        db.session.query(Product).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_create_a_product(self):

        """It should Create a product and assert that it exists"""

        app.logger.info("Creating a product in memory")

        product = Product(name="Fedora", description="A red hat", price=12.50, available=True, category=Category.SOFTWARE)
        self.assertEqual(str(product), "<Product Fedora id=[None]>")
        self.assertTrue(product is not None)
        self.assertEqual(product.id, None)
        self.assertEqual(product.name, "Fedora")
        self.assertEqual(product.description, "A red hat")
        self.assertEqual(product.available, True)
        self.assertEqual(product.price, 12.50)
        self.assertEqual(product.category, Category.SOFTWARE)



    def test_add_a_product(self):
        """It should Create a product and add it to the database"""

        products = Product.all()
        self.assertEqual(products, [])

        product = ProductFactory()
        product.id = None

        app.logger.info("Adding a {product} product to the database")

        product.create()

        # Assert that it was assigned an id and shows up in the database
        self.assertIsNotNone(product.id)
        products = Product.all()
        self.assertEqual(len(products), 1)

        # Check that it matches the original product
        new_product = products[0]
        self.assertEqual(new_product.name, product.name)
        self.assertEqual(new_product.description, product.description)
        self.assertEqual(Decimal(new_product.price), product.price)
        self.assertEqual(new_product.available, product.available)
        self.assertEqual(new_product.category, product.category)

    #
    # ADD YOUR TEST CASES HERE
    #
    def test_read_a_product(self):

        """It should Read a product"""

        product = ProductFactory()

        app.logger.info(f"a new {product} product created to test subsequent reading from the database")

        product.id = None
        product.create()
        self.assertIsNotNone(product.id)
        # Fetch it back
        found_product = Product.find(product.id)
        self.assertEqual(found_product.id, product.id)
        self.assertEqual(found_product.name, product.name)
        self.assertEqual(found_product.description, product.description)
        self.assertEqual(found_product.price, product.price)
        self.assertEqual(found_product.available, product.available)
        self.assertEqual(found_product.category, product.category)
        assert found_product.available == True or found_product.available == False
        # assert found_product.category in range(0, len(Category))


    def test_update_a_product(self):

        """It should Update a Product"""

        product = ProductFactory()

        app.logger.info(f"The information about a {product} product to be updated in the database")

        product.id = None
        product.create()
        self.assertIsNotNone(product.id)

        found_product = Product.find(product.id)
        app.logger.info(f"The information about the {found_product} product fetched from the database")
        
        # Save the value of the product id in a local variable to use in assertions
        original_id = product.id

        # Update the description of product and save the updated version in the database
        product.description = "A new description"
        product.update()

        self.assertEqual(product.id, original_id)
        self.assertEqual(product.description, "A new description")

        # Fetch it back and test that the description has been changed,
        # while the id hasn't
        products = Product.all()
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].description, "A new description")
        self.assertEqual(products[0].id, original_id)


    def test_update_a_product_not_saved(self):

        """It should fail when updating a product that was not saved to the database"""

        product = ProductFactory()
        product.id = None
        self.assertRaises(DataValidationError, product.update)


    def test_delete_a_product(self):

        """It should Delete a Product"""

        product = ProductFactory()
        product.create()
        self.assertEqual(len(Product.all()), 1)

        # Remove the product from the database
        product.delete()
        self.assertEqual(len(Product.all()), 0)


    def test_list_all_products(self):

        """It should List all Products in the database"""

        products = Product.all()
        self.assertEqual(len(products), 0)

        # Create five products and save them to the database
        for _ in range(5):
            product = ProductFactory()
            product.create()

        # See if we get back 5 products
        products = Product.all()
        self.assertEqual(len(products), 5)


    def test_find_by_name(self):

        """It should Find a Product by Name"""

        # Create a batch of 5 Product objects using the ProductFactory and save them to the database
        products = ProductFactory.create_batch(5)
        for product in products:
            product.create()

        # Retrieve the name of the first product in the products list
        name = products[0].name

        # Count the number of occurrences of the product name in the list
        count = len([product for product in products if product.name == name])

        # Retrieve products from the database that have the specified name
        found = Product.find_by_name(name)

        # Assert if the count of the found products matches the expected count
        self.assertEqual(found.count(), count)

        # Assert that each product’s name matches the expected name
        for product in found:
            self.assertEqual(product.name, name)


    def test_find_by_availability(self):

        """It should Find Products by Availability"""

        # Create a batch of 10 Product objects using the ProductFactory and save them to the database.
        products = ProductFactory.create_batch(10)
        for product in products:
            product.create()

        # Retrieve the availability of the first product in the products list
        available = products[0].available

        # Count the number of occurrences of the product availability in the list
        count = len([product for product in products if product.available == available])

        # Retrieve products from the database that have the specified availability
        found = Product.find_by_availability(available)

        # Assert if the count of the found products matches the expected count
        self.assertEqual(found.count(), count)

        # Assert that each product's availability matches the expected availability
        for product in found:
            self.assertEqual(product.available, available)


    def test_find_by_category(self):

        """It should Find Products by Category"""

        # Create a batch of 10 Product objects using the ProductFactory and save them to the database
        products = ProductFactory.create_batch(10)
        for product in products:
            product.create()

        # Retrieve the category of the first product in the products list
        category = products[0].category

        # Count the number of occurrences of the product that have the same category in the list
        count = len([product for product in products if product.category == category])

        # Retrieve products from the database that have the specified category
        found = Product.find_by_category(category)

        # Assert if the count of the found products matches the expected count
        self.assertEqual(found.count(), count)

        # Assert that each product's category matches the expected category.
        for product in found:
            self.assertEqual(product.category, category)


    def test_deserialize_a_product(self):

        """It should Deserialize a product and raise appropiate exceptions for missing fields"""

        saved_product = ProductFactory()
        saved_product.id = None
        saved_product.create()
        product = {}
        with self.assertRaises(DataValidationError):
            saved_product.deserialize(product)
        product = saved_product.serialize()
        saved_product.deserialize(product)
        self.assertEqual(product['id'], saved_product.id)
        self.assertEqual(product['name'], saved_product.name)
        self.assertEqual(product['description'], saved_product.description)
        self.assertEqual(Decimal(product['price']), Decimal(saved_product.price))
        self.assertEqual(product['available'], saved_product.available)
        self.assertEqual(product['category'], saved_product.category.name)
        invalid_product = product.copy()
        invalid_product['available'] = 'Invalid value'
        with self.assertRaises(DataValidationError):
            saved_product.deserialize(invalid_product)
        saved_product.deserialize(product)
        invalid_product = product.copy()
        invalid_product['category'] = 'Invalid category'
        with self.assertRaises(DataValidationError):
            saved_product.deserialize(invalid_product)
        saved_product.deserialize(product)


    def test_find_by_price(self):

        """It should Find Products by Price"""

        price = Decimal(10.20)

        # Create a batch of 10 Product objects using the ProductFactory and save them to the database
        products = ProductFactory.create_batch(10)
        for index, product in products:
            if index == 5:
                product.price = price
            else:
                product.price = 20.00 + index
            product.create()

        # Retrieve products from the database that have the specified price
        found = Product.find_by_price(price)

        # Assert if the count of the found products matches the expected count
        self.assertEqual(found.count(), 1)

        # Assert that each product's category matches the expected category.
        for product in found:
            self.assertEqual(product.price, price)

