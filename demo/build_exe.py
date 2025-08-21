#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows用exeファイルビルドスクリプト
PyInstallerでexeファイルをビルドする
"""

import os
import platform
import shutil
import subprocess
import sys


def check_windows():
    """Windows環境かチェック"""
    if platform.system() != "Windows":
        print("⚠️ このスクリプトはWindows環境で実行してください")
        print(f"現在のOS: {platform.system()}")
        return False
    return True

def install_pyinstaller():
    """PyInstallerをインストール"""
    try:
        import PyInstaller
        print("✅ PyInstallerは既にインストールされています")
        return True
    except ImportError:
        print("PyInstallerをインストール中...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
            print("✅ PyInstallerのインストールが完了しました")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ PyInstallerのインストールに失敗しました: {e}")
            return False

def build_exe():
    """exeファイルをビルド"""
    print("🚀 exeファイルのビルドを開始...")
    
    # ビルド設定
    script_name = "main.py"
    exe_name = "FrameOptimizer.exe"
    
    # PyInstallerコマンドを構築（Windows用）
    cmd = [
        "pyinstaller",
        "--onefile",  # 単一のexeファイルに
        "--windowed",  # コンソールウィンドウを非表示
        "--name", exe_name,
        "--add-data", "config.py;.",  # 設定ファイルを含める（Windows用）
        "--hidden-import", "cv2",
        "--hidden-import", "skimage",
        "--hidden-import", "numpy",
        "--icon", "icon.ico",  # アイコンファイル（オプション）
        script_name
    ]
    
    # アイコンファイルが存在しない場合は除外
    if not os.path.exists("icon.ico"):
        cmd.remove("--icon")
        cmd.remove("icon.ico")
        print("ℹ️ アイコンファイルが見つからないため、デフォルトアイコンを使用")
    
    try:
        # PyInstallerを実行
        print(f"実行コマンド: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        print("✅ ビルドが完了しました！")
        
        # 出力ファイルの場所を表示
        dist_dir = "dist"
        exe_path = os.path.join(dist_dir, exe_name)
        
        if os.path.exists(exe_path):
            file_size_mb = os.path.getsize(exe_path) / (1024*1024)
            print(f"📁 exeファイルの場所: {os.path.abspath(exe_path)}")
            print(f"📊 ファイルサイズ: {file_size_mb:.1f} MB")
            
            # ファイルサイズの警告
            if file_size_mb > 100:
                print("⚠️ ファイルサイズが大きいです（100MB以上）")
                print("   配布時は注意が必要です")
        else:
            print("⚠️ exeファイルが見つかりません")
            
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ ビルドに失敗しました: {e}")
        if e.stdout:
            print(f"標準出力: {e.stdout}")
        if e.stderr:
            print(f"エラー出力: {e.stderr}")
        return False

def clean_build_files():
    """ビルドファイルをクリーンアップ"""
    print("🧹 ビルドファイルをクリーンアップ中...")
    
    dirs_to_remove = ["build", "__pycache__"]
    files_to_remove = ["*.spec"]
    
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"削除: {dir_name}")
    
    for pattern in files_to_remove:
        for file_path in glob.glob(pattern):
            os.remove(file_path)
            print(f"削除: {file_path}")
    
    print("✅ クリーンアップ完了")

def create_batch_file():
    """Windows用のバッチファイルを作成"""
    batch_content = """@echo off
REM フレーム最適化システム実行ファイル
REM 使用方法: FrameOptimizer.exe input_folder output_folder [options]

echo フレーム最適化システムを起動中...
echo.

if "%1"=="" (
    echo 使用方法: FrameOptimizer.exe input_folder output_folder
    echo 例: FrameOptimizer.exe test_images optimized_images
    pause
    exit /b 1
)

if "%2"=="" (
    echo 出力ディレクトリが指定されていません
    echo 使用方法: FrameOptimizer.exe input_folder output_folder
    pause
    exit /b 1
)

echo 入力ディレクトリ: %1
echo 出力ディレクトリ: %2
echo.

FrameOptimizer.exe %*

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ 処理が正常に完了しました
) else (
    echo.
    echo ❌ エラーが発生しました
)

pause
"""
    
    batch_file = "run_frame_optimizer.bat"
    with open(batch_file, "w", encoding="shift_jis") as f:
        f.write(batch_content)
    
    print(f"✅ バッチファイルを作成: {batch_file}")

def main():
    """メイン関数"""
    print("🔧 フレーム最適化システム - Windows exeビルドツール")
    print("=" * 60)
    
    # Windows環境チェック
    if not check_windows():
        return False
    
    # 現在のディレクトリを確認
    current_dir = os.getcwd()
    print(f"現在のディレクトリ: {current_dir}")
    
    # 必要なファイルの存在確認
    required_files = ["main.py", "config.py"]
    missing_files = [f for f in required_files if not os.path.exists(f)]
    
    if missing_files:
        print(f"❌ 必要なファイルが見つかりません: {missing_files}")
        return False
    
    print("✅ 必要なファイルが確認できました")
    
    # PyInstallerをインストール
    if not install_pyinstaller():
        return False
    
    # exeファイルをビルド
    if not build_exe():
        return False
    
    # バッチファイルを作成
    create_batch_file()
    
    print("\n🎉 ビルドが正常に完了しました！")
    print("\n📁 生成されたファイル:")
    print("  - dist/FrameOptimizer.exe (メイン実行ファイル)")
    print("  - run_frame_optimizer.bat (実行用バッチファイル)")
    
    print("\n🚀 使用方法:")
    print("1. distフォルダ内のFrameOptimizer.exeを実行")
    print("2. または、run_frame_optimizer.batをダブルクリック")
    print("3. コマンドライン引数で入力・出力ディレクトリを指定")
    print("   例: FrameOptimizer.exe input_folder output_folder")
    print("   例: FrameOptimizer.exe input_folder output_folder --sharpness 150 --similarity 0.80")
    
    print("\n💡 配布方法:")
    print("  - FrameOptimizer.exe と run_frame_optimizer.bat を配布")
    print("  - ユーザーはPython環境不要で実行可能")
    
    return True

if __name__ == "__main__":
    import glob
    success = main()
    if not success:
        print("\n❌ ビルドに失敗しました")
        sys.exit(1)
    else:
        print("\n✨ すべての処理が完了しました！")
