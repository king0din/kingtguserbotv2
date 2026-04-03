# KingTG UserBot - Chess (Satranç) Plugin
# İki kişilik satranç oyunu - Inline butonlarla
# Kullanım: .chess @kullanıcı veya .chess 123456789 veya yanıtla .chess

from telethon import events, Button
import hashlib
import time
import asyncio

GAMES = {}

PIECES = {
    'wr': '♖', 'wn': '♘', 'wb': '♗', 'wq': '♕', 'wk': '♔', 'wp': '♙',
    'br': '♜', 'bn': '♞', 'bb': '♝', 'bq': '♛', 'bk': '♚', 'bp': '♟'
}

def create_board():
    return [
        ['br', 'bn', 'bb', 'bq', 'bk', 'bb', 'bn', 'br'],
        ['bp', 'bp', 'bp', 'bp', 'bp', 'bp', 'bp', 'bp'],
        ['', '', '', '', '', '', '', ''],
        ['', '', '', '', '', '', '', ''],
        ['', '', '', '', '', '', '', ''],
        ['', '', '', '', '', '', '', ''],
        ['wp', 'wp', 'wp', 'wp', 'wp', 'wp', 'wp', 'wp'],
        ['wr', 'wn', 'wb', 'wq', 'wk', 'wb', 'wn', 'wr']
    ]

def create_board_buttons(game_id, board, selected=None, valid_moves=None, flipped=False, highlight=None):
    valid_moves = valid_moves or []
    buttons = []
    
    rows = range(7, -1, -1) if flipped else range(8)
    cols = range(7, -1, -1) if flipped else range(8)
    
    for row in rows:
        row_buttons = []
        for col in cols:
            piece = board[row][col]
            symbol = PIECES.get(piece, '')
            
            if highlight and (row, col) in highlight:
                if symbol:
                    symbol = f"⟨{symbol}⟩"
                else:
                    symbol = "◈"
            elif not symbol:
                if (row, col) in valid_moves:
                    symbol = "•"
                else:
                    symbol = " "
            elif (row, col) == selected:
                symbol = "🔵"
            elif (row, col) in valid_moves:
                symbol = "❌"
            
            row_buttons.append(Button.inline(symbol, f"ch_{game_id}_{row}_{col}"))
        buttons.append(row_buttons)
    
    buttons.append([
        Button.inline("Son Hamle ⏮", f"chlast_{game_id}"),
        Button.inline("Pes Et🏳️", f"chres_{game_id}"),
        Button.inline("Yeni🔄", f"chnew_{game_id}")
    ])
    
    return buttons

def get_valid_moves(board, row, col, check_check=True):
    piece = board[row][col]
    if not piece:
        return []
    
    color = piece[0]
    piece_type = piece[1]
    moves = []
    
    def valid(r, c): return 0 <= r < 8 and 0 <= c < 8
    def enemy(r, c): return valid(r, c) and board[r][c] and board[r][c][0] != color
    def empty(r, c): return valid(r, c) and not board[r][c]
    def empty_or_enemy(r, c): return valid(r, c) and (not board[r][c] or board[r][c][0] != color)
    
    if piece_type == 'p':
        d = -1 if color == 'w' else 1
        start = 6 if color == 'w' else 1
        if empty(row + d, col):
            moves.append((row + d, col))
            if row == start and empty(row + 2*d, col):
                moves.append((row + 2*d, col))
        for dc in [-1, 1]:
            if enemy(row + d, col + dc):
                moves.append((row + d, col + dc))
    
    elif piece_type == 'r':
        for dr, dc in [(0,1),(0,-1),(1,0),(-1,0)]:
            for i in range(1, 8):
                nr, nc = row + dr*i, col + dc*i
                if not valid(nr, nc): break
                if empty(nr, nc): moves.append((nr, nc))
                elif enemy(nr, nc): moves.append((nr, nc)); break
                else: break
    
    elif piece_type == 'n':
        for dr, dc in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
            if empty_or_enemy(row + dr, col + dc):
                moves.append((row + dr, col + dc))
    
    elif piece_type == 'b':
        for dr, dc in [(1,1),(1,-1),(-1,1),(-1,-1)]:
            for i in range(1, 8):
                nr, nc = row + dr*i, col + dc*i
                if not valid(nr, nc): break
                if empty(nr, nc): moves.append((nr, nc))
                elif enemy(nr, nc): moves.append((nr, nc)); break
                else: break
    
    elif piece_type == 'q':
        for dr, dc in [(0,1),(0,-1),(1,0),(-1,0),(1,1),(1,-1),(-1,1),(-1,-1)]:
            for i in range(1, 8):
                nr, nc = row + dr*i, col + dc*i
                if not valid(nr, nc): break
                if empty(nr, nc): moves.append((nr, nc))
                elif enemy(nr, nc): moves.append((nr, nc)); break
                else: break
    
    elif piece_type == 'k':
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0: continue
                if empty_or_enemy(row + dr, col + dc):
                    moves.append((row + dr, col + dc))
    
    if check_check:
        legal = []
        for move in moves:
            test = [r[:] for r in board]
            test[move[0]][move[1]] = test[row][col]
            test[row][col] = ''
            if not is_in_check(test, color):
                legal.append(move)
        return legal
    return moves

