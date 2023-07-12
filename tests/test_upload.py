import os
import tempfile
import unittest
from fastapi.testclient import TestClient
from tssvr import app  

client = TestClient(app)

class TestUploadAudio(unittest.TestCase):

    def test_upload_audio_success(self):
        # Create a temporary file for testing
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
            temp_file.write(b"dummy content")
            temp_file_path = temp_file.name

        # Read the temporary file and send it as a request
        with open(temp_file_path, "rb") as file:
            response = client.post("/upload_audio", files={"audio_file": file})

        # Check if the response status code is 200 OK
        self.assertEqual(response.status_code, 200)

        # Check if the response contains a file_id
        self.assertIn("file_id", response.json())

        # Clean up the temporary file
        os.remove(temp_file_path)

    def test_upload_audio_invalid_file(self):
        response = client.post("/upload_audio", data={"audio_file": "invalid_file"})
        self.assertEqual(response.status_code, 422)

    def test_upload_audio_invalid_extension(self):
        # Create a temporary file with an unapproved extension
        with tempfile.NamedTemporaryFile(delete=False, suffix=".unapproved") as temp_file:
            temp_file.write(b"dummy content")
            temp_file_path = temp_file.name

        # Read the temporary file and send it as a request
        with open(temp_file_path, "rb") as file:
            response = client.post("/upload_audio", files={"audio_file": file})

        # Check if the response status code is 400 Bad Request
        self.assertEqual(response.status_code, 400)

        # Clean up the temporary file
        os.remove(temp_file_path)

if __name__ == "__main__":
    unittest.main()
