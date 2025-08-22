# MemoryBasedFrameOptimizer 入出力仕様書

## 📥 入力仕様

### メソッド呼び出し
```csharp
// バイト配列から最適化
var result = await optimizer.OptimizeFramesFromMemoryAsync(
    imageDataList,  // List<byte[]>
    outputDir,
    sharpnessThreshold: 150.0,
    similarityThreshold: 0.80
);

// 画像オブジェクトから最適化
var result = await optimizer.OptimizeFramesFromImagesAsync(
    images,  // List<System.Drawing.Image>
    outputDir,
    sharpnessThreshold: 150.0,
    similarityThreshold: 0.80
);
```

#### 入力パラメータ
| パラメータ | 型 | 必須 | 説明 | 制限 |
|------------|-----|------|------|------|
| `imageDataList` | `List<byte[]>` | ✅ | 画像データのバイト配列リスト | 最大1000枚、各50MB以下 |
| `images` | `List<T>` | ✅ | 画像オブジェクトのリスト | 最大1000枚 |
| `outputDir` | string | ✅ | 出力ディレクトリのパス | 書き込み権限が必要 |
| `sharpnessThreshold` | double | ❌ | 鮮明度閾値 | 0.0 - 1000.0、デフォルト: 100.0 |
| `similarityThreshold` | double | ❌ | 類似度閾値 | 0.0 - 1.0、デフォルト: 0.85 |

### 入力データの要件

#### バイト配列形式
- **形式**: JPEG、PNG、BMP、TIFF等の画像データ
- **サイズ制限**: 各画像50MB以下
- **枚数制限**: 最大1000枚
- **品質**: 元画像の品質を保持

#### 画像オブジェクト形式
- **System.Drawing.Image**: Windows Forms、WPF等
- **System.Windows.Media.ImageSource**: WPF専用
- **その他**: カスタム画像クラス（変換メソッド実装必要）

## 📤 出力仕様

### 1. 標準出力（stdout）

#### ログ形式
```
YYYY-MM-DD HH:mm:ss,sss - LEVEL - メッセージ
```

#### 主要ログメッセージ（メモリベース特有）
```
メモリからのフレーム最適化を開始しています...
画像 1/8 を変換中...
画像 2/8 を変換中...
...
すべての画像の変換が完了しました
8個の画像を一時ファイルに保存しました
FrameOptimizer.exeを実行中...
2025-08-21 20:56:11,808 - INFO - 入力ディレクトリ: C:\Temp\FrameOptimizer_12345678-1234-1234-1234-123456789abc
2025-08-21 20:56:11,808 - INFO - 出力ディレクトリ: C:\OutputImages
2025-08-21 20:56:11,808 - INFO - 鮮明度閾値: 150.0
2025-08-21 20:56:11,808 - INFO - 類似度閾値: 0.80
2025-08-21 20:56:11,808 - INFO - フレーム最適化処理を開始...
2025-08-21 20:56:11,808 - INFO - 入力画像数: 8
2025-08-21 20:56:11,808 - INFO - 鮮明度フィルタリングを開始...
2025-08-21 20:56:11,816 - INFO - temp_image_0001.jpeg: 鮮明度 = 156.89
2025-08-21 20:56:11,817 - INFO - ✓ 鮮明度基準を満たす: temp_image_0001.jpeg
2025-08-21 20:56:11,841 - INFO - 鮮明度フィルタリング完了: 6/8 画像が選択
2025-08-21 20:56:11,841 - INFO - 類似度フィルタリングを開始...
2025-08-21 20:56:11,872 - INFO - temp_image_0002.jpeg vs temp_image_0001.jpeg: 類似度 = 0.090
2025-08-21 20:56:11,873 - INFO - ✓ 類似度基準を満たす: temp_image_0002.jpeg
2025-08-21 20:56:11,953 - INFO - 類似度フィルタリング完了: 4/6 画像が選択
2025-08-21 20:56:11,953 - INFO - 画像リネームを開始...
2025-08-21 20:56:11,953 - INFO - ✓ temp_image_0001.jpeg → still_image_1_0001.jpeg
2025-08-21 20:56:11,954 - INFO - フレーム最適化処理完了!
2025-08-21 20:56:11,954 - INFO - 最終結果: 4 画像

✅ 処理完了: 4 画像が最適化されました
出力先: C:\OutputImages
メモリベースの最適化が完了しました
一時ファイルをクリーンアップ中...
一時ファイルのクリーンアップが完了しました
```

