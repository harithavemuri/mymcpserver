import unittest
import sys
import asyncio
from tests.test_api import test_search_customers

class TestSearchCustomers(unittest.IsolatedAsyncioTestCase):
    async def test_search_customers_runner(self):
        await test_search_customers()

if __name__ == "__main__":
    unittest.main()
