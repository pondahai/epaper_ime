#!/usr/bin/python
# -*- coding:utf-8 -*-
import sys
import os
import time
import json
import logging
import threading
from PIL import Image, ImageDraw

# --- 設定路徑、導入驅動、配置 (不變) ---
libdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)
from TP_lib import gt1151
from TP_lib import epd2in13_V4

logging.basicConfig(level=logging.INFO)
FONT_MAP_PATH = "output_data/BoutiqueBitmap9x9_1.92.ttf_10.map"
FONT_DATA_PATH = "output_data/BoutiqueBitmap9x9_1.92.ttf_10.font"
IME_IDX_PATH = "output_data/zhuyin.idx"
IME_DAT_PATH = "output_data/zhuyin.dat"
SCREEN_WIDTH = 250
SCREEN_HEIGHT = 122

# --- 核心類別：FontRenderer, ImeEngine (不變，為節省篇幅省略) ---
class FontRenderer:
    def __init__(self, map_path, font_path):
        self.char_map = {}; self.font_file = None; self.metadata = {}
        if not self._load_map(map_path) or not self._open_font_data(font_path): raise RuntimeError("字型渲染器初始化失敗！")
        logging.info("字型渲染器初始化成功！")
    def _load_map(self, map_path):
        try:
            with open(map_path, 'r', encoding='utf-8') as f:
                map_data = json.load(f); self.metadata = map_data.get('metadata', {}); self.char_map = map_data.get('characters', {}); logging.info(f"成功載入 {len(self.char_map)} 個字元的查找表。"); return True
        except Exception as e: logging.error(f"錯誤: 無法載入或解析 .map 檔案: {e}"); return False
    def _open_font_data(self, font_path):
        try:
            self.font_file = open(font_path, 'rb'); return True
        except Exception as e: logging.error(f"錯誤: 找不到 .font 檔案: {e}"); return False
    def measure_string(self, text):
        width = 0
        for char in text:
            unicode_str = str(ord(char))
            if unicode_str in self.char_map:
                _, char_width, _ = self.char_map[unicode_str]; width += char_width + 1
            else: width += self.metadata.get('font_size', 10) + 1
        return width
    def draw_string(self, draw, text, x, y, color=0):
        current_x = x
        for char in text:
            unicode_str = str(ord(char))
            if unicode_str not in self.char_map:
                draw.rectangle((current_x, y, current_x + 10, y + 10), outline=color); current_x += 12; continue
            offset, width, height = self.char_map[unicode_str]
            self.font_file.seek(offset); pixel_data = self.font_file.read(width * height)
            for row in range(height):
                for col in range(width):
                    if pixel_data[row * width + col] > 128: draw.point((current_x + col, y + row), fill=color)
            current_x += width + 1
        return current_x
    def close(self):
        if self.font_file: self.font_file.close()

class ImeEngine:
    def __init__(self, idx_path, dat_path):
        self.idx_data = {}; self.dat_file = None
        if not self._load_idx(idx_path) or not self._open_dat(dat_path): raise RuntimeError("輸入法引擎初始化失敗！")
        logging.info("輸入法引擎初始化成功！")
    def _load_idx(self, idx_path):
        try:
            with open(idx_path, 'r', encoding='utf-8') as f:
                self.idx_data = json.load(f); logging.info(f"成功載入 {len(self.idx_data)} 條輸入法索引。"); return True
        except Exception as e: logging.error(f"錯誤: 無法載入或解析 .idx 檔案: {e}"); return False
    def _open_dat(self, dat_path):
        try:
            self.dat_file = open(dat_path, 'rb'); return True
        except Exception as e: logging.error(f"錯誤: 找不到 .dat 檔案: {e}"); return False
    def query(self, input_code):
        if input_code not in self.idx_data: return ""
        offset, length = self.idx_data[input_code]
        self.dat_file.seek(offset)
        return self.dat_file.read(length).decode('utf-8')
    def close(self):
        if self.dat_file: self.dat_file.close()

