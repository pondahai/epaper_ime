# E-Paper Chinese IME - 基於 Raspberry Pi 的電子紙中文輸入法

## 專案概述 (Project Overview)

本專案是一個在 **Raspberry Pi Zero W** 上，使用 **Python** 語言和 **Waveshare 2.13 吋觸控電子紙** 實現的、功能完備的獨立中文輸入系統。它旨在探索和解決在刷新速度極慢、僅有黑白兩色的電子紙螢幕上，如何設計和實現一套可用的中文輸入法。

整個系統從底層的資料處理到上層的使用者互動都經過精心設計，以最大化電子紙的優點（清晰、省電）並規避其缺點（刷新慢）。

 <!-- 強烈建議您拍一張實際運行的照片並替換此連結 -->
![螢幕擷取畫面 2025-06-22 155535](https://github.com/user-attachments/assets/28c29812-2dc9-4cb1-af2f-9757e61cf4cf)

### 主要功能
-   **觸控虛擬鍵盤**: 直接在螢幕上點擊輸入注音、聲調和標點符號。
-   **多頁鍵盤佈局**: 將「聲母」、「韻母」、「聲調及符號」劃分為三個獨立頁面，佈局清晰，按鍵大小合理。
-   **注音輸入法引擎**: 支援完整的注音輸入，並能從預處理的碼表檔案中即時查詢候選字。
-   **候選字翻頁**: 當候選字超過一頁時，可透過觸控按鈕進行翻頁。
-   **固定槽位顯示**: 候選字顯示在固定寬度、固定位置的槽位中，佈局穩定、點擊準確。
-   **智慧刷新策略**: 精巧地混合使用電子紙的**全局刷新**和**局部刷新**模式，在顯示清晰度和響應速度之間取得最佳平衡。
-   **完整的編輯體驗**: 包含獨立的編輯區，支援自動換行和刪除功能。

## 部署與運行

本指南假設您已經在 PC 端使用本專案提供的 `tools/` 工具腳本，生成了所有必需的資源檔案。

### 必備條件

#### 硬體
-   Raspberry Pi Zero W (或任何帶有 40-Pin GPIO 排針的樹莓派型號)。
-   Waveshare 2.13inch Touch e-Paper HAT。
-   已燒錄 Raspberry Pi OS 並配置好網路的 Micro SD 卡。

#### 軟體/資料
-   **預處理的資源檔案**:
    -   `output_data/BoutiqueBitmap9x9_1.92.ttf_10.map`
    -   `output_data/BoutiqueBitmap9x9_1.92.ttf_10.font`
    -   `output_data/zhuyin.idx`
    -   `output_data/zhuyin.dat`
-   **驅動程式庫**: Waveshare 官方提供的 `lib/` 資料夾。
-   **主應用程式**: `epaper_ime_app.py`。

### 步驟 1: 設置 Raspberry Pi 環境

1.  在 Raspberry Pi 的終端機中，啟用 SPI 和 I2C 介面。這是電子紙顯示和觸控功能所必需的。
    ```bash
    sudo raspi-config
    ```
    在選單中，導航至 `Interface Options`，分別啟用 `SPI` 和 `I2C`。

2.  安裝應用程式所需的 Python 函式庫。
    ```bash
    sudo apt-get update
    sudo apt-get install -y python3-pip python3-pil
    sudo pip3 install RPi.GPIO spidev
    ```

### 步驟 2: 部署專案檔案

1.  在您的 Raspberry Pi 上創建一個專案目錄，例如 `epaper-ime`。
    ```bash
    mkdir ~/epaper-ime
    cd ~/epaper-ime
    ```
2.  將以下檔案和資料夾從您的 PC 傳輸到這個目錄中，最終形成如下結構：
    ```
    /home/pi/epaper-ime/
    ├── epaper_ime_app.py        # 主應用程式
    |
    ├── lib/                     # 完整的 Waveshare 驅動庫
    │   ├── TP_lib/
    |
    └── output_data/             # 包含所有 .map, .font, .idx, .dat 檔案
    ```
    *(您可以使用 `scp`、FTP 工具或隨身碟來傳輸檔案。)*

### 步驟 3: 運行輸入法

1.  進入專案目錄：
    ```bash
    cd ~/epaper-ime
    ```
2.  執行主應用程式：
    ```bash
    python3 epaper_ime_app.py
    ```
3.  電子紙螢幕將會進行一次全局刷新，並顯示出輸入法的主介面。

### 步驟 4: 操作指南

-   **輸入**: 點擊螢幕下方的虛擬鍵盤來輸入注音符號。
-   **切換鍵盤**: 點擊鍵盤右側的 `Pg` 鍵，可以在「聲母」、「韻母」、「聲調/符號」三頁鍵盤之間循環切換。
-   **選字**: 當中間的狀態欄出現候選字時，直接點擊您想要的那個字，它就會被輸入到上方的編輯區。
-   **候選字翻頁**: 如果候選字多於一頁，狀態欄右側會出現 `<` 和 `>` 按鈕，點擊它們可以進行翻頁。
-   **輸入標點**: 在第三頁鍵盤上，直接點擊標點符號（如 `，` `。`），即可將其直接輸入到編輯區。
-   **刪除**: 點擊鍵盤右側的 `Del` 鍵。它會優先刪除輸入區的注音；如果輸入區為空，則會刪除編輯區的最後一個字元。
-   **退出**: 回到運行程式的終端機，按下 `Ctrl + C` 即可安全退出應用程式。

## 鳴謝與資料來源 (Acknowledgements and Data Sources)

本專案的成功離不開以下開源專案和社群提供的寶貴資源，特此感謝。

-   **硬體驅動與範例**:
    -   **Waveshare 2.13inch Touch e-Paper HAT Wiki & Manual**: 提供了本專案所使用的電子紙硬體的底層 Python 驅動程式庫和初始化範例。
    -   [https://www.waveshare.com/wiki/2.13inch_Touch_e-Paper_HAT_Manual](https://www.waveshare.com/wiki/2.13inch_Touch_e-Paper_HAT_Manual)

-   **中文字型**:
    -   **BoutiqueBitmap9x9 (精品點陣體9x9)**: 本專案預設使用的點陣字型。其清晰、優雅的設計在低解析度螢幕上表現出色。由 justfont / aninjusta 團隊創作。
    -   [https://github.com/scott0107000/BoutiqueBitmap9x9](https://github.com/scott0107000/BoutiqueBitmap9x9)

-   **注音輸入法碼表**:
    -   **McBopomofo (小麥注音輸入法)**: 本專案所使用的注音碼表 (`BPMFBase.txt`, `BPMFPunctuations.txt`) 源於此專案。其高品質、格式清晰的資料是實現注音引擎的關鍵。
    -   [https://github.com/openvanilla/McBopomofo](https://github.com/openvanilla/McBopomofo)

## 技術亮點回顧
-   **精確的觸控模型**: 透過分析觸控晶片的 `TouchCount` 回報，結合軟體狀態鎖，實現了精準、無彈跳的單次點擊事件偵測。
-   **智慧混合刷新**: 應用程式能夠根據操作的類型（例如輸入、選字、翻頁），智能地選擇使用快速的**局部刷新**或清晰的**全局刷新**，在反應速度和顯示質量之間取得了極佳的平衡。
-   **動態與固定佈局的結合**: 鍵盤的生成採用了動態計算，便於維護；而候選字的顯示和點擊則採用了固定槽位模型，保證了 UI 的穩定性和操作的準確性。

## 未來可擴展方向
-   **支援倉頡輸入法**: 透過編寫新的 `ime_converter_cangjie.py` 並在主程式中加入切換邏輯。
-   **英文/數字鍵盤**: 增加一個英文/數字鍵盤頁面。
-   **介面美化**: 設計更美觀的圖示和按鈕樣式。
-   **移植到微控制器 (RP2040)**: 本專案的架構設計完全是為了最終能移植到像 Raspberry Pi Pico 這樣的微控制器上。屆時需要將 Python 邏輯用 C/C++ 重寫，並將 JSON 格式的索引檔 (`.map`, `.idx`) 轉換為更節省記憶體的純二進位格式。
