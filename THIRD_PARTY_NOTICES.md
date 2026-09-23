# Third-Party Notices

本專案收錄或衍生自下列第三方資源。散布本專案時,以下聲明必須隨著一起散布。

---

## 1. 注音輸入法碼表 — McBopomofo(小麥注音輸入法)

`output_data/zhuyin.idx` 與 `output_data/zhuyin.dat` 是由 McBopomofo 的
碼表檔轉換而成的衍生資料。

| | |
|---|---|
| 上游 | https://github.com/openvanilla/McBopomofo |
| 授權 | MIT License |
| 著作權 | Copyright (c) 2011-2026 Mengjuei Hsieh et al. |

### 實際使用的檔案

| 檔案 | 內容 | 有無額外上游出處 |
|---|---|---|
| `Source/Data/BPMFBase.txt` | 單字注音對應 | 無 —— 適用 McBopomofo 的 MIT |
| `Source/Data/BPMFPunctuations.txt` | 標點符號對應 | 無 —— 適用 McBopomofo 的 MIT |

### 明確未使用的檔案

`Source/Data/BPMFMappings.txt`(2–6 字的多字詞庫)**未被使用**。

依 McBopomofo 的 `Source/Data/README.md`,該檔案
*"Originally simplified from tsi.src of libtabe (BSD Licensed) with modifications"*
——它帶有 libtabe 的 BSD 血統。本專案是單字候選而非詞庫,不涉及 libtabe。

### MIT License 全文

```
MIT License

Copyright (c) 2011-2026 Mengjuei Hsieh et al.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 2. 中文字型 — BoutiqueBitmap9x9(精品點陣體 9x9)

`output_data/BoutiqueBitmap9x9_1.92.ttf_10.font` 與 `..._10.map`
是該字型光柵化後的點陣資料。

| | |
|---|---|
| 上游 | https://github.com/scott0107000/BoutiqueBitmap9x9 |
| 授權 | SIL Open Font License 1.1 |
| 作者 | justfont / aninjusta |

依 SIL OFL 1.1,散布衍生資料時須隨附授權文字,且不得以原字型的
**保留字型名稱**對外呈現為字型名。

---

## 3. 電子紙驅動 — Waveshare

`lib/TP_lib/` 為 Waveshare 官方提供的 2.13inch Touch e-Paper HAT
Python 驅動程式庫,未經修改收錄。

| | |
|---|---|
| 來源 | https://www.waveshare.com/wiki/2.13inch_Touch_e-Paper_HAT_Manual |
| 授權 | 依 Waveshare 隨附範例碼的條款,見該目錄內檔案的檔頭聲明 |
