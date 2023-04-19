from typing import Any
from pprint import pprint
from datetime import datetime  

def rprint(object:Any, source:str, success:bool = True):
    if isinstance(object, dict):
        print("........................................................", "[start]")
        print(datetime.utcnow(), "::", source, "\n")
        pprint(object)
        state = "[OK]" if success else "[Failed]"
        print("........................................................", state, "\n")
    else:
        state = "[OK]" if success else "[Failed]"
        print(datetime.utcnow(), "::", source, "::", object, state, "\n")

