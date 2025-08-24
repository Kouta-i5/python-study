# 画像品質スクリーニングシステム - C#デモ

## 概要

このプロジェクトは、Pythonで作成された画像品質スクリーニングシステムをC#アプリケーションから呼び出すためのデモアプリケーションです。

## ファイル構成

```
c_demo/
├── ImageQualityScreener.csproj  # C#プロジェクトファイル
├── ImageProcessor.cs             # 画像処理クラス
├── Program.cs                    # メインプログラム
├── README.md                     # このファイル
└── ImageQualityScreener.exe     # Pythonスクリプトから生成された実行ファイル
```

## 必要な環境

- .NET 6.0 以上
- `ImageQualityScreener.exe` ファイル（`8/build_exe.py`で生成）

## 使用方法

### 1. ビルド

```bash
cd c_demo
dotnet build
```

### 2. 実行

#### 基本的な実行
```bash
dotnet run
```

#### カスタムディレクトリを指定
```bash
dotnet run "InputImages" "OutputImages"
```

### 3. ディレクトリ構造

```
実行ディレクトリ/
├── ImageQualityScreener.exe     # 実行ファイル
├── InputImages/                  # 入力画像フォルダ
│   ├── still_image_1_0001.jpeg
│   ├── still_image_1_0002.jpeg
│   └── ...
└── OutputImages/                 # 出力画像フォルダ（自動生成）
    ├── still_image_1_0001.jpeg
    ├── still_image_1_0002.jpeg
    └── ...
```

## 機能

### ImageProcessor クラス

- **ProcessImagesAsync()**: 非同期で画像品質スクリーニングを実行
- **ProcessImages()**: 同期的に画像品質スクリーニングを実行

### 処理フロー

1. 入力ディレクトリから画像を読み込み
2. `ImageQualityScreener.exe`を呼び出し
3. 鮮明度・類似度でスクリーニング実行
4. 結果を出力ディレクトリに保存
5. 処理結果を表示

### 出力情報

- 入力画像数
- スクリーニング済み画像数
- 除外された画像数
- 各画像のファイルサイズ

## エラーハンドリング

- .exeファイルの存在確認
- 入力ディレクトリの存在確認
- プロセス実行エラーの捕捉
- 詳細なエラーメッセージの表示

## 統合方法

### C#アプリケーションへの組み込み

```csharp
var processor = new ImageProcessor();
bool success = await processor.ProcessImagesAsync("input", "output");
```

### 設定可能なパラメータ

- 入力ディレクトリ
- 出力ディレクトリ
- 非同期/同期実行

## 注意事項

- `ImageQualityScreener.exe`は同じディレクトリに配置する必要があります
- 入力画像は`.jpeg`形式を想定しています
- 出力画像も`.jpeg`形式で保存されます

## トラブルシューティング

### よくある問題

1. **.exeファイルが見つからない**
   - `ImageQualityScreener.exe`が正しい場所にあるか確認

2. **入力ディレクトリが存在しない**
   - 指定したディレクトリパスが正しいか確認

3. **権限エラー**
   - 出力ディレクトリに書き込み権限があるか確認

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。