# --- 主應用程式類別 (實驗性刷新版) ---
class App:
    def __init__(self):
        # 初始化硬體、軟體元件
        self.epd = epd2in13_V4.EPD(); self.gt = gt1151.GT1151()
        self.epd.init(self.epd.FULL_UPDATE); self.gt.GT_Init(); self.epd.Clear(0xFF)
        self.renderer = FontRenderer(FONT_MAP_PATH, FONT_DATA_PATH)
        self.ime = ImeEngine(IME_IDX_PATH, IME_DAT_PATH)
        self.image = Image.new('1', (SCREEN_WIDTH, SCREEN_HEIGHT), 255); self.draw = ImageDraw.Draw(self.image)
        
        # 觸控執行緒
        self.touch_dev = gt1151.GT_Development()
        self.touch_thread_running = True
        self.touch_thread = threading.Thread(target=self._touch_irq_handler); self.touch_thread.setDaemon(True); self.touch_thread.start()
        
        # 狀態管理
        self.editor_content = ""
        self.input_buffer = ""
        self.candidate_string = ""
        self.candidate_page = 0
        self.CANDIDATES_PER_PAGE = 6
        self.CANDIDATE_SLOT_WIDTH = 23 # <--- 新增：每個候選字槽的固定寬度
        self.needs_refresh = True
        self.keyboard_page = 0
        self.direct_input_symbols = set("，。？！《》")
        
        # --- 刷新管理 ---
        self.clear_rect_on_next_refresh = None # 觸發預清理刷新的標誌

        # UI 元素定義
        self.ui_elements = {}; self.keyboard_layout = []
        self.setup_ui()
        
    def setup_ui(self):
        # (不變)
        self.ui_elements['editor'] = {'rect': (0, 0, SCREEN_WIDTH, 45)}
        self.ui_elements['status'] = {'rect': (0, 46, SCREEN_WIDTH, 70)}
        self.ui_elements['keyboard'] = {'rect': (0, 71, SCREEN_WIDTH, SCREEN_HEIGHT)}
        status_rect = self.ui_elements['status']['rect']
        self.ui_elements['cand_prev_btn'] = {'rect': (status_rect[2] - 50, status_rect[1], status_rect[2] - 25, status_rect[3]), 'char': '<'}
        self.ui_elements['cand_next_btn'] = {'rect': (status_rect[2] - 25, status_rect[1], status_rect[2], status_rect[3]), 'char': '>'}
        keyboards_def = [[("ㄅㄆㄇㄈㄉㄊㄋㄌㄍㄎㄏ", 17), ("ㄐㄑㄒㄓㄔㄕㄖㄗㄘㄙ", 17)], [("ㄚㄛㄜㄝㄞㄟㄠㄡ", 24), ("ㄢㄣㄤㄥㄦㄧㄨㄩ", 24)], [("ˊˇˋ˙，。", 28), ("？！《》", 28)]]
        self.keyboard_layout = []
        key_height = 24
        for page_def in keyboards_def:
            page_layout = []; y_offset = self.ui_elements['keyboard']['rect'][1] + 2
            for row_tuple in page_def:
                x_offset = 5; row_chars, key_width = row_tuple
                for char in row_chars:
                    page_layout.append({'char': char, 'rect': (x_offset, y_offset, x_offset + key_width, y_offset + key_height)}); x_offset += key_width + 2
                y_offset += key_height + 2
            self.keyboard_layout.append(page_layout)
        kb_rect = self.ui_elements['keyboard']['rect']
        self.common_keys = [{'char': 'Pg', 'rect': (218, kb_rect[1] + 1, 248, kb_rect[1] + 25), 'action': 'switch_keyboard'}, {'char': 'Del', 'rect': (218, kb_rect[1] + 27, 248, kb_rect[3] - 1), 'action': 'delete'}]

    def _touch_irq_handler(self):
        while self.touch_thread_running:
            if self.gt.digital_read(self.gt.INT) == 0: self.touch_dev.Touch = 1
            else: self.touch_dev.Touch = 0
            time.sleep(0.01)
        
    def process_touch(self, x, y):
        # 檢查候選字翻頁
        if len(self.candidate_string) > self.CANDIDATES_PER_PAGE:
            prev_btn = self.ui_elements['cand_prev_btn']; next_btn = self.ui_elements['cand_next_btn']
            if prev_btn['rect'][0] <= x <= prev_btn['rect'][2] and prev_btn['rect'][1] <= y <= prev_btn['rect'][3]:
                if self.candidate_page > 0:
                    self.candidate_page -= 1; self.needs_refresh = True; self.clear_rect_on_next_refresh = self.ui_elements['status']['rect']
                return
            if next_btn['rect'][0] <= x <= next_btn['rect'][2] and next_btn['rect'][1] <= y <= next_btn['rect'][3]:
                if self.candidate_page < (len(self.candidate_string) - 1) // self.CANDIDATES_PER_PAGE:
                    self.candidate_page += 1; self.needs_refresh = True; self.clear_rect_on_next_refresh = self.ui_elements['status']['rect']
                return

        # 檢查選字
        status_rect = self.ui_elements['status']['rect']
        if status_rect[0] <= x <= status_rect[2] and status_rect[1] <= y <= status_rect[3]:
            if self.candidate_string:
                # 1. 計算候選字顯示的起始 X 座標
                cand_start_x = 5 + self.renderer.measure_string(self.input_buffer + " | ")
                
                # 2. 只有當點擊發生在候選字區域時才處理
                if x > cand_start_x:
                    # 3. 用固定的槽位寬度來計算點中了第幾個槽
                    choice_on_page = (x - cand_start_x) // self.CANDIDATE_SLOT_WIDTH
                    
                    actual_choice_index = self.candidate_page * self.CANDIDATES_PER_PAGE + choice_on_page
                    
                    # 4. 檢查計算出的索引是否有效
                    if actual_choice_index < len(self.candidate_string):
                        logging.info(f"固定槽位選中候選字: '{self.candidate_string[actual_choice_index]}'")
                        
                        # --- 後續的選字成功邏輯不變 ---
                        self.editor_content += self.candidate_string[actual_choice_index]
                        self.input_buffer = ""; self.candidate_string = ""; self.candidate_page = 0
                        self.needs_refresh = True
                        self.clear_rect_on_next_refresh = (0,0,SCREEN_WIDTH,SCREEN_HEIGHT)
                return

        # 檢查鍵盤
        for key in self.common_keys:
            if key['rect'][0] <= x <= key['rect'][2] and key['rect'][1] <= y <= key['rect'][3]:
                self.handle_key_action(key['action']); return
        for key in self.keyboard_layout[self.keyboard_page]:
            if key['rect'][0] <= x <= key['rect'][2] and key['rect'][1] <= y <= key['rect'][3]:
                self.handle_key_action(key['char']); return
            
    def handle_key_action(self, action):
        logging.info(f"執行動作: {action}")
        self.needs_refresh = True
        status_rect = self.ui_elements['status']['rect']
        
        if action in self.direct_input_symbols:
            self.editor_content += action; self.input_buffer = ""; self.candidate_string = ""
            self.clear_rect_on_next_refresh = self.ui_elements['editor']['rect']
            return
        if action == 'switch_keyboard':
            self.keyboard_page = (self.keyboard_page + 1) % len(self.keyboard_layout)
            self.clear_rect_on_next_refresh = self.ui_elements['keyboard']['rect']
        elif action == 'delete':
            if self.input_buffer:
                self.input_buffer = self.input_buffer[:-1]
                if self.input_buffer: self.trigger_query()
                else: self.candidate_string = ""; self.clear_rect_on_next_refresh = status_rect
            elif self.editor_content:
                self.editor_content = self.editor_content[:-1]; self.clear_rect_on_next_refresh = self.ui_elements['editor']['rect']
        else: 
            self.input_buffer += action
            self.trigger_query()

    def trigger_query(self):
        self.candidate_page = 0
        query_code = self.input_buffer.replace("ˊ", "2").replace("ˇ", "3").replace("ˋ", "4").replace("˙", "5")
        if not any(c.isdigit() for c in query_code) and query_code: query_code += "1"
        new_candidates = self.ime.query(query_code)
        if new_candidates:
            self.candidate_string = new_candidates
            self.clear_rect_on_next_refresh = self.ui_elements['status']['rect']
        else:
            self.candidate_string = ""

    def draw_ui(self):
        # 清空畫布
        self.draw.rectangle((0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), fill=255)
        
        # 繪製編輯區 (保持不變)
        editor_rect = self.ui_elements['editor']['rect']
        self.draw.rectangle(editor_rect, outline=0)
        line_y = editor_rect[1] + 5; current_line = ""; font_height = 12
        for char in self.editor_content:
            test_line = current_line + char
            if self.renderer.measure_string(test_line) > editor_rect[2] - 10:
                self.renderer.draw_string(self.draw, current_line, 5, line_y)
                line_y += font_height
                current_line = char
            else:
                current_line = test_line
            if line_y > editor_rect[3] - font_height: break
        self.renderer.draw_string(self.draw, current_line, 5, line_y)
        
        # --- 開始修改：繪製狀態/候選字區 ---
        status_rect = self.ui_elements['status']['rect']
        self.draw.rectangle(status_rect, outline=0)
        status_y = status_rect[1] + 5
        
        # 1. 繪製輸入碼，並得到候選字的起始 X 座標
        cand_start_x = 5
        if self.input_buffer:
            cand_start_x = self.renderer.draw_string(self.draw, self.input_buffer, 5, status_y)
        
        # 2. 如果有候選字，繪製分隔符和候選字
        if self.candidate_string:
            # 繪製分隔符
            cand_start_x = self.renderer.draw_string(self.draw, " | ", cand_start_x, status_y)
            
            # 獲取當前頁的候選字
            start_index = self.candidate_page * self.CANDIDATES_PER_PAGE
            end_index = start_index + self.CANDIDATES_PER_PAGE
            page_candidates = self.candidate_string[start_index:end_index]
            
            # 遍歷固定數量的槽位 (CANDIDATES_PER_PAGE)，並在每個槽位的中心繪製字元
            for i in range(self.CANDIDATES_PER_PAGE):
                # 只有當這一頁還有候選字時才繪製
                if i < len(page_candidates):
                    char = page_candidates[i]
                    
                    # 計算第 i 個槽位的起始 X 座標
                    slot_x_start = cand_start_x + i * self.CANDIDATE_SLOT_WIDTH
                    
                    # 為了讓字元在槽位中大致居中，計算偏移
                    char_width = self.renderer.measure_string(char)
                    char_x_offset = (self.CANDIDATE_SLOT_WIDTH - char_width) / 2
                    
                    # 繪製字元
                    self.renderer.draw_string(self.draw, char, slot_x_start + char_x_offset, status_y)
        
        # --- 結束修改 ---

        # 繪製候選字翻頁按鈕和頁碼 (保持不變)
        if len(self.candidate_string) > self.CANDIDATES_PER_PAGE:
            prev_btn = self.ui_elements['cand_prev_btn']; next_btn = self.ui_elements['cand_next_btn']
            self.draw.rectangle(prev_btn['rect'], outline=0); self.renderer.draw_string(self.draw, prev_btn['char'], prev_btn['rect'][0]+8, prev_btn['rect'][1]+5)
            self.draw.rectangle(next_btn['rect'], outline=0); self.renderer.draw_string(self.draw, next_btn['char'], next_btn['rect'][0]+8, next_btn['rect'][1]+5)
            total_pages = (len(self.candidate_string) - 1) // self.CANDIDATES_PER_PAGE + 1
            self.renderer.draw_string(self.draw, f"{self.candidate_page + 1}/{total_pages}", status_rect[2] - 85, status_rect[1] + 5)
            
        # 繪製鍵盤 (保持不變)
        for key in self.common_keys:
            self.draw.rectangle(key['rect'], outline=0, fill=255); self.renderer.draw_string(self.draw, key['char'], key['rect'][0] + 5, key['rect'][1] + 8)
        for key in self.keyboard_layout[self.keyboard_page]:
            self.draw.rectangle(key['rect'], outline=0, fill=255); self.renderer.draw_string(self.draw, key['char'], key['rect'][0] + 5, key['rect'][1] + 8)

    def refresh_display(self, clear_area_rect=None, clear_cycles=2):
        # 繪製最新的UI到畫布上
        self.draw_ui()
        
        # 執行預清理
        if clear_area_rect:
            logging.info(f"執行 {clear_cycles} 次局部清理，區域: {clear_area_rect}")
            temp_image = self.image.copy() # 複製一份當前畫布
            temp_draw = ImageDraw.Draw(temp_image)
            temp_draw.rectangle(clear_area_rect, fill=255) # 在副本上塗白
            rotated_image = temp_image.rotate(90, expand=True)
            for i in range(clear_cycles):
                self.epd.displayPartial_Wait(self.epd.getbuffer(rotated_image))
                logging.info(f"局部清理第 {i+1} 次完成。")
        
        # 執行最終的局部繪製
        rotated_image = self.image.rotate(90, expand=True)
        logging.info("執行最終的局部繪製...")
        self.epd.displayPartial_Wait(self.epd.getbuffer(rotated_image))

    def run(self):
        logging.info("應用程式開始運行..."); was_pressed_in_last_frame = False
        self.epd.init(self.epd.FULL_UPDATE); self.draw_ui(); self.epd.display(self.epd.getbuffer(self.image.rotate(90, expand=True))); self.epd.init(self.epd.PART_UPDATE) # 首次全局刷新
        while True:
            self.gt.GT_Scan(self.touch_dev, self.touch_dev)
            is_currently_pressed = (self.touch_dev.TouchCount > 0)
            if is_currently_pressed and not was_pressed_in_last_frame:
                touch_x, touch_y = self.touch_dev.X[0], self.touch_dev.Y[0]
                canvas_x = 250 - touch_y; canvas_y = touch_x
                logging.info(f"--- 觸控按下事件 ---: (canvas_x={canvas_x}, canvas_y={canvas_y})")
                self.process_touch(canvas_x, canvas_y)
            was_pressed_in_last_frame = is_currently_pressed
            
            if self.needs_refresh:
                logging.info("狀態更新，觸發刷新流程...");
                clear_rect = self.clear_rect_on_next_refresh
                self.clear_rect_on_next_refresh = None # 使用後立即重置
                self.refresh_display(clear_area_rect=clear_rect, clear_cycles=1)
                self.needs_refresh = False
            
            time.sleep(0.05)
            
    def exit(self):
        logging.info("程式退出..."); self.touch_thread_running = False; self.touch_thread.join()
        self.renderer.close(); self.ime.close(); self.epd.sleep(); time.sleep(1); self.epd.Dev_exit()

if __name__ == '__main__':
    app = None
    try:
        app = App()
        app.run()
    except Exception as e:
        logging.error(f"發生未預期錯誤: {e}", exc_info=True)
        if app: app.exit()
    except KeyboardInterrupt:
        logging.info("Ctrl+C 中斷");
        if app: app.exit()