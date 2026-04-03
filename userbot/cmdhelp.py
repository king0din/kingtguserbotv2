# KingTG UserBot - CmdHelp Uyumluluk Modülü
_help_dict = {}

class CmdHelp:
    def __init__(self, module_name):
        self.module_name = module_name
        self.commands = []
        self.info = None
    
    def add_command(self, command, params=None, description=None, example=None):
        self.commands.append({
            'command': command,
            'params': params,
            'description': description,
            'example': example
        })
        return self
    
    def add_info(self, info):
        self.info = info
        return self
    
    def add(self):
        _help_dict[self.module_name] = {
            'commands': self.commands,
            'info': self.info
        }
        return self

def get_all_help():
    return _help_dict

def get_help(module_name):
    return _help_dict.get(module_name)

def format_help(module_name):
    help_data = get_help(module_name)
    if not help_data:
        return None
    
    text = f"**📖 {module_name} Yardım**\n\n"
    
    for cmd in help_data['commands']:
        text += f"• `.{cmd['command']}`"
        if cmd['params']:
            text += f" `{cmd['params']}`"
        text += "\n"
        if cmd['description']:
            text += f"  ➥ {cmd['description']}\n"
        if cmd['example']:
            text += f"  📝 Örnek: `{cmd['example']}`\n"
        text += "\n"
    
    if help_data['info']:
        text += f"ℹ️ {help_data['info']}"
    
    return text
