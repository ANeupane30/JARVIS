import sherpa_onnx
import configparser
import queue
from listener import process_audio_stream, audio_queue


# initializing configparser
config = configparser.ConfigParser()
config.read("config/sherpa_onnx.config") # config for keyword spotter
config.read("config/sounddevice.config")  # config for keyword spotter audio


# loading value for Keyword Spotter Audio
sample_rate = int(config['kws_audio']['SAMPLE_RATE'])
block_duration = float(config['kws_audio']['BLOCK_DURATION'])
channels = int(config['kws_audio']['CHANNELS'])


# loading value for Keyword Spotter 
tokens=str(config['kws']['TOKEN'])
encoder=str(config['kws']['ENCODER'])
decoder=str(config['kws']['DECODER'])
joiner=str(config['kws']['JOINER'])
num_threads=int(config['kws']['NUM_THREADS'])
max_active_paths=int(config['kws']['MAX_ACTIVE_PATHS'])
keywords_file=str(config['kws']['KEYWORDS_FILE'])
keywords_score=float(config['kws']['KEYWORD_SCORE'])
keywords_threshold=float(config['kws']['KEYWORD_THRESHOLD'])
num_trailing_blanks=int(config['kws']['NUM_TRAILING_BLANKS'])
provider=str(config['kws']['PROVIDER'])

# instantiate the keyword spotter function from sherpa-onnx
keyword_spotter = sherpa_onnx.KeywordSpotter(
    tokens= tokens,
    encoder= encoder,
    decoder= decoder,
    joiner= joiner,
    num_threads= num_threads,
    max_active_paths= max_active_paths,
    keywords_file= keywords_file,
    keywords_score= keywords_score,
    keywords_threshold= keywords_threshold,
    num_trailing_blanks= num_trailing_blanks,
    provider= provider,
)

def kws():
    # instantiate stream for KWS 
    kws_stream = keyword_spotter.create_stream()
    device_stream = process_audio_stream(sample_rate, channels, block_duration)
    try:
        print("Listening for keyword... (Ctrl+C to stop)")
        while True:
            try:
                samples = audio_queue.get(timeout=0.1)
            except queue.Empty:
                continue
            
            # Flatten the 2D array into 1D array
            samples = samples.reshape(-1)
            # feed audio into  the sherpa-onnx decoder
            kws_stream.accept_waveform(sample_rate, samples)
            
            # Check if the AI model has enough context window to evaluate the speech 
            while keyword_spotter.is_ready(kws_stream):
                keyword_spotter.decode_stream(kws_stream)
                
            # fetch detection results
            result = keyword_spotter.get_result(kws_stream)
            # return result <-- uncomment this and comment print when you complete Speech Recognition system
            if result:
                print(f"\n🎯 KEYWORD DETECTED: {result}")
                kws_stream = keyword_spotter.create_stream()
    except KeyboardInterrupt:
        print("\n🛑 Execution stopped safely by user.")
    finally: # closing the background audio process
        device_stream.stop()
        device_stream.close()
        # print('Error')

        

test = kws()
print(test)