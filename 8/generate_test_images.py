#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
テスト用サンプル画像生成スクリプト
フレーム最適化システムのテスト用に、様々な品質の画像を生成する
"""

import os
import random

import cv2  # type: ignore
import numpy as np  # type: ignore


def create_test_image(width=640, height=480, quality='sharp', blur_level=0):
    """
    テスト用画像を生成
    
    Args:
        width: 画像幅
        height: 画像高さ
        quality: 画像品質 ('sharp', 'blur', 'noise')
        blur_level: ぼかしレベル（0-10）
        
    Returns:
        np.ndarray: 生成された画像
    """
    # ベース画像を作成（グラデーション + ノイズ）
    base = np.zeros((height, width, 3), dtype=np.uint8)
    
    # グラデーションを作成
    for y in range(height):
        for x in range(width):
            r = int(255 * x / width)
            g = int(255 * y / height)
            b = int(128 + 127 * np.sin(x / 50) * np.cos(y / 50))
            base[y, x] = [r, g, b]
    
    # 円形のパターンを追加
    center_x, center_y = width // 2, height // 2
    radius = min(width, height) // 4
    
    for y in range(height):
        for x in range(width):
            dist = np.sqrt((x - center_x)**2 + (y - center_y)**2)
            if dist < radius:
                intensity = int(255 * (1 - dist / radius))
                base[y, x] = [intensity, intensity, intensity]
    
    # 品質に応じて画像を調整
    if quality == 'blur':
        # ぼかしを適用
        kernel_size = 2 * blur_level + 1
        if kernel_size > 1:
            base = cv2.GaussianBlur(base, (kernel_size, kernel_size), 0)
    
    elif quality == 'noise':
        # ノイズを追加
        noise = np.random.normal(0, 25, base.shape).astype(np.uint8)
        base = cv2.add(base, noise)
        base = np.clip(base, 0, 255)
    
    return base

def generate_test_dataset(output_dir="test_images", num_images=8):
    """
    テストデータセットを生成
    
    Args:
        output_dir: 出力ディレクトリ
        num_images: 生成する画像数
    """
    # 出力ディレクトリを作成
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"テスト画像を生成中: {output_dir}")
    
    # 画像品質のパターン
    qualities = ['sharp', 'blur', 'noise']
    
    for i in range(num_images):
        # ランダムに品質を選択
        quality = random.choice(qualities)
        
        if quality == 'blur':
            blur_level = random.randint(3, 8)
            image = create_test_image(quality=quality, blur_level=blur_level)
            filename = f"still_image_1_{i+1:04d}.jpeg"
        elif quality == 'noise':
            image = create_test_image(quality=quality)
            filename = f"still_image_1_{i+1:04d}.jpeg"
        else:
            image = create_test_image(quality=quality)
            filename = f"still_image_1_{i+1:04d}.jpeg"
        
        # 画像を保存
        output_path = os.path.join(output_dir, filename)
        cv2.imwrite(output_path, image)
        
        print(f"生成: {filename} (品質: {quality})")
    
    print(f"\n✅ {num_images} 個のテスト画像を生成しました")
    print(f"出力先: {output_dir}")

def generate_similar_images(output_dir="test_images", base_image_path=None):
    """
    類似画像を生成（類似度テスト用）
    
    Args:
        output_dir: 出力ディレクトリ
        base_image_path: ベース画像のパス
    """
    os.makedirs(output_dir, exist_ok=True)
    
    if base_image_path and os.path.exists(base_image_path):
        # 既存画像をベースに類似画像を生成
        base_image = cv2.imread(base_image_path)
        if base_image is not None:
            # 少しずつ異なる画像を生成
            for i in range(3):
                # 軽微な変更を加える
                modified = base_image.copy()
                
                # 明度を少し変更
                brightness = random.uniform(0.9, 1.1)
                modified = cv2.convertScaleAbs(modified, alpha=brightness, beta=0)
                
                # 軽微なぼかし
                modified = cv2.GaussianBlur(modified, (3, 3), 0.5)
                
                filename = f"similar_image_{i+1:04d}.jpeg"
                output_path = os.path.join(output_dir, filename)
                cv2.imwrite(output_path, modified)
                
                print(f"類似画像生成: {filename}")
    else:
        print("ベース画像が見つからないため、類似画像の生成をスキップします")

def main():
    """メイン関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='テスト用サンプル画像生成')
    parser.add_argument('--output', default='test_images', help='出力ディレクトリ')
    parser.add_argument('--count', type=int, default=8, help='生成する画像数')
    parser.add_argument('--similar', action='store_true', help='類似画像も生成')
    
    args = parser.parse_args()
    
    # テストデータセットを生成
    generate_test_dataset(args.output, args.count)
    
    # 類似画像を生成（オプション）
    if args.similar:
        base_image = os.path.join(args.output, "still_image_1_0001.jpeg")
        generate_similar_images(args.output, base_image)
    
    print("\n🎯 フレーム最適化システムのテスト準備が完了しました！")
    print("以下のコマンドでテストを実行できます:")
    print(f"python main.py {args.output} optimized_images")

if __name__ == "__main__":
    main()
