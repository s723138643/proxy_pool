import logging

# verify settings
VERIFY_TARGET = 'http://www.baidu.com'
VERIFY_TIMEOUT = 15

# refresh settings
FETCH_TIMEOUT = 60
FETCH_INTERVAL = 5 * 60
REFRESH_INTERVAL = 20 * 60

# server settings
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 5000

# logging
LOGFMT = '%(asctime)s %(name)s:: %(message)s'
LOGDATEFMT = '%Y-%m-%d %H:%M:%S'
LOGLEVEL = logging.INFO