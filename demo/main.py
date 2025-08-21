#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
フレーム自動品質フィルタリングシステム
内視鏡動画のフレームから、鮮明度と類似度を評価して最適なフレームを選択し、連番でリネームする
"""

import argparse
import glob
import logging
import os
from typing import List

import cv2  # type: ignore
import numpy as np  # type: ignore
from skimage.metrics import structural_similarity as ssim  # type: ignore

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FrameOptimizer:
    """フレーム最適化クラス"""
    
    def __init__(self, input_dir: str, output_dir: str, 
                 sharpness_threshold: float = 100.0, 
                 similarity_threshold: float = 0.85):
        """
        初期化
        
        Args:
            input_dir: 入力画像ディレクトリ
            output_dir: 出力画像ディレクトリ
            sharpness_threshold: 鮮明度閾値（ラプラシアンの分散）
            similarity_threshold: 類似度閾値（SSIM）
        """
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.sharpness_threshold = sharpness_threshold
        self.similarity_threshold = similarity_threshold
        
        # 出力ディレクトリが存在しない場合は作成
        os.makedirs(output_dir, exist_ok=True)
        
        logger.info(f"入力ディレクトリ: {input_dir}")
        logger.info(f"出力ディレクトリ: {output_dir}")
        logger.info(f"鮮明度閾値: {sharpness_threshold}")
        logger.info(f"類似度閾値: {similarity_threshold}")
    
    def calculate_sharpness(self, image: np.ndarray) -> float:
        """
        画像の鮮明度を計算（ラプラシアンの分散）
        
        Args:
            image: 入力画像
            
        Returns:
            float: 鮮明度スコア
        """
        # グレースケールに変換
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
            
        # ラプラシアンフィルタを適用
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        
        # 分散を計算
        sharpness = laplacian.var()
        
        return sharpness
    
    def calculate_similarity(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """
        2つの画像の類似度を計算（SSIM）
        
        Args:
            img1: 画像1
            img2: 画像2
            
        Returns:
            float: SSIMスコア（0-1、1に近いほど類似）
        """
        # グレースケールに変換
        if len(img1.shape) == 3:
            gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        else:
            gray1 = img1
            
        if len(img2.shape) == 3:
            gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
        else:
            gray2 = img2
        
        # サイズを統一
        if gray1.shape != gray2.shape:
            gray2 = cv2.resize(gray2, (gray1.shape[1], gray1.shape[0]))
        
        # SSIMを計算
        similarity = ssim(gray1, gray2)
        
        return similarity
    
    def filter_by_sharpness(self, image_paths: List[str]) -> List[str]:
        """
        鮮明度でフィルタリング
        
        Args:
            image_paths: 画像パスのリスト
            
        Returns:
            List[str]: 鮮明度基準を満たす画像パスのリスト
        """
        logger.info("鮮明度フィルタリングを開始...")
        
        sharp_images = []
        for i, img_path in enumerate(image_paths):
            try:
                image = cv2.imread(img_path)
                if image is None:
                    logger.warning(f"画像を読み込めません: {img_path}")
                    continue
                
                sharpness = self.calculate_sharpness(image)
                logger.info(f"{os.path.basename(img_path)}: 鮮明度 = {sharpness:.2f}")
                
                if sharpness >= self.sharpness_threshold:
                    sharp_images.append(img_path)
                    logger.info(f"✓ 鮮明度基準を満たす: {os.path.basename(img_path)}")
                else:
                    logger.info(f"✗ 鮮明度基準を満たさない: {os.path.basename(img_path)}")
                    
            except Exception as e:
                logger.error(f"画像処理エラー {img_path}: {e}")
                continue
        
        logger.info(f"鮮明度フィルタリング完了: {len(sharp_images)}/{len(image_paths)} 画像が選択")
        return sharp_images
    
    def filter_by_similarity(self, image_paths: List[str]) -> List[str]:
        """
        類似度でフィルタリング（重複除去）
        
        Args:
            image_paths: 画像パスのリスト
            
        Returns:
            List[str]: 類似度フィルタリング後の画像パスのリスト
        """
        logger.info("類似度フィルタリングを開始...")
        
        if len(image_paths) <= 1:
            return image_paths
        
        # 画像を読み込み
        images = []
        valid_paths = []
        
        for img_path in image_paths:
            try:
                image = cv2.imread(img_path)
                if image is not None:
                    images.append(image)
                    valid_paths.append(img_path)
                else:
                    logger.warning(f"画像を読み込めません: {img_path}")
            except Exception as e:
                logger.error(f"画像読み込みエラー {img_path}: {e}")
                continue
        
        if len(images) <= 1:
            return valid_paths
        
        # 類似度フィルタリング
        selected_indices = [0]  # 最初の画像は必ず選択
        
        for i in range(1, len(images)):
            is_similar = False
            
            for selected_idx in selected_indices:
                similarity = self.calculate_similarity(images[i], images[selected_idx])
                logger.info(f"{os.path.basename(valid_paths[i])} vs {os.path.basename(valid_paths[selected_idx])}: 類似度 = {similarity:.3f}")
                
                if similarity >= self.similarity_threshold:
                    is_similar = True
                    logger.info(f"✗ 類似度が高いため除外: {os.path.basename(valid_paths[i])}")
                    break
            
            if not is_similar:
                selected_indices.append(i)
                logger.info(f"✓ 類似度基準を満たす: {os.path.basename(valid_paths[i])}")
        
        selected_paths = [valid_paths[i] for i in selected_indices]
        logger.info(f"類似度フィルタリング完了: {len(selected_paths)}/{len(valid_paths)} 画像が選択")
        
        return selected_paths
    
    def rename_images(self, image_paths: List[str]) -> List[str]:
        """
        画像を連番でリネーム
        
        Args:
            image_paths: 画像パスのリスト
            
        Returns:
            List[str]: リネーム後の画像パスのリスト
        """
        logger.info("画像リネームを開始...")
        
        renamed_paths = []
        
        for i, img_path in enumerate(image_paths, 1):
            # 元のファイル拡張子を取得
            _, ext = os.path.splitext(img_path)
            
            # 新しいファイル名を生成
            new_filename = f"still_image_1_{i:04d}{ext}"
            new_path = os.path.join(self.output_dir, new_filename)
            
            try:
                # 画像をコピー
                import shutil
                shutil.copy2(img_path, new_path)
                renamed_paths.append(new_path)
                logger.info(f"✓ {os.path.basename(img_path)} → {new_filename}")
                
            except Exception as e:
                logger.error(f"画像コピーエラー {img_path}: {e}")
                continue
        
        logger.info(f"リネーム完了: {len(renamed_paths)} 画像を処理")
        return renamed_paths
    
    def process(self) -> List[str]:
        """
        メイン処理：鮮明度フィルタリング → 類似度フィルタリング → リネーム
        
        Returns:
            List[str]: 最終的な画像パスのリスト
        """
        logger.info("フレーム最適化処理を開始...")
        
        # 入力画像を取得（ソート）
        image_pattern = os.path.join(self.input_dir, "*.jpeg")
        image_paths = sorted(glob.glob(image_pattern))
        
        if not image_paths:
            image_pattern = os.path.join(self.input_dir, "*.jpg")
            image_paths = sorted(glob.glob(image_pattern))
        
        if not image_paths:
            image_pattern = os.path.join(self.input_dir, "*.png")
            image_paths = sorted(glob.glob(image_pattern))
        
        if not image_paths:
            logger.error(f"入力ディレクトリに画像が見つかりません: {self.input_dir}")
            return []
        
        logger.info(f"入力画像数: {len(image_paths)}")
        
        # 1. 鮮明度フィルタリング
        sharp_images = self.filter_by_sharpness(image_paths)
        
        # 2. 類似度フィルタリング
        unique_images = self.filter_by_similarity(sharp_images)
        
        # 3. リネーム
        final_images = self.rename_images(unique_images)
        
        logger.info("フレーム最適化処理完了!")
        logger.info(f"最終結果: {len(final_images)} 画像")
        
        return final_images

def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description='フレーム自動品質フィルタリングシステム')
    parser.add_argument('input_dir', help='入力画像ディレクトリ')
    parser.add_argument('output_dir', help='出力画像ディレクトリ')
    parser.add_argument('--sharpness', type=float, default=100.0, 
                       help='鮮明度閾値（デフォルト: 100.0）')
    parser.add_argument('--similarity', type=float, default=0.85, 
                       help='類似度閾値（デフォルト: 0.85）')
    
    args = parser.parse_args()
    
    # フレーム最適化を実行
    optimizer = FrameOptimizer(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        sharpness_threshold=args.sharpness,
        similarity_threshold=args.similarity
    )
    
    try:
        result = optimizer.process()
        if result:
            print(f"\n✅ 処理完了: {len(result)} 画像が最適化されました")
            print(f"出力先: {args.output_dir}")
        else:
            print("\n❌ 処理に失敗しました")
            
    except Exception as e:
        logger.error(f"処理エラー: {e}")
        print(f"\n❌ エラーが発生しました: {e}")

if __name__ == "__main__":
    main()