#### 抽出可能な情報
| 情報 | 抽出パターン | 例 |
|------|--------------|-----|
| 入力画像数 | `入力画像数: (\d+)` | `入力画像数: 8` |
| 鮮明度フィルタリング結果 | `鮮明度フィルタリング完了: (\d+)/(\d+)` | `鮮明度フィルタリング完了: 6/8` |
| 類似度フィルタリング結果 | `類似度フィルタリング完了: (\d+)/(\d+)` | `類似度フィルタリング完了: 4/6` |
| 最終結果 | `処理完了: (\d+) 画像` | `処理完了: 4 画像` |

### 2. エラー出力（stderr）
```
エラーメッセージ（エラーが発生した場合のみ）
```

### 3. 終了コード（ExitCode）
| コード | 意味 | 説明 |
|--------|------|------|
| `0` | 成功 | 正常に処理が完了 |
| `1` | 一般エラー | 引数エラー、ファイルアクセスエラーなど |
| `2` | システムエラー | メモリ不足、権限エラーなど |

### 4. 出力ファイル

#### 出力ディレクトリ
- **自動作成**: 存在しない場合は自動作成
- **書き込み権限**: プロセスに書き込み権限が必要

#### 出力ファイル形式
```
still_image_1_0001.jpeg
still_image_1_0002.jpeg
still_image_1_0003.jpeg
still_image_1_0004.jpeg
...
```

#### ファイル名規則
- **プレフィックス**: `still_image_1_`
- **連番**: 4桁ゼロパディング (`0001`, `0002`, ...)
- **拡張子**: JPEG形式で統一

## 🔧 C#での入出力処理

### 入力データの準備
```csharp
// 画像データの検証
if (imageDataList == null || imageDataList.Count == 0)
    throw new ArgumentException("画像データが指定されていません");

if (imageDataList.Count > 1000)
    throw new ArgumentException("画像数が多すぎます（最大1000枚）");

foreach (var imageData in imageDataList)
{
    if (imageData == null || imageData.Length == 0)
        throw new ArgumentException("空の画像データが含まれています");
    
    if (imageData.Length > 50 * 1024 * 1024) // 50MB制限
        throw new ArgumentException("画像サイズが大きすぎます（最大50MB）");
}
```

### 出力データの処理
```csharp
// 標準出力の解析
foreach (var line in outputLines)
{
    // 入力画像数
    var inputMatch = Regex.Match(line, @"入力画像数:\s*(\d+)");
    
    // 鮮明度フィルタリング結果
    var sharpMatch = Regex.Match(line, @"鮮明度フィルタリング完了:\s*(\d+)/(\d+)");
    
    // 類似度フィルタリング結果
    var similarMatch = Regex.Match(line, @"類似度フィルタリング完了:\s*(\d+)/(\d+)");
    
    // 最終結果
    var finalMatch = Regex.Match(line, @"処理完了:\s*(\d+)\s*画像");
}

// 出力ファイルの確認
var outputFiles = Directory.GetFiles(outputDir, "*.jpeg")
    .Concat(Directory.GetFiles(outputDir, "*.jpg"))
    .Concat(Directory.GetFiles(outputDir, "*.png"))
    .ToArray();
```

