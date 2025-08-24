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
        print("このスクリプトはWindows環境で実行してください")
        print(f"現在のOS: {platform.system()}")
        return False
    return True

def install_pyinstaller():
    """PyInstallerをインストール"""
    try:
        import PyInstaller
        print("PyInstallerは既にインストールされています")
        return True
    except ImportError:
        print("PyInstallerをインストール中...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
            print("PyInstallerのインストールが完了しました")
            return True
        except subprocess.CalledProcessError as e:
            print(f"PyInstallerのインストールに失敗しました: {e}")
            return False

def build_exe():
    """exeファイルをビルド"""
    print("🚀 exeファイルのビルドを開始...")
    
    # ビルド設定
    script_name = "main.py"
    exe_name = "ImageQualityScreener.exe"
    
    # PyInstallerコマンドを構築（Windows用）
    cmd = [
        "pyinstaller",
        "--onefile",  # 単一のexeファイルに
        "--windowed",  # コンソールウィンドウを非表示
        "--name", exe_name,

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
        
        print("ビルドが完了しました！")
        
        # 出力ファイルの場所を表示
        dist_dir = "dist"
        exe_path = os.path.join(dist_dir, exe_name)
        
        if os.path.exists(exe_path):
            file_size_mb = os.path.getsize(exe_path) / (1024*1024)
            print(f"exeファイルの場所: {os.path.abspath(exe_path)}")
            print(f"ファイルサイズ: {file_size_mb:.1f} MB")
            
            # ファイルサイズの警告
            if file_size_mb > 100:
                print("ファイルサイズが大きいです（100MB以上）")
                print("   配布時は注意が必要です")
        else:
            print("exeファイルが見つかりません")
            
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"ビルドに失敗しました: {e}")
        if e.stdout:
            print(f"標準出力: {e.stdout}")
        if e.stderr:
            print(f"エラー出力: {e.stderr}")
        return False

def clean_build_files():
    """ビルドファイルをクリーンアップ"""
    print("ビルドファイルをクリーンアップ中...")
    
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
    
    print("クリーンアップ完了")



def main():
    """メイン関数"""
    print("画像品質スクリーニングシステム - Windows exeビルドツール")
    print("=" * 60)
    
    # Windows環境チェック
    if not check_windows():
        return False
    
    # 現在のディレクトリを確認
    current_dir = os.getcwd()
    print(f"現在のディレクトリ: {current_dir}")
    
    # 必要なファイルの存在確認
    required_files = ["main.py"]
    missing_files = [f for f in required_files if not os.path.exists(f)]
    
    if missing_files:
        print(f"必要なファイルが見つかりません: {missing_files}")
        return False
    
    print("必要なファイルが確認できました")
    
    # PyInstallerをインストール
    if not install_pyinstaller():
        return False
    
    # exeファイルをビルド
    if not build_exe():
        return False
    
    print("\nビルドが正常に完了しました！")
    print("\n生成されたファイル:")
    print("  - dist/ImageQualityScreener.exe (メイン実行ファイル)")
    
    print("\n使用方法:")
    print("1. distフォルダ内のImageQualityScreener.exeを実行")
    print("2. コマンドライン引数で入力・出力ディレクトリを指定")
    print("   例: ImageQualityScreener.exe input_folder output_folder")
    print("   例: ImageQualityScreener.exe input_folder output_folder --sharpness 150 --similarity 0.80")
    
    print("\n配布方法:")
    print("  - ImageQualityScreener.exe のみを配布")
    print("  - C#アプリケーションから直接呼び出し可能")
    
    return True

if __name__ == "__main__":
    import glob
    success = main()
    if not success:
        print("\nビルドに失敗しました")
        sys.exit(1)
    else:
        print("\nすべての処理が完了しました！")
