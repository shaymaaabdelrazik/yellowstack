
# Add timezone configuration to Python code

import os
os.environ['TZ'] = 'America/Toronto'

# This makes Python use the system timezone settings
try:
    import time
    time.tzset()
except AttributeError:
    # time.tzset() is not available on Windows
    pass
