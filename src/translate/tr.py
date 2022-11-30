import os
import json

def __(key: str, lang: str) -> str:
    """Get the translation of a key string in the given language.

    Args:
        key (str): The string key
        lang (str): The language to translate to

    Returns:
        str: The translated string. If the key is not found, the key itself is returned.
        
    Raises:
        KeyError: If the language is not supported.
    """
    
    if not os.path.exists(os.path.abspath(f'src/translate/translations/{lang}.json')):
        raise KeyError(f'`{lang}` is not a supported language')
    
    with open(f'src/translate/translations/{lang}.json') as f:
        data = json.load(f)
        
        keys = key.split('.')
        
        try:       
            for k in keys:
                data = data[k]
        except KeyError:
            return key
        return data