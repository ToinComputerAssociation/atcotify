"""テスト用の最小限の env/config.ini を用意する。

一部のモジュールは import 時に Config を読み、config.ini が無いと
KeyError になる。config.ini は .gitignore 対象（*.ini）なので、
存在しない場合だけダミーを作り、セッション終了時に消す。
"""

import atexit
from pathlib import Path

_CONFIG_INI = Path(__file__).resolve().parent.parent / "env" / "config.ini"

_DUMMY = """\
[TOKEN]
TOKEN = dummy
[SEASON]
SEASON = dummy
[ATCODER]
ATCODER_USERNAME = dummy
ATCODER_PASSWORD = dummy
[GOOGLE]
SERVICE_ACCOUNT_FILE = dummy.json
SPREADSHEET_ID = dummy
SHEET_NAME = dummy
[YEAR]
YEAR = 2026
"""

if not _CONFIG_INI.exists():
    _CONFIG_INI.write_text(_DUMMY, encoding="utf-8")
    atexit.register(lambda: _CONFIG_INI.unlink(missing_ok=True))
