# Installation

* Clone the repository
* Create a `.env` file in the root directory and add your API key with `OPENAI_API_KEY=[YOUR_API_KEY]`. The tool will run without a key but will only be able to perform transcriptions using the local whisper.cpp installation
* The application can be run directly with by setting up a virtual env and running ```pip install -r requirements.txt``` followed by ```python ./tscript_ws.py```.
* It can also be run as a Docker container  
  * Create a Docker image with ```docker build -t tscript_ws .```
  * Run the container with ```docker run -p 127.0.0.1:8008:8008 --env-file .env --name tscript_ws tscript_ws```
* The application will be available at http://127.0.0.1:5000 if run directly and http://127.0.0.1:8008 if run in a docker container or via gunicorn.
* The application can be run on an external interface by running ```docker run --net host --env-file .env --name tscript_ws tscript_ws```
* The port can be changed by updating the dockerfile and gunicorn_conf.py

# Simple Audio Transcription and OpenAI LLM Based Processing Pipeline

A Flask application providing two primary API endpoints (`/transcribe` and `/process`). The `/transcribe` enpoint allows users to transcribe audio files. Transcription is performed directly using the `whisper.cpp` package which runs as a subprocess. The code allows for the small, medium or large models to be used but this can be customized easily in the code and by updating the dockerfile to retrieve different models. This allows for recordings that should not be processed in the cloud to be transcribed quickly and reliably. The endpoint also allows use of the OpenAI Whisper API which requires access to a API key.

The tool allows transcriptions to be optionally processed by one of the OpenAI GPT models. This also requires access to an OpenAI API key. The code currently defaults to the gpt-3.5-turbo model but this can be changed by editing the default value in `tscript_ws.py` (```ts_flask_app.config['model'] = 'gpt-3.5-turbo'```). Making this user selectable from the HTML form is a *todo*. The code makes no attempt to prevent processing by the API so care should be taken not to do so for confidential audio or transcriptions. 

# Transcription API

## POST /transcribe

This API endpoint transcribes audio files. It accepts both local files and files from URLs, and uses either the OpenAI API or a local installation of whisper.cpp for the transcription. It can transcribe in multiple languages and return the transcription in multiple formats. It can optionally translate from the source language to English.

# Process API Documentation

TODO

## Supporting Functions

Supporting functions for OpenAI API processing of text are in gpt_processing.py.

### split_audio(file_path, max_size_bytes=25 * 1024 * 1024, file_ext=None)
The OpenAI Whisper API accepts files with a maximum size of 25MB. This function uses the `pydub` library as per the OpenAI API documentation to split audio into appropriate sized chunks for use with the API. 

### convert_to_wav(input_file_path: str, output_wav_file_path: str)
Uses ffmpeg to convert input audio files to wav for processing by the local whisper.cpp instance. TODO: check this isn't being used by the OpenAI API path.

### tok_count(text, model="gpt-4")

This function counts the number of tokens in a given piece of text using OpenAI's `tiktoken` library. The function takes two arguments: the text to be tokenized and the model to use for tokenization. By default, it uses the "gpt-4" model. Easily modified to return tokens for embeddings.

### split_text(text, max_tokens)

This function splits a given piece of text into chunks for processing by a GPT API. Each chunk will contain the specified number of tokens defined by the token limit of the processor used plus or minus some tokens as a result of splitting on sentence boundries. 

### gpt_proc(text, sys_role, gpt_model="gpt-3.5-turbo", remember="true")

This function takes a piece of text and processes it based on a specified role. It uses the OpenAI API to generate a summary of the text according to the role. The function takes four arguments: the text to be processed, the system role to use for processing, and a boolean flag indicating whether to remember previous summaries and feed them back into the GPT API with the next chunk of text. This is done to retain context while summarizing or working on longer pieces of text because the API does not retain this automatically between calls.

The function first splits the text into chunks using the `split_text` function. It then iterates over each chunk, sending it to the OpenAI API for processing, and concatenating the results to form the final summary.

## System Roles

The code defines a list of system roles. Each role has an associated description, and is used to guide the style and content of the text processing. The roles are:

- **mtg_notes**: An assistant that summarizes what was discussed in meetings.
- **iview_summary**: An interviewer that transcribes an interview so that questions and answers are identified clearly.
- **pod_summary**: Summarizes the podcast transcript to highlight what's most interesting.
- **expand**: A copywriter who expands a short piece of text to make it longer, building on the points in the original text to keep the new text on topic.
- **test**: This is a test role. Responds with the first sentence of the text provided and the word TEST.

It's straightforward to let users write their own roles - a TODO. 

