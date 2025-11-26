import unittest
import requests
import json
import os
from typing import Dict, Any

class TestMCPServer(unittest.TestCase):    
    BASE_URL = "http://localhost:8002"
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def test_health_check(self):
        """Test the health check endpoint."""
        response = self.session.get(f"{self.BASE_URL}/health")
        self.assertEqual(response.status_code, 200)
        self.assertIn("status", response.json())
        self.assertEqual(response.json()["status"], "ok")
    
    def test_list_tools(self):
        """Test the list tools endpoint."""
        response = self.session.get(f"{self.BASE_URL}/tools")
        self.assertEqual(response.status_code, 200)
        tools = response.json()
        self.assertIn("text_processor", tools)
    
    def test_text_processor_uppercase(self):
        """Test the text processor with uppercase transformation."""
        test_cases = [
            ("hello", "HELLO"),
            ("Test Case", "TEST CASE"),
            ("123abc", "123ABC")
        ]
        
        for input_text, expected_output in test_cases:
            with self.subTest(input_text=input_text):
                payload = {
                    "text": input_text,
                    "params": {"to_upper": True}
                }
                response = self.session.post(
                    f"{self.BASE_URL}/process",
                    json=payload
                )
                
                self.assertEqual(response.status_code, 200, 
                              f"Unexpected status code for input: {input_text}")
                
                result = response.json()
                self.assertIn("result", result, 
                            f"Response missing 'result' key for input: {input_text}")
                
                # Check the text processor result
                result_data = result["result"]
                text_processor_result = result_data.get("results", {}).get("text_processor", {})
                
                # Check the transformed text
                self.assertIn("transformed_text", text_processor_result,
                            f"No 'transformed_text' in response for input: {input_text}")
                self.assertEqual(text_processor_result["transformed_text"], expected_output,
                              f"Unexpected transformed_text for input: {input_text}")
                
                # Check the uppercase field is present and correct
                self.assertIn("uppercase", text_processor_result,
                            f"No 'uppercase' in response for input: {input_text}")
                self.assertEqual(text_processor_result["uppercase"], expected_output,
                              f"Uppercase transformation failed for input: {input_text}")
                
                # Check metadata
                self.assertIn("metadata", result_data)
                metadata = result_data["metadata"]
                self.assertIn("params_used", metadata)
                self.assertIn("transformation_applied", metadata)
                self.assertTrue(metadata["transformation_applied"])
                self.assertEqual(text_processor_result["transformed_text"], input_text.upper())
    
    def test_text_processor_lowercase(self):
        """Test the text processor with lowercase transformation."""
        payload = {
            "text": "HELLO World",
            "params": {"to_lower": True}
        }
        response = self.session.post(
            f"{self.BASE_URL}/process",
            data=json.dumps(payload)
        )
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        print(f"Response JSON: {json.dumps(result, indent=2)}")
        self.assertTrue(result["success"])
        
        # Check the basic response structure
        self.assertIn("result", result)
        result_data = result["result"]
        self.assertEqual(result_data["original_text"], "HELLO World")
        
        # Check metadata
        self.assertIn("metadata", result_data)
        metadata = result_data["metadata"]
        self.assertIn("params_used", metadata)
        self.assertIn("to_lower", metadata["params_used"])
        self.assertTrue(metadata["params_used"]["to_lower"])
        self.assertIn("transformation_applied", metadata)
        self.assertTrue(metadata["transformation_applied"])
        
        # Check text processor results
        self.assertIn("results", result_data)
        self.assertIn("text_processor", result_data["results"])
        
        text_processor_result = result_data["results"]["text_processor"]
        self.assertEqual(text_processor_result["original_text"], "HELLO World")
        self.assertEqual(text_processor_result["length"], 11)
        self.assertEqual(text_processor_result["word_count"], 2)
        self.assertEqual(text_processor_result["line_count"], 1)
        
        # Check that transformed_text is in the response and has the expected value
        self.assertIn("transformed_text", text_processor_result)
        self.assertEqual(text_processor_result["transformed_text"], "hello world")
    
    def test_text_processor_title_case(self):
        """Test the text processor with title case transformation."""
        payload = {
            "text": "hello world",
            "params": {"title_case": True}
        }
        response = self.session.post(
            f"{self.BASE_URL}/process",
            data=json.dumps(payload)
        )
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        print(f"Response JSON: {json.dumps(result, indent=2)}")
        self.assertTrue(result["success"])
        
        # Check the basic response structure
        self.assertIn("result", result)
        result_data = result["result"]
        self.assertEqual(result_data["original_text"], "hello world")
        
        # Check metadata
        self.assertIn("metadata", result_data)
        metadata = result_data["metadata"]
        self.assertIn("params_used", metadata)
        self.assertIn("title_case", metadata["params_used"])
        self.assertTrue(metadata["params_used"]["title_case"])
        self.assertIn("transformation_applied", metadata)
        self.assertTrue(metadata["transformation_applied"])
        
        # Check text processor results
        self.assertIn("results", result_data)
        self.assertIn("text_processor", result_data["results"])
        
        text_processor_result = result_data["results"]["text_processor"]
        self.assertEqual(text_processor_result["original_text"], "hello world")
        self.assertEqual(text_processor_result["length"], 11)
        self.assertEqual(text_processor_result["word_count"], 2)
        self.assertEqual(text_processor_result["line_count"], 1)
        
        # Check that transformed_text is in the response and has the expected value
        self.assertIn("transformed_text", text_processor_result)
        self.assertEqual(text_processor_result["transformed_text"], "Hello World")
    
    def test_text_processor_reverse(self):
        """Test the text processor with reverse transformation."""
        payload = {
            "text": "hello",
            "params": {"reverse": True}
        }
        response = self.session.post(
            f"{self.BASE_URL}/process",
            data=json.dumps(payload)
        )
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        print(f"Response JSON: {json.dumps(result, indent=2)}")
        self.assertTrue(result["success"])
        
        # Check the basic response structure
        self.assertIn("result", result)
        result_data = result["result"]
        self.assertEqual(result_data["original_text"], "hello")
        
        # Check metadata
        self.assertIn("metadata", result_data)
        metadata = result_data["metadata"]
        self.assertIn("params_used", metadata)
        self.assertIn("reverse", metadata["params_used"])
        self.assertTrue(metadata["params_used"]["reverse"])
        self.assertIn("transformation_applied", metadata)
        self.assertTrue(metadata["transformation_applied"])
        
        # Check text processor results
        self.assertIn("results", result_data)
        self.assertIn("text_processor", result_data["results"])
        
        text_processor_result = result_data["results"]["text_processor"]
        self.assertEqual(text_processor_result["original_text"], "hello")
        self.assertEqual(text_processor_result["length"], 5)
        self.assertEqual(text_processor_result["word_count"], 1)
        self.assertEqual(text_processor_result["line_count"], 1)
        
        # Check that transformed_text is in the response and has the expected value
        self.assertIn("transformed_text", text_processor_result)
        self.assertEqual(text_processor_result["transformed_text"], "olleh")
    
    def test_text_processor_strip(self):
        """Test the text processor with strip transformation."""
        payload = {
            "text": "  hello  ",
            "params": {"strip": True}
        }
        response = self.session.post(
            f"{self.BASE_URL}/process",
            data=json.dumps(payload)
        )
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        print(f"Response JSON: {json.dumps(result, indent=2)}")
        self.assertTrue(result["success"])
        
        # Check the basic response structure
        self.assertIn("result", result)
        result_data = result["result"]
        self.assertEqual(result_data["original_text"], "  hello  ")
        
        # Check metadata
        self.assertIn("metadata", result_data)
        metadata = result_data["metadata"]
        self.assertIn("params_used", metadata)
        self.assertIn("strip", metadata["params_used"])
        self.assertTrue(metadata["params_used"]["strip"])
        self.assertIn("transformation_applied", metadata)
        self.assertTrue(metadata["transformation_applied"])
        
        # Check text processor results
        self.assertIn("results", result_data)
        self.assertIn("text_processor", result_data["results"])
        
        text_processor_result = result_data["results"]["text_processor"]
        self.assertEqual(text_processor_result["original_text"], "  hello  ")
        self.assertEqual(text_processor_result["length"], 9)  # Original length with spaces
        self.assertEqual(text_processor_result["word_count"], 1)
        self.assertEqual(text_processor_result["line_count"], 1)
        
        # Check that transformed_text is in the response and has the expected value
        self.assertIn("transformed_text", text_processor_result)
        self.assertEqual(text_processor_result["transformed_text"], "hello")
    
    def test_invalid_parameters(self):
        """Test the text processor with invalid parameters."""
        # No params provided
        payload = {"text": "test"}
        response = self.session.post(
            f"{self.BASE_URL}/process",
            data=json.dumps(payload)
        )
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertTrue(result["success"])
        self.assertFalse(result["result"]["metadata"]["transformation_applied"])
        
        # Invalid parameter
        payload = {
            "text": "test",
            "params": {"invalid_param": True}
        }
        response = self.session.post(
            f"{self.BASE_URL}/process",
            data=json.dumps(payload)
        )
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertTrue(result["success"])
        self.assertFalse(result["result"]["metadata"]["transformation_applied"])

if __name__ == "__main__":
    unittest.main()
