* Enable operation on AWS or Azure
* Make sure that uploaded files are cleaned up - they don't get deleted if the processing fails.
* Use Celery to manage the transcription and processing tasks and provide better feedback to the user
* Allow for user specified system messages in processing
* Allow the user to select the GPT version (3.5-Turbo, 3.5 16K, 4 and 4 32K)