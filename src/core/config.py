import os
from datetime import datetime
max_file_size = 10 * 1024 * 1024
media_root = os.path.join(os.getcwd(), "src", "media_root", datetime.now().date().strftime('%Y/%m/%d'))
os.makedirs(media_root, exist_ok=True)