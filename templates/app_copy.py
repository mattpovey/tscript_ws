import os
import openai
import tempfile
import pysrt
import json
import requests
import re
import support_funcs
from support_funcs import gpt_proc, split_text, tok_count
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from werkzeug.utils import secure_filename
from werkzeug.exceptions import BadRequest
from datetime import timedelta
from pydub import AudioSegment

app = Flask(__name__)
CORS(app)
app.config['upload_dir'] = 'uploads'
app.config['allowed_exts'] = {'wav', 'mp3', 'ogg', 'm4a', 'mp4'}
app.config['model'] = 'gpt-4'
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.errorhandler(BadRequest)
def handle_bad_request(e):
    return jsonify(error=str(e)), 400

def rename_m4a(file_path, new_ext='mp4'):
    # ffmpeg seems to have problems with m4a files which are resolved if they 
    # are renamed to mp4 first
    print("Renaming M4A to MP4")
    new_file_path = file_path.rsplit('.', 1)[0] + "." + new_ext
    os.rename(file_path, new_file_path)
    return new_file_path

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['allowed_exts']

# Split audio into chunks of 25MB
# The OpenAI API has a limit of 25MB per request
def split_audio(file_path, max_size_bytes=25 * 1024 * 1024, file_ext=None):
    print("In split_audio(), file path: " + file_path)
    print("In split_audio(), file extension: " + file_ext)

    file_size = os.path.getsize(file_path)

    if file_size <= max_size_bytes:
        print("File size is less than max size")
        return [AudioSegment.from_file(file_path, format=file_ext)]

    audio_formats = {'mp3': 'from_mp3', 'mp4': 'from_file', 'm4a': 'from_file', 'wav': 'from_wav'}
    audio_func = audio_formats.get(file_ext, 'from_wav')
    print("Audio function: " + audio_func)
    audio = getattr(AudioSegment, audio_func)(file_path)

    chunk_length = int((len(audio) * max_size_bytes) / file_size)
    print("Chunk length: " + str(chunk_length))
    
    #audio_chunks = [audio[i:i+chunk_length] for i in range(0, len(audio), chunk_length)]
    audio_chunks = []
    for i in range(0, len(audio), chunk_length):
        chunk = audio[i:i+chunk_length]
        audio_chunks.append(chunk)
    audio_segments = []

    for chunk in audio_chunks:
        audio_segments.extend(chunk.split_to_mono())

    return audio_segments

@app.route('/')
def index():
    print("Serving index.html")
    return render_template('index.html')

