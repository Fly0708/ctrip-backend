from pathlib import Path, WindowsPath
from dotenv import load_dotenv

root_path: Path = Path(__file__).parent.parent

resource_path: Path = root_path / 'resource'

load_dotenv(dotenv_path=root_path / '.env')
