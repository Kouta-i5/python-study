#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
画像品質スクリーニング
不鮮明画像検出(ラプラシアン分散を使い、ボケている画像とノイズ画像をスクリーニング)とフリーズ検出(SSIMを使いフレーム間の類似度を測り重複画像をスクリーニング)
"""

import argparse
import glob
import logging
import os
from typing import List, Optional

import cv2  # type: ignore
import numpy as np  # type: ignore
from skimage.metrics import structural_similarity as ssim  # type: ignore

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ImageQualityScreener:
    """画像品質スクリーニングクラス（改良版）"""
    
    def __init__(self, input_dir: str, output_dir: str, 
                 sharpness_threshold_min: Optional[float] = None, 
                 sharpness_threshold_max: float = 5000.0,
                 similarity_threshold: float = 0.90):
        """
        初期化
        
        Args:
            input_dir: 入力画像ディレクトリ
            output_dir: 出力画像ディレクトリ
            sharpness_threshold_min: 鮮明度閾値の下限（Noneの場合は自動設定）
            sharpness_threshold_max: 鮮明度閾値の上限（デフォルト: 5000.0）
            similarity_threshold: 類似度閾値（SSIM、デフォルト: 0.90）
        """
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.sharpness_threshold_min = sharpness_threshold_min
        self.sharpness_threshold_max = sharpness_threshold_max
        self.similarity_threshold = similarity_threshold
        
        # 鮮明度の統計情報
        self.sharpness_values: List[float] = []
        self.sharpness_mean: float = 0.0
        self.sharpness_std: float = 0.0
        
        # 出力ディレクトリが存在しない場合は作成
        os.makedirs(output_dir, exist_ok=True)
        
        logger.info(f"入力: {input_dir}")
        logger.info(f"出力: {output_dir}")
        if sharpness_threshold_min:
            logger.info(f"鮮明度下限: {sharpness_threshold_min}")
        logger.info(f"鮮明度上限: {sharpness_threshold_max}")
        logger.info(f"類似度閾値: {similarity_threshold}")
    
    # 不鮮明画像検出（ラプラシアン分散）
    def detect_blur_and_noise(self, image: np.ndarray) -> float:
        """
        不鮮明画像検出（ラプラシアンの分散）
        
        Args:
            image: 入力画像
            
        Returns:
            float: 鮮明度スコア（値が低いほどボケ、高いほどノイズ）
        """
        # ３チャンネルのRGB画像を１チャンネルのグレースケールに変換
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
            
        # ラプラシアンフィルタを適用
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        
        # 分散を計算
        sharpness = laplacian.var()
        
        return sharpness
    
    # フリーズ検出（SSIM）
    def detect_freeze(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """
        フリーズ検出（SSIM）
        
        Args:
            img1: 画像1
            img2: 画像2
            
        Returns:
            float: SSIMスコア（0-1、1に近いほどフリーズの可能性）
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
    
    # 画像を一度だけ読み込み、鮮明度も計算
    def load_images_once(self, image_paths: List[str]) -> tuple[List[np.ndarray], List[str], List[float]]:
        """
        画像を一度だけ読み込み、鮮明度も計算
        
        Args:
            image_paths: 画像パスのリスト
            
        Returns:
            tuple: (画像リスト, 有効なパスリスト, 鮮明度リスト)
        """
        images = []
        valid_paths = []
        sharpness_values = []
        
        for img_path in image_paths:
            try:
                image = cv2.imread(img_path)
                if image is not None:
                    images.append(image)
                    valid_paths.append(img_path)
                    sharpness = self.detect_blur_and_noise(image)
                    sharpness_values.append(sharpness)
                else:
                    logger.warning(f"画像を読み込めません: {img_path}")
            except Exception as e:
                logger.error(f"画像読み込みエラー {img_path}: {e}")
                continue
        
        return images, valid_paths, sharpness_values
    
    # 鮮明度統計を計算し、適応的な閾値を自動設定
    def calculate_image_statistics(self, sharpness_values: List[float]) -> None:
        """
        鮮明度統計を計算し、適応的な閾値を自動設定
        
        Args:
            sharpness_values: 鮮明度のリスト
        """
        logger.info("画像統計情報の計算を開始...")
        
        # 統計情報を設定
        self.sharpness_values = sharpness_values
        
        # 統計を計算
        if self.sharpness_values:
            self.sharpness_mean = np.mean(self.sharpness_values)
            self.sharpness_std = np.std(self.sharpness_values)
            
            logger.info(f"鮮明度統計: 平均={self.sharpness_mean:.2f}, 標準偏差={self.sharpness_std:.2f}, 枚数={len(self.sharpness_values)}")
        
        # 自動閾値設定
        std_multiplier = 1.5
        if self.sharpness_threshold_min is None and self.sharpness_values:
            # 平均 - std_multiplier倍標準偏差で下限を設定（ただし最小値は10）
            self.sharpness_threshold_min = max(10.0, self.sharpness_mean - std_multiplier * self.sharpness_std)
            
            logger.info(f"自動設定された鮮明度閾値下限: {self.sharpness_threshold_min:.2f}")
            logger.info(f"  (全体平均: {self.sharpness_mean:.2f}, 標準偏差: {self.sharpness_std:.2f}, {std_multiplier}倍標準偏差: {std_multiplier * self.sharpness_std:.2f})")
    
    # 不鮮明画像検出（ボケ画像・ノイズ画像をスクリーニング）
    def screen_image_quality(self, image_paths: List[str], images: List[np.ndarray], sharpness_values: List[float]) -> List[str]:
        """
        不鮮明画像検出（ボケ画像・ノイズ画像をスクリーニング）
        
        Args:
            image_paths: 画像パスのリスト
            images: 事前に読み込んだ画像リスト
            sharpness_values: 事前に計算された鮮明度リスト
            
        Returns:
            List[str]: 品質基準を満たす画像パスのリスト
        """
        logger.info("品質スクリーニングを開始...")
        
        sharp_images = []
        for i, (img_path, sharpness) in enumerate(zip(image_paths, sharpness_values)):
            # ノイズ画像の除外
            if sharpness > self.sharpness_threshold_max:
                logger.warning(f"ノイズ画像を除外: {os.path.basename(img_path)} (鮮明度: {sharpness:.2f})")
                continue
            
            # 下限チェック
            if self.sharpness_threshold_min is not None and sharpness < self.sharpness_threshold_min:
                logger.info(f"× 鮮明度基準未満: {os.path.basename(img_path)} ({sharpness:.2f})")
                continue
            
            sharp_images.append(img_path)
            logger.info(f"⚪ 鮮明度基準OK: {os.path.basename(img_path)} ({sharpness:.2f})")
        
        logger.info(f"鮮明度フィルタリング完了: {len(sharp_images)}/{len(image_paths)} 画像が選択")
        return sharp_images
    
    # フリーズ検出（重複画像をスクリーニング）
    def screen_duplicate_frames(self, image_paths: List[str]) -> List[str]:
        """
        フリーズ検出（重複画像をスクリーニング）
        
        Args:
            image_paths: 画像パスのリスト
            
        Returns:
            List[str]: 重複除外後の画像パスのリスト
        """
        logger.info("重複除外スクリーニングを開始...")
        
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
        
        # 連続フレーム間の類似度フィルタリング
        selected_indices = [0]  # 最初の画像は必ず選択
        
        for i in range(1, len(images)):
            # 直前の選択されたフレームとのみ比較
            prev_idx = selected_indices[-1]
            similarity = self.detect_freeze(images[i], images[prev_idx])
            
            if similarity >= self.similarity_threshold:
                # フリーズフレームとして除外
                logger.info(f"× フリーズフレーム除外: {os.path.basename(valid_paths[i])} ({similarity:.3f})")
            else:
                # 十分に異なるフレームとして選択
                selected_indices.append(i)
                logger.info(f"⚪ フレーム選択: {os.path.basename(valid_paths[i])} ({similarity:.3f})")
        
        selected_paths = [valid_paths[i] for i in selected_indices]
        logger.info(f"連続フレーム類似度フィルタリング完了: {len(selected_paths)}/{len(valid_paths)} 画像が選択")
        
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
        logger.info("画像スクリーニング処理を開始...")
        
        # 入力画像を取得（複数拡張子を一度に検索）
        extensions = ["*.jpeg", "*.jpg", "*.png", "*.bmp", "*.tiff"]
        image_paths = []
        
        for ext in extensions:
            pattern = os.path.join(self.input_dir, ext)
            paths = glob.glob(pattern)
            image_paths.extend(paths)
        
        image_paths = sorted(image_paths)
        
        if not image_paths:
            logger.error(f"入力ディレクトリに画像が見つかりません: {self.input_dir}")
            return []
        
        logger.info(f"入力画像数: {len(image_paths)}")
        
        # 0. 画像を一度だけ読み込み、鮮明度も計算
        images, valid_paths, sharpness_values = self.load_images_once(image_paths)
        
        # 1. 画像統計情報の計算と自動閾値設定
        self.calculate_image_statistics(sharpness_values)
        
        # 2. 不鮮明画像検出
        sharp_images = self.screen_image_quality(valid_paths, images, sharpness_values)
        
        # 3. フリーズ検出
        unique_images = self.screen_duplicate_frames(sharp_images)
        
        # 3. リネーム
        final_images = self.rename_images(unique_images)
        
        logger.info("画像スクリーニング処理完了!")
        logger.info(f"最終結果: {len(final_images)} 画像")
        
        return final_images

