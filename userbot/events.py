# KingTG UserBot - Events Uyumluluk Modülü
from telethon import events
import functools

_client = None
_pending_handlers = []

# NewMessage'ın desteklediği parametreler
VALID_PARAMS = {
    'incoming', 'outgoing', 'from_users', 'forwards', 'pattern',
    'chats', 'blacklist_chats', 'func'
}

def set_client(client):
    global _client
    _client = client
    for handler, event in _pending_handlers:
        _client.add_event_handler(handler, event)
    _pending_handlers.clear()

def register(outgoing=True, incoming=False, pattern=None, **kwargs):
    # Bilinmeyen parametreleri filtrele (disable_errors, allow_sudo vb.)
    filtered_kwargs = {k: v for k, v in kwargs.items() if k in VALID_PARAMS}
    
    def decorator(func):
        event = events.NewMessage(
            outgoing=outgoing,
            incoming=incoming,
            pattern=pattern,
            **filtered_kwargs
        )
        
        @functools.wraps(func)
        async def wrapper(event):
            try:
                return await func(event)
            except Exception as e:
                # disable_errors=True olan pluginler için hataları yut
                print(f"[PLUGIN HATA] {func.__name__}: {e}")
                return None
        
        if _client is not None:
            _client.add_event_handler(wrapper, event)
        else:
            _pending_handlers.append((wrapper, event))
        
        return wrapper
    return decorator

def on(event):
    def decorator(func):
        if _client is not None:
            _client.add_event_handler(func, event)
        else:
            _pending_handlers.append((func, event))
        return func
    return decorator
