# KingTG UserBot - Utils Uyumluluk Modülü
import asyncio
import subprocess

async def edit_or_reply(event, text, **kwargs):
    try:
        return await event.edit(text, **kwargs)
    except:
        return await event.reply(text, **kwargs)

async def edit_delete(event, text, time=5):
    msg = await event.edit(text)
    await asyncio.sleep(time)
    await msg.delete()

def run_command(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout or result.stderr
    except Exception as e:
        return str(e)

async def run_command_async(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    return stdout.decode() or stderr.decode()

TEMP_DIR = "/tmp"
CMD_HELP = {}
CMD_LIST = {}
SUDO_LIST = []
BLACKLIST = []