def find_king(board, color):
    for r in range(8):
        for c in range(8):
            if board[r][c] == color + 'k':
                return (r, c)
    return None

def is_in_check(board, color):
    king = find_king(board, color)
    if not king: return False
    enemy = 'b' if color == 'w' else 'w'
    for r in range(8):
        for c in range(8):
            if board[r][c] and board[r][c][0] == enemy:
                if king in get_valid_moves(board, r, c, False):
                    return True
    return False

def is_checkmate(board, color):
    if not is_in_check(board, color): return False
    for r in range(8):
        for c in range(8):
            if board[r][c] and board[r][c][0] == color:
                if get_valid_moves(board, r, c, True):
                    return False
    return True

def is_stalemate(board, color):
    if is_in_check(board, color): return False
    for r in range(8):
        for c in range(8):
            if board[r][c] and board[r][c][0] == color:
                if get_valid_moves(board, r, c, True):
                    return False
    return True

def pos_to_notation(row, col):
    return f"{chr(97+col)}{8-row}"


def register(client):
    @client.on(events.NewMessage(outgoing=True, pattern=r'^\.chess(?:\s+(.+))?$'))
    async def chess_cmd(event):
        target_input = event.pattern_match.group(1)
        
        white_id = event.sender_id
        white_name = "Sen"
        black_id = None
        black_name = None
        
        # 1. Önce yanıtlanan mesajı kontrol et
        reply = await event.get_reply_message()
        if reply:
            black_id = reply.sender_id
            try:
                u = await client.get_entity(black_id)
                if u.username:
                    black_name = f"@{u.username}"
                elif u.first_name:
                    black_name = u.first_name
                else:
                    black_name = f"Kullanıcı {black_id}"
            except:
                black_name = f"Kullanıcı {black_id}"
        
        # 2. Yanıt yoksa veya ek olarak input varsa, input'u kontrol et
        elif target_input:
            target_input = target_input.strip()
            
            # @ işaretini kaldır
            if target_input.startswith('@'):
                target_input = target_input[1:]
            
            try:
                # Önce ID olarak dene
                if target_input.isdigit():
                    black_id = int(target_input)
                    try:
                        u = await client.get_entity(black_id)
                        if u.username:
                            black_name = f"@{u.username}"
                        elif u.first_name:
                            black_name = u.first_name
                        else:
                            black_name = f"Kullanıcı {black_id}"
                    except:
                        black_name = f"Kullanıcı {black_id}"
                else:
                    # Kullanıcı adı olarak dene
                    u = await client.get_entity(target_input)
                    black_id = u.id
                    if u.username:
                        black_name = f"@{u.username}"
                    elif u.first_name:
                        black_name = u.first_name
                    else:
                        black_name = f"Kullanıcı {black_id}"
            except Exception as e:
                await event.edit(f"❌ Kullanıcı bulunamadı: `{target_input}`\n\nHata: {e}")
                return
        
        # 3. Hiçbiri yoksa yardım göster
        else:
            await event.edit(
                "**♟️ Satranç**\n\n"
                "**Kullanım:**\n"
                "• `.chess @kullanıcı` - Kullanıcı adıyla\n"
                "• `.chess 123456789` - ID ile\n"
                "• Mesajı yanıtla + `.chess`\n\n"
                "**Oyun:**\n"
                "• Taşa tıkla → Seç\n"
                "• `•` işaretine tıkla → Hamle yap\n"
                "• `❌` işaretine tıkla → Taş ye"
            )
            return
        
        # Kontroller
        if not black_id:
            await event.edit("❌ Kullanıcı belirlenemedi!")
            return
        
        if black_id == white_id:
            await event.edit("❌ Kendinle oynayamazsın!")
            return
        
        game_id = hashlib.md5(f"{white_id}{black_id}{time.time()}".encode()).hexdigest()[:8]
        
        GAMES[game_id] = {
            'white_id': white_id, 'black_id': black_id,
            'white_name': white_name, 'black_name': black_name,
            'board': create_board(), 'turn': 'w',
            'selected': None, 'valid_moves': [],
            'last_move': None, 'last_move_data': None,
            'status': 'active', 'moves': []
        }
        
        try:
            import sys
            main = sys.modules.get('__main__')
            if main and hasattr(main, 'bot'):
                bot_me = await main.bot.get_me()
                results = await client.inline_query(bot_me.username, f"chess_{game_id}")
                if results:
                    await results[0].click(event.chat_id)
                    await event.delete()
                else:
                    await event.edit("❌ Inline sorgu başarısız!")
            else:
                await event.edit("❌ Bot bulunamadı!")
        except Exception as e:
            await event.edit(f"❌ Hata: {e}")


