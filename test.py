import os
from pathlib import Path

Path(f'/{os.path.join(os.getpwd(),"/edge_list.json")}').touch()