def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description='画像自動品質スクリーニングシステム')
    parser.add_argument('input_dir', help='入力画像ディレクトリ')
    parser.add_argument('output_dir', help='出力画像ディレクトリ')
    parser.add_argument('--sharpness_min', type=float, default=None, 
                       help='鮮明度閾値の下限（指定しない場合は自動設定）')
    parser.add_argument('--sharpness_max', type=float, default=5000.0, 
                       help='鮮明度閾値の上限（デフォルト: 5000.0）')
    parser.add_argument('--similarity', type=float, default=0.90, 
                       help='類似度閾値（デフォルト: 0.90）')

    
    args = parser.parse_args()
    
    # 画像品質スクリーニングを実行
    screener = ImageQualityScreener(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        sharpness_threshold_min=args.sharpness_min,
        sharpness_threshold_max=args.sharpness_max,
        similarity_threshold=args.similarity
    )
    
    try:
        result = screener.process()
        if result:
            print(f"\n✅ 処理完了: {len(result)} 画像がスクリーニングされました")
            print(f"出力先: {args.output_dir}")
        else:
            print("\n❌ 処理に失敗しました")
            
    except Exception as e:
        logger.error(f"処理エラー: {e}")
        print(f"\n❌ エラーが発生しました: {e}")

if __name__ == "__main__":
    main()