def register_bot(bot, client):
    @bot.on(events.InlineQuery(pattern=r'^chess_(.+)$'))
    async def inline_chess(event):
        game_id = event.pattern_match.group(1)
        game = GAMES.get(game_id)
        if not game:
            await event.answer([], cache_time=0)
            return
        
        turn_name = game['white_name'] if game['turn'] == 'w' else game['black_name']
        turn_emoji = "⚪" if game['turn'] == 'w' else "⚫"
        flipped = game['turn'] == 'b'
        
        text = f"♟️ **Satranç**\n\n"
        text += f"⚪ {game['white_name']} vs ⚫ {game['black_name']}\n"
        text += f"Sıra: {turn_emoji} **{turn_name}**"
        
        buttons = create_board_buttons(game_id, game['board'], game['selected'], game['valid_moves'], flipped)
        
        result = event.builder.article(
            title="♟️ Satranç",
            description=f"Sıra: {turn_name}",
            text=text,
            buttons=buttons
        )
        await event.answer([result], cache_time=0)
    
    @bot.on(events.CallbackQuery(pattern=r'^ch_(.+)_(\d)_(\d)$'))
    async def chess_click(event):
        match = event.pattern_match
        game_id = match.group(1).decode() if isinstance(match.group(1), bytes) else match.group(1)
        row, col = int(match.group(2)), int(match.group(3))
        
        game = GAMES.get(game_id)
        if not game or game['status'] != 'active':
            await event.answer("❌ Oyun bulunamadı!", alert=True)
            return
        
        user_id = event.sender_id
        color = game['turn']
        flipped = color == 'b'
        
        if (color == 'w' and user_id != game['white_id']) or (color == 'b' and user_id != game['black_id']):
            await event.answer("⏳ Sıra sende değil!", alert=True)
            return
        
        board = game['board']
        piece = board[row][col]
        selected = game['selected']
        valid_moves = game['valid_moves']
        
        if selected and (row, col) in valid_moves:
            sr, sc = selected
            moved = board[sr][sc]
            captured = board[row][col]
            
            game['last_move_data'] = {
                'from': (sr, sc),
                'to': (row, col),
                'piece': moved,
                'captured': captured
            }
            
            board[row][col] = moved
            board[sr][sc] = ''
            
            if moved[1] == 'p' and row in [0, 7]:
                board[row][col] = moved[0] + 'q'
            
            notation = f"{PIECES.get(moved,'')}{pos_to_notation(sr,sc)}{'x' if captured else '-'}{pos_to_notation(row,col)}"
            game['moves'].append(notation)
            game['last_move'] = notation
            game['turn'] = 'b' if color == 'w' else 'w'
            game['selected'] = None
            game['valid_moves'] = []
            
            new_flipped = game['turn'] == 'b'
            next_color = game['turn']
            status = ""
            
            if is_checkmate(board, next_color):
                winner = game['white_name'] if next_color == 'b' else game['black_name']
                game['status'] = 'checkmate'
                status = f"\n\n🏆 **ŞAH MAT!** {winner} kazandı!"
            elif is_stalemate(board, next_color):
                game['status'] = 'stalemate'
                status = "\n\n🤝 **PAT!** Berabere!"
            elif is_in_check(board, next_color):
                status = "\n\n⚠️ **ŞAH!**"
            
            turn_name = game['white_name'] if game['turn'] == 'w' else game['black_name']
            turn_emoji = "⚪" if game['turn'] == 'w' else "⚫"
            
            text = f"♟️ **Satranç**\n\n"
            text += f"⚪ {game['white_name']} vs ⚫ {game['black_name']}\n"
            if game['status'] == 'active':
                text += f"Sıra: {turn_emoji} **{turn_name}**"
            text += status
            text += f"\n\n📝 {game['last_move']}"
            
            buttons = create_board_buttons(game_id, board, None, [], new_flipped)
            try:
                await event.edit(text, buttons=buttons)
            except: pass
            await event.answer(f"✅ {notation}")
            return
        
        if piece and piece[0] == color:
            moves = get_valid_moves(board, row, col)
            if moves:
                game['selected'] = (row, col)
                game['valid_moves'] = moves
                
                turn_name = game['white_name'] if game['turn'] == 'w' else game['black_name']
                turn_emoji = "⚪" if game['turn'] == 'w' else "⚫"
                
                text = f"♟️ **Satranç**\n\n"
                text += f"⚪ {game['white_name']} vs ⚫ {game['black_name']}\n"
                text += f"Sıra: {turn_emoji} **{turn_name}**\n"
                text += f"Seçili: {PIECES.get(piece,'')} `{pos_to_notation(row,col)}`"
                
                buttons = create_board_buttons(game_id, board, (row, col), moves, flipped)
                try:
                    await event.edit(text, buttons=buttons)
                except: pass
                await event.answer(f"{PIECES.get(piece,'')} seçildi")
            else:
                await event.answer("❌ Bu taş hareket edemiyor!", alert=True)
        elif piece:
            await event.answer("❌ Rakibin taşı!", alert=True)
        else:
            if selected:
                game['selected'] = None
                game['valid_moves'] = []
                
                turn_name = game['white_name'] if game['turn'] == 'w' else game['black_name']
                turn_emoji = "⚪" if game['turn'] == 'w' else "⚫"
                
                text = f"♟️ **Satranç**\n\n"
                text += f"⚪ {game['white_name']} vs ⚫ {game['black_name']}\n"
                text += f"Sıra: {turn_emoji} **{turn_name}**"
                
                buttons = create_board_buttons(game_id, board, None, [], flipped)
                try:
                    await event.edit(text, buttons=buttons)
                except: pass
                await event.answer("İptal")
    
    @bot.on(events.CallbackQuery(pattern=r'^chlast_(.+)$'))
    async def chess_last(event):
        game_id = event.pattern_match.group(1)
        game_id = game_id.decode() if isinstance(game_id, bytes) else game_id
        game = GAMES.get(game_id)
        
        if not game:
            await event.answer("❌ Oyun yok!", alert=True)
            return
        
        if not game['last_move_data']:
            await event.answer("Henüz hamle yok!", alert=True)
            return
        
        lm = game['last_move_data']
        from_pos = lm['from']
        to_pos = lm['to']
        piece = lm['piece']
        captured = lm['captured']
        
        board = game['board']
        flipped = game['turn'] == 'b'
        
        temp_board = [r[:] for r in board]
        temp_board[to_pos[0]][to_pos[1]] = captured or ''
        temp_board[from_pos[0]][from_pos[1]] = piece
        
        turn_name = game['white_name'] if game['turn'] == 'w' else game['black_name']
        turn_emoji = "⚪" if game['turn'] == 'w' else "⚫"
        
        text = f"♟️ **Satranç** ⏮️\n\n"
        text += f"⚪ {game['white_name']} vs ⚫ {game['black_name']}\n"
        text += f"📝 Son hamle: **{game['last_move']}**"
        
        highlight = [from_pos, to_pos]
        buttons = create_board_buttons(game_id, temp_board, None, [], flipped, highlight)
        
        try:
            await event.edit(text, buttons=buttons)
        except: pass
        
        await event.answer(f"⏮️ {game['last_move']}")
        
        await asyncio.sleep(1.5)
        
        text = f"♟️ **Satranç**\n\n"
        text += f"⚪ {game['white_name']} vs ⚫ {game['black_name']}\n"
        if game['status'] == 'active':
            text += f"Sıra: {turn_emoji} **{turn_name}**"
        elif game['status'] == 'checkmate':
            winner = game['white_name'] if game['turn'] == 'b' else game['black_name']
            text += f"\n🏆 **ŞAH MAT!** {winner} kazandı!"
        elif game['status'] == 'stalemate':
            text += "\n🤝 **PAT!** Berabere!"
        
        text += f"\n\n📝 {game['last_move']}"
        
        buttons = create_board_buttons(game_id, board, None, [], flipped)
        try:
            await event.edit(text, buttons=buttons)
        except: pass
    
    @bot.on(events.CallbackQuery(pattern=r'^chres_(.+)$'))
    async def chess_resign(event):
        game_id = event.pattern_match.group(1)
        game_id = game_id.decode() if isinstance(game_id, bytes) else game_id
        game = GAMES.get(game_id)
        
        if not game or game['status'] != 'active':
            await event.answer("❌ Oyun yok!", alert=True)
            return
        
        user_id = event.sender_id
        if user_id not in [game['white_id'], game['black_id']]:
            await event.answer("❌ Bu oyunda değilsin!", alert=True)
            return
        
        game['status'] = 'resigned'
        loser = game['white_name'] if user_id == game['white_id'] else game['black_name']
        winner = game['black_name'] if user_id == game['white_id'] else game['white_name']
        
        text = f"♟️ **Satranç**\n\n"
        text += f"🏳️ {loser} pes etti!\n"
        text += f"🏆 **{winner}** kazandı!"
        
        buttons = [[Button.inline("🔄 Rövanş", f"chnew_{game_id}")]]
        try:
            await event.edit(text, buttons=buttons)
        except: pass
        await event.answer("🏳️ Pes ettin!", alert=True)
    
    @bot.on(events.CallbackQuery(pattern=r'^chnew_(.+)$'))
    async def chess_new(event):
        game_id = event.pattern_match.group(1)
        game_id = game_id.decode() if isinstance(game_id, bytes) else game_id
        game = GAMES.get(game_id)
        
        if not game:
            await event.answer("❌ Oyun yok!", alert=True)
            return
        
        user_id = event.sender_id
        if user_id not in [game['white_id'], game['black_id']]:
            await event.answer("❌ Bu oyunda değilsin!", alert=True)
            return
        
        game['white_id'], game['black_id'] = game['black_id'], game['white_id']
        game['white_name'], game['black_name'] = game['black_name'], game['white_name']
        game['board'] = create_board()
        game['turn'] = 'w'
        game['selected'] = None
        game['valid_moves'] = []
        game['last_move'] = None
        game['last_move_data'] = None
        game['status'] = 'active'
        game['moves'] = []
        
        text = f"♟️ **Satranç** (Rövanş)\n\n"
        text += f"⚪ {game['white_name']} vs ⚫ {game['black_name']}\n"
        text += f"Sıra: ⚪ **{game['white_name']}**"
        
        buttons = create_board_buttons(game_id, game['board'], None, [], False)
        try:
            await event.edit(text, buttons=buttons)
        except: pass
        await event.answer("🔄 Rövanş başladı!", alert=True)