@app.route('/transcribe', methods=['POST'])
def transcribe_audio():
    if request.method == 'POST': # Seems to hang sometimes after this. Doesnt' get into the next statement...  print("/transcribe received POST request") # Setup the file if 'file' not in request.files: return jsonify(error='No file part'), 400 print("No file part") file = request.files['file'] print(file.filename) # Setup options resp_format = request.form.get('output-format') print(resp_format) # Get engine to determine which API to use # openai_api or local_whisper engine = request.form.get('engine') model = request.form.get('model') lang = request.form.get('language') translate = request.form.get('translate') processing = request.form.get('processing') processing_role = request.form.get('processing-role') # Create a dictionary to store the output

        if 'file' not in request.files:
            return jsonify(error='No file part'), 400
        file = request.files['file']
        resp_format = request.form.get('output-format')
        print("The transcript for, " + file.name + " will be in " + resp_format + " format.")
        # Get engine to determine which API to use
        # openai_api or local_whisper
        engine = request.form.get('engine')
        model = request.form.get('model')
        lang = request.form.get('language')
        translate = request.form.get('translate')
        summarize = request.form.get('summarize')
        processing = request.form.get('processing')
        processing_role = request.form.get('processing-role')

        # Create a dictionary to store the output
        output = {}

        if file.filename == '':
            return jsonify(error='No selected file'), 400

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['upload_dir'], filename)
            print("Saving file locally: " + file_path)
            try:
                file.save(file_path)
            except Exception as e:
                print(e)
                return jsonify(error='Error saving file'), 500

            # Create a dictionary to store the output for OpenAI transcriptions
            transcriptions = []
            # Create a dictionary to store the output of local (tssvr) transcriptions
            transcriptions_json = []

            if engine == 'openai_api':
                # Option is misspelled in index.html
                if resp_format == 'txt':
                    resp_format = 'text'
                print("Using OpenAI API")
                f_ext = file_path.rsplit('.', 1)[1].lower()

                # the ffmpeg library on MacOS has problems with m4a files
                # they can be renamed to mp4 without any issues
                if f_ext == 'm4a':
                    file_path = rename_m4a(file_path, 'mp4')
                    # update file_extension to mp4
                    print(file_path)
                    f_ext = file_path.rsplit('.', 1)[1].lower()

                # Split audio into chunks - split_audio returns a list of AudioSegment objects
                # file_ext=file_ext is gross. Shouldn't use same variable name.
                # OpenAI max size should be stored in one place...
                audio_chunks = split_audio(file_path, max_size_bytes=25 * 1024 * 1024, file_ext=f_ext)
                print(f"Audio chunks: {len(audio_chunks)}")

                for index, chunk in enumerate(audio_chunks):
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{f_ext}') as chunk_file:
                        chunk.export(chunk_file.name, format=f_ext)
                        print(f"Sending chunk {index + 1} to API: {chunk_file.name}")
                        with open(chunk_file.name, 'rb') as audio_file:
                            # Use openai.Audio.transcribe if 'translate' is false
                            # Use openai.Audio.translate if 'translate' is true
                            if translate == "true":     
                                print("Translating")
                                # Translation is always to English and language detection is automatic and cannot be specified.
                                transcript = openai.Audio.translate(model="whisper-1", file=audio_file, response_format=resp_format)
                            else:
                                print("Transcribing")
                                # The API only takes the language parameter to when NOT translating.
                                transcript = openai.Audio.transcribe("whisper-1", audio_file, response_format=resp_format, language=lang)
                        os.remove(chunk_file.name)

                        # add the current chunk to transcriptions
                        transcriptions.append(transcript)
                        print(transcriptions)
                        print(transcriptions[0])

            else:
                # Run using the local API
                print("Using local API via tssvr")
                print(file_path)

                BASE_URL = "http://ragnar.sys.kyomu.co.uk:8000"

                with open(file_path, "rb") as f:
                    print("Uploading audio file...")
                    try:
                        upload_response = requests.post(f"{BASE_URL}/upload_audio", files={"audio_file": f})

                    except upload_response.status_code != 200 as e:
                        print("Error uploading audio file:", upload_response.text)
                        return e

                file_id = upload_response.json()["file_id"]
                print("File ID: ", file_id, "\n")

                if resp_format == "text":
                    print("Output format is text")
                    resp_format = "txt"

                # Process the audio file
                options = {
                    "model": model,
                    "translate": translate,
                    "language": lang,
                    "outfmt": resp_format,
                }
                print("Requesting transcription of: ", file_id, "with options:", options, "\n")

                transcript = requests.post(f"{BASE_URL}/process_audio", json=options, params={"file_id": file_id})
                transcriptions.append(transcript.text)

                print("Attempting conversion of response object to JSON")
                transcriptions_json.append(jsonify(transcript.text))
                print("Conversion successful")
                # print(transcriptions)
                # print(transcriptions[0])

                if transcript.status_code != 200:
                    print("Error processing audio file:", transcript.text)
                    return
        
        # Summarize the transcription if summarize is true
        if processing == "true":
            if app.config['model'] == "gpt-4":
                m_tok = 4096 # half of 8192
            else:
                m_tok = 800
            print("processing_role: " + processing_role)
            tscript = transcriptions[0]
            # TODO: Next job is to get search the roles dict for the name rather than pass it directly
            # TODO: Also allow for a custom role description

            # gpt_proc(text, sys_role, max_tokens=800, remember="false")
            # Remember is an attempt to give GPT a memory of the previous summary to enable summaries of longer items
            summary = gpt_proc(text=tscript, sys_role=processing_role, max_tokens=m_tok, remember="false")
            print("-----------\nSummary:\n-----------")
            print(summary)
            tscript = transcriptions[0]
            output['summary'] = summary
            output['transcript'] = tscript
        else:
            # Return the text of the transcription from the list
            output['summary'] = "No summarization requested"
            output['transcript'] = transcriptions[0]
    
        print("Attempting to return")
        return output
    
if __name__ == '__main__':
    app.run(debug=True, port=5007)


