import sherpa_onnx
import configparser

# initializing configparser
config = configparser.ConfigParser()
config.read_file("/config/sherpa_onnx.config")

# loading value from cofing file
tokens=config.TOKEN,
encoder=config.ENCODER,
decoder=config.DECODER,
joiner=config.JOINER,
num_threads=config.NUM_THREADS,
max_active_paths=config.MAX_ACTIVE_PATHS,
keywords_file=config.KEYWORDS_FILE,
keywords_score=config.KEYWORD_SCORE,
keywords_threshold=config.KEYWORD_THRESHOLD,
num_trailing_blanks=config.NUM_TRAILING_BLANKS,
provider=config.PROVIDER,

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