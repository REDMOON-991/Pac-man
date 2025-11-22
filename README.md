# Pygame Pac-Man Project

這是一個使用 Python 與 Pygame 函式庫開發的經典《小精靈》(Pac-Man) 復刻版遊戲。 專案完整實作了地圖路徑、碰撞偵測、傳送通道，以及經典的四色鬼魂 AI（包含追逐、散開與受驚模式）。

## ✨ 遊戲特色 (Features)

經典遊戲機制：包含吃豆子、吃大力丸 (Power Pellets)、鬼魂重生與分數計算。

四種鬼魂 AI 個性：忠實還原原作中 Blinky, Pinky, Inky, Clyde 四隻鬼魂不同的追蹤邏輯。

AI 模式切換：鬼魂會在「追逐 (Chase)」與「散開 (Scatter)」模式間定時切換，增加遊戲節奏感。

路徑搜尋：鬼魂具備基於網格 (Grid-based) 的路徑判斷能力，能識別牆壁與單行道。

除錯日誌系統：遊戲視窗底部設有即時 Log 面板，顯示當前遊戲狀態、鬼魂模式切換與觸發事件。

## 🛠️ 安裝與執行 (Installation)

確保你的電腦已安裝 Python 3.x。

安裝必要的依賴套件：

    pip install -r requirements.txt

進入 code 資料夾並執行遊戲：

    python code/main.py

## 🎮 操作說明 (Controls)

開始遊戲：在開始畫面按下 方向鍵。

移動：使用鍵盤 ↑ ↓ ← → 控制小精靈移動。

勝利條件：吃光地圖上所有的豆子。

失敗條件：被鬼魂抓到。

## 👻 鬼魂 AI 機制 (Ghost AI)

本專案中的鬼魂並非單純隨機移動，而是根據目標點 (Target Tile) 計算最短路徑。

### 1.行為模式

散開 (Scatter)：鬼魂會放棄追捕玩家，轉而繞行地圖四個角落的固定巡邏點。

追逐 (Chase)：根據各自的個性鎖定玩家位置進行夾擊。

受驚 (Frightened)：玩家吃到大力丸後觸發，鬼魂變為藍色並隨機逃竄，此時玩家可以吃掉鬼魂。

### 2.鬼魂個性 (Personalities)

🔴 Blinky (紅)：直球對決，直接將目標鎖定在玩家當前的格子。

🩷 Pinky (粉)：預判埋伏，目標設在玩家「前方 4 格」的位置。

🩵 Inky (藍)：戰術夾擊，以 Blinky 的位置和玩家前方 2 格為向量參考，計算出對稱的夾擊點。

🧡 Clyde (橘)：隨性遊走，當距離玩家大於 8 格時會追逐，但距離過近時會反而跑回自己的散開角落。

## 📂 檔案結構 (File Structure)

    Pac-man/
    ├── code/
    │   ├── main.py       # 遊戲主程式：負責初始化、遊戲迴圈與畫面繪製
    │   ├── settings.py   # 設定檔：地圖佈局、顏色、常數與參數調整
    │   ├── player.py     # 玩家類別：處理小精靈的移動與輸入
    │   └── ghost.py      # 鬼魂類別：處理所有 AI 邏輯與狀態機
    ├── requirements.txt  # 依賴列表
    └── README.md         # 專案說明文件

---

Enjoy the game!
