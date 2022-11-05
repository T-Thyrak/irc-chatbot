class DualMap:
    def __init__(self, items: dict = None, *args, **kwargs):
        self._map = {}
        
        if items is not None:
            for key, value in items.items():
                self._map[key] = value
                self._map[value] = key
                
    def __getitem__(self, key):
        return self._map[key]
    
    def __setitem__(self, key, value):
        self._map[key] = value
        self._map[value] = key
    
    def __delitem__(self, key):
        # key and value might be the same
        value = self._map.get(key)
        if value != key:
            del self._map[value]
        
        del self._map[key]
        
    def get(self, key, default=None):
        return self._map.get(key, default)