### 結果オブジェクトの活用
```csharp
var result = await optimizer.OptimizeFramesFromMemoryAsync(imageDataList, outputDir);

if (result.Success)
{
    Console.WriteLine($"入力画像数: {result.InputImageCount}");
    Console.WriteLine($"総入力サイズ: {result.TotalInputSize / (1024*1024):F1} MB");
    Console.WriteLine($"平均画像サイズ: {result.AverageInputSize / (1024*1024):F1} MB");
    Console.WriteLine($"出力ファイル数: {result.OutputFileCount}");
    Console.WriteLine($"鮮明度OK: {result.SharpImageCount}");
    Console.WriteLine($"類似度OK: {result.UniqueImageCount}");
    Console.WriteLine($"最終結果: {result.FinalImageCount}");
}
```

## ⚠️ 注意事項

### エンコーディング
- **標準出力/エラー**: UTF-8
- **ファイルパス**: Windows標準（UTF-16）
- **ログメッセージ**: UTF-8（日本語対応）

### パス処理
- **区切り文字**: Windows標準（`\`）
- **一時ディレクトリ**: `%TEMP%\FrameOptimizer_{GUID}\`
- **相対パス**: 絶対パスに変換して処理

### エラーハンドリング
- **画像データ検証**: null、空、サイズ制限のチェック
- **一時ファイル管理**: 作成・削除の確実な実行
- **クリーンアップ**: エラー時も一時ファイルを削除
- **権限エラー**: 一時ディレクトリ作成権限の確認

### パフォーマンス
- **メモリ使用量**: 画像サイズと枚数に比例
- **処理時間**: 画像数と解像度に比例
- **一時ファイルI/O**: 大量画像の場合、一時ファイル作成がボトルネック
- **並列処理**: 現在は単一スレッドで処理

### 一時ファイル管理
- **自動作成**: GUIDベースの一意なディレクトリ名
- **自動削除**: 処理完了後の確実なクリーンアップ
- **エラー対応**: 例外発生時もクリーンアップ実行
- **ディスク容量**: 一時ファイル用の十分な容量確保

## 🧪 テスト項目

### 入力テスト
- [ ] 正常な画像データ
- [ ] null画像データ
- [ ] 空の画像データ
- [ ] サイズ制限超過画像
- [ ] 枚数制限超過
- [ ] サポートされていない画像形式
- [ ] 破損した画像データ

### 出力テスト
- [ ] 標準出力の文字エンコーディング
- [ ] エラー出力の内容
- [ ] 終了コードの正確性
- [ ] 出力ファイルの形式
- [ ] ファイル名の連番
- [ ] 一時ファイルのクリーンアップ

### 設定テスト
- [ ] 鮮明度閾値の範囲（0-1000）
- [ ] 類似度閾値の範囲（0-1）
- [ ] デフォルト値の動作
- [ ] 不正な値の処理

### 一時ファイルテスト
- [ ] 一時ディレクトリの作成
- [ ] 一時ファイルの保存
- [ ] 処理後のクリーンアップ
- [ ] エラー時のクリーンアップ
- [ ] ディスク容量不足時の処理

## 💡 使用シーン

### 適している用途
- **リアルタイム処理**: カメラからのストリーミング画像
- **メモリ内処理**: メモリ上で生成・編集された画像
- **ネットワーク画像**: ダウンロードした画像の即座処理
- **UI統合**: WPF、Windows Forms等での画像処理
- **カスタム処理**: 独自の画像生成・変換処理

### 適していない用途
- **バッチ処理**: 大量の既存ファイルの一括処理
- **オフライン処理**: ディスク上の画像ファイル処理
- **定期処理**: 定期的に生成される画像の処理
- **低メモリ環境**: メモリ制限が厳しい環境

## 🔄 処理フロー

```
1. メモリ上の画像データ
   ↓
2. 画像データの検証
   ↓
3. 一時ディレクトリ作成
   ↓
4. 一時ファイルとして保存
   ↓
5. FrameOptimizer.exe実行
   ↓
6. 結果取得
   ↓
7. 一時ファイルクリーンアップ
   ↓
8. 最適化された画像出力
```
