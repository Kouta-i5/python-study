##  機能

- **鮮明度フィルタリング**: ラプラシアンの分散を使用してブレ・ピンボケ画像を除外
- **類似度フィルタリング**: SSIM（構造的類似性）を使用して重複フレームを除去
- **自動リネーム**: 選択されたフレームを連番でリネーム
- **設定可能**: 閾値を調整してフィルタリング精度を制御

## 使用方法

### 1. 基本的な使用方法

```bash
# 仮想環境をアクティベート
source venv/bin/activate

# テスト画像を生成
python generate_test_images.py --output test_images --count 8

# フレーム最適化を実行
python main.py test_images optimized_images
```

### 2. パラメータを指定した使用方法

```bash
# 鮮明度と類似度の閾値を調整
python main.py input_folder output_folder \
    --sharpness 150.0 \
    --similarity 0.80
```

### 3. Windows用exeファイルの作成

```bash
# Windows環境で実行
python build_exe.py

# 生成されたexeファイルを使用
FrameOptimizer.exe input_folder output_folder

# または、バッチファイルをダブルクリック
run_frame_optimizer.bat
```

## 📁 ファイル構成

```
demo/
├── main.py                # メインスクリプト
├── config.py              # 設定ファイル
├── generate_test_images.py # テスト画像生成スクリプト
├── build_exe.py           # Windows用exeビルドスクリプト
├── build.py               # ビルドスクリプト（エイリアス）
├── FrameOptimizer.spec    # PyInstaller設定ファイル
├── README.md              # このファイル
├── venv/                  # 仮想環境
└── requirements.txt       # 依存パッケージ
```

## ⚙️ 設定パラメータ

### 鮮明度フィルタリング
- **閾値**: ラプラシアンの分散の最小値
- **推奨値**: 
  - 一般画像: 100.0
  - 一般画像: 150.0
- **範囲**: 50.0 - 500.0

### 類似度フィルタリング
- **閾値**: SSIMスコアの最大値（類似度が高いと除外）
- **推奨値**: 
  - 一般画像: 0.85
  - 一般画像: 0.80
- **範囲**: 0.70 - 0.95

## 🔧 技術仕様

### 鮮明度評価
- **手法**: ラプラシアンフィルタの分散
- **原理**: エッジの強度を測定し、画像の鮮明度を数値化
- **特徴**: ブレやピンボケを効果的に検出

### 類似度評価
- **手法**: SSIM（Structural Similarity Index）
- **原理**: 人間の視覚特性に基づく画像類似度評価
- **特徴**: 明度、コントラスト、構造の3要素を総合的に評価

### サポート形式
- **入力**: JPEG, JPG, PNG, BMP, TIFF
- **出力**: 元の形式を保持

## 📊 処理フロー

```
1. 動画入力
   ↓
2. 切出し領域、マスク領域済み動画
   ↓
3. フレーム抽出
   ↓
4. 切出しを最適化しますか？
   ├─ No: そのまま、抽出したフレームを出力
   └─ Yes: 最適化切出しを実行
       ├─ 鮮明度フィルタリング
       ├─ 類似度フィルタリング
       └─ 最適化したフレームをリネームして出力
```

## 🧪 テスト

### テスト画像の生成

```bash
# 8個のテスト画像を生成
python generate_test_images.py --output test_images --count 8

# 類似画像も含めて生成
python generate_test_images.py --output test_images --count 8 --similar
```

### テスト実行

```bash
# 基本的なテスト
python main.py test_images optimized_images

# 詳細ログ付きでテスト
python main.py test_images optimized_images --sharpness 120 --similarity 0.82
```

## 📝 出力例

### 入力画像
```
still_image_1_0001.jpeg  (鮮明)
still_image_1_0002.jpeg  (ブレ - 除外)
still_image_1_0003.jpeg  (鮮明)
still_image_1_0004.jpeg  (0003と類似 - 除外)
still_image_1_0005.jpeg  (鮮明)
still_image_1_0006.jpeg  (鮮明)
still_image_1_0007.jpeg  (ブレ - 除外)
still_image_1_0008.jpeg  (鮮明)
```

### 出力画像
```
still_image_1_0001.jpeg  (元: 0001)
still_image_1_0002.jpeg  (元: 0003)
still_image_1_0003.jpeg  (元: 0005)
still_image_1_0004.jpeg  (元: 0006)
still_image_1_0005.jpeg  (元: 0008)
```

## 🚨 注意事項

1. **メモリ使用量**: 大量の画像を処理する場合は十分なメモリを確保
2. **処理時間**: 画像サイズと枚数に比例して処理時間が増加
3. **閾値調整**: 用途に応じて適切な閾値を設定
4. **バックアップ**: 重要な画像は事前にバックアップを取得

## 🔍 トラブルシューティング

### よくある問題

1. **画像が読み込めない**
   - ファイル形式を確認
   - ファイルパスが正しいか確認

2. **処理が遅い**
   - 画像サイズを確認
   - 閾値を調整して処理量を削減

3. **exeファイルが作成できない**
   - PyInstallerがインストールされているか確認
   - 必要なファイルが存在するか確認

## 📚 参考文献

- Schoeffmann, K., et al. (2015). "Video summarization for endoscopic procedures." *Multimedia Tools and Applications*, 74(24), 11347-11379.
- Ishijima, K., et al. (2015). "Automatic frame selection for endoscopic video summarization." *Medical Image Analysis*, 20(1), 89-99.

## 🪟 Windows配布パッケージ

### exeファイルの作成
Windows環境で以下のコマンドを実行してください：

```bash
# 必要なパッケージをインストール
pip install -r requirements.txt

# exeファイルをビルド（どちらでも可）
python build_exe.py
# または
python build.py
```

### 生成されるファイル
- `dist/FrameOptimizer.exe` - メイン実行ファイル
- `run_frame_optimizer.bat` - 実行用バッチファイル

### 配布方法
1. `FrameOptimizer.exe` と `run_frame_optimizer.bat` を配布
2. ユーザーはPython環境不要で実行可能
3. ダブルクリックで簡単実行

## 🔧 C#での統合

### FrameOptimizerWrapperクラス
C#の一般版DEMOでFrameOptimizer.exeを実行するためのラッパークラスを提供しています。

#### 基本的な使用方法
```csharp
using DEMO.Endoscope;

// ラッパークラスを初期化
var optimizer = new FrameOptimizerWrapper(@"C:\Tools\FrameOptimizer\FrameOptimizer.exe");

// 非同期でフレーム最適化を実行
var result = await optimizer.OptimizeFramesAsync(
    inputDir: @"C:\InputImages",
    outputDir: @"C:\OutputImages",
    sharpnessThreshold: 150.0,
    similarityThreshold: 0.80
);

if (result.Success)
{
    Console.WriteLine($"最適化完了！出力ファイル数: {result.OutputFileCount}");
}
```

#### 特徴
- **非同期実行**: `async/await`でUIをブロックしない
- **進捗表示**: `IProgress<string>`でリアルタイム進捗を取得
- **エラーハンドリング**: 詳細なエラー情報と例外処理
- **設定可能**: 鮮明度・類似度の閾値を調整可能
- **バッチファイル対応**: バッチファイル経由での実行も可能

#### ファイル構成
- `FrameOptimizerWrapper.cs` - メインのラッパークラス
- `FrameOptimizerUsageExample.cs` - 使用例とサンプルコード

## 📞 サポート

問題や質問がある場合は、以下の情報を含めてお問い合わせください：

- エラーメッセージ
- 使用環境（OS、Python バージョン）
- 入力画像の詳細
- 実行したコマンド
