import os
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
import tempfile
from tssvr import app, ModelSize, APIOptions, process_transcription
import tssvr

client = TestClient(app)

class TestProcessAudio(unittest.TestCase):
    def setUp(self):
        # Upload a sample audio file
        with open("tests/sample_audio.wav", "rb") as f:
            response = client.post("/upload_audio", files={"audio_file": f})
            self.file_id = response.json()["file_id"]

    def tearDown(self):
        # Cleanup temp files if necessary
        pass

    def test_successful_transcription_different_models(self):
        for model in ModelSize:
            options = APIOptions(model=model)
            response = client.post(f"/process_audio/{self.file_id}", json=options.dict())
            self.assertEqual(response.status_code, 200, f"Failed for model {model}. Response: {response.content}")


    def test_successful_transcription_different_output_formats(self):
        for outfmt in ["txt", "srt"]:
            options = APIOptions(outfmt=outfmt)
            response = client.post(f"/process_audio/{self.file_id}", json=options.dict())
            self.assertEqual(response.status_code, 200)

    def test_handling_of_non_existent_file_id(self):
        options = APIOptions()
        response = client.post("/process_audio/non_existent_file_id", json=options.dict())
        self.assertEqual(response.status_code, 404)

    def test_handling_of_incorrect_options(self):
        incorrect_options = [
            APIOptions(model="invalid_model"),
            APIOptions(outfmt="invalid_outfmt")
        ]
        for options in incorrect_options:
            response = client.post(f"/process_audio/{self.file_id}", json=options.dict())
            self.assertEqual(response.status_code, 400)

    @patch("app.process_transcription", side_effect=Exception("Transcription failed", "Error details"))
    def test_handling_of_transcription_failure(self, mock_process_transcription):
        options = APIOptions()
        response = client.post(f"/process_audio/{self.file_id}", json=options.dict())
        self.assertEqual(response.status_code, 500)

if __name__ == "__main__":
    unittest.main()
