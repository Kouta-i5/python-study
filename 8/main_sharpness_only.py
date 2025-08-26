#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
画像鮮明度スクリーニング（IQRベース）
不鮮明画像検出(ラプラシアン分散を使い、ボケている画像とノイズ画像をスクリーニング)
"""

import argparse
import glob
import logging
import os
from typing import List, Optional

import cv2  # type: ignore
import numpy as np  # type: ignore

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SharpnessScreener:
    """画像鮮明度スクリーニングクラス（IQRベース）"""
    
    def __init__(self, input_dir: str, output_dir: str, 
                 sharpness_threshold_min: Optional[float] = None, 
                 sharpness_threshold_max: float = 5000.0,
                 iqr_multiplier: float = 1.5):  # 静的なIQR係数
        """
        初期化
        
        Args:
            input_dir: 入力画像ディレクトリ
            output_dir: 出力画像ディレクトリ（入力と同じディレクトリ）
            sharpness_threshold_min: 鮮明度閾値の下限（Noneの場合はIQRベースで自動設定）
            sharpness_threshold_max: 鮮明度閾値の上限（デフォルト: 5000.0）
            iqr_multiplier: IQR係数（デフォルト: 1.5、静的設定）
        """
        self.input_dir = input_dir
        self.output_dir = output_dir  # 入力と同じディレクトリ
        self.sharpness_threshold_min = sharpness_threshold_min
        self.sharpness_threshold_max = sharpness_threshold_max
        self.iqr_multiplier = iqr_multiplier  # 静的なIQR係数
        
        # 鮮明度の統計情報
        self.sharpness_values: List[float] = []
        self.sharpness_mean: float = 0.0
        self.sharpness_std: float = 0.0
        
        # 出力ディレクトリが存在しない場合は作成
        os.makedirs(output_dir, exist_ok=True)
        
        logger.info(f"入力・出力: {input_dir}")
        if sharpness_threshold_min:
            logger.info(f"鮮明度下限: {sharpness_threshold_min}")
        logger.info(f"鮮明度上限: {sharpness_threshold_max}")
        logger.info(f"IQR係数: {iqr_multiplier} (静的設定)")
    
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
    
    # 鮮明度統計を計算し、IQRベースで下限しきい値を自動設定
    def calculate_image_statistics(self, sharpness_values: List[float]) -> None:
        """
        鮮明度統計を計算し、IQRベースで下限しきい値を自動設定
        - 下限: T_low = Q1 - 1.5 * IQR（最小でも10.0）
        - 上限: 既存の self.sharpness_threshold_max（例: 5000.0）をそのまま使用
        """
        logger.info("画像統計情報の計算を開始...")

        # 統計情報を保持
        self.sharpness_values = sharpness_values

        if not self.sharpness_values:
            return

        vals = np.asarray(self.sharpness_values, dtype=float)

        # 参考情報として平均・標準偏差も出す（使わないがデバッグに有用）
        self.sharpness_mean = float(np.mean(vals))
        self.sharpness_std  = float(np.std(vals))

        # IQR系統計
        q1 = float(np.percentile(vals, 25))
        q3 = float(np.percentile(vals, 75))
        iqr = q3 - q1
        median = float(np.median(vals))

        logger.info(
            f"鮮明度統計: 中央値={median:.2f}, Q1={q1:.2f}, Q3={q3:.2f}, IQR={iqr:.2f}, "
            f"平均={self.sharpness_mean:.2f}, 標準偏差={self.sharpness_std:.2f}, 枚数={len(vals)}"
        )

        # ===== 下限しきい値（IQRベース）=====
        if self.sharpness_threshold_min is None:
            if len(vals) >= 5:
                # 通常: IQRルール（静的係数を使用）
                #IQR(Interquartile Range)
                t_low = q1 - self.iqr_multFiplier * iqr
                # IQR=0 などで全体がほぼ同値の場合は分位点にフォールバック
                # 10%分位点を下限にする
                if iqr == 0.0:
                    t_low = float(np.percentile(vals, 10))
            else:
                # データが少ない場合は MAD ベースにフォールバック
                # MAD: 中央値からの絶対偏差の中央値(Median Absolute Deviation)
                mad = float(np.median(np.abs(vals - median)))
                if mad > 0:
                    t_low = median - 2.0 * 1.4826 * mad
                else:
                    # さらに全一致に近い場合の最終フォールバック
                    t_low = 0.8 * median

            # 最低下限は 10.0 に張る
            self.sharpness_threshold_min = max(10.0, float(t_low))

            logger.info(
                f"自動設定された鮮明度閾値下限(IQRベース): {self.sharpness_threshold_min:.2f} "
                f"(Q1={q1:.2f}, IQR={iqr:.2f}, 係数={self.iqr_multiplier})"
            )

        # 上限は既存値（例: 5000.0）をそのまま使用
        logger.info(f"鮮明度閾値上限(固定): {self.sharpness_threshold_max:.2f}")
    
    # ===== 動的IQR係数計算メソッド（コメントアウト）=====
    
    # def calculate_dynamic_iqr_multiplier(self, iqr: float, q1: float, q3: float) -> float:
    #     """
    #     データの特性に基づいてIQR係数を動的に計算
    #     
    #     Args:
    #         iqr: 四分位範囲
    #         q1: 第1四分位数
    #         q3: 第3四分位数
    #         
    #     Returns:
    #         float: 動的に計算されたIQR係数
    #     """
    #     # IQRが小さい場合（データが均一）
    #     if iqr < 20:
    #         return 1.0  # 緩い判定
    #     
    #     # IQRが中程度の場合
    #     elif iqr < 50:
    #         return 1.2  # 標準的な判定
    #     
    #     # IQRが大きい場合（データがばらついている）
    #     else:
    #         return 1.5  # 厳しい判定
    
    # def calculate_distribution_based_multiplier(self, vals: np.ndarray, q1: float, q3: float, median: float) -> float:
    #     """
    #     分布の形状に基づいてIQR係数を調整
    #     
    #     Args:
    #         vals: 鮮明度値の配列
    #         q1: 第1四分位数
    #         q3: 第3四分位数
    #         median: 中央値
    #         
    #     Returns:
    #         float: 調整されたIQR係数
    #     """
    #     # 歪度を計算（分布の非対称性）
    #     skewness = self.calculate_skewness(vals)
    #     
    #     # 正規分布からの逸脱度を計算
    #     normality_score = self.calculate_normality_score(vals)
    #     
    #     # 分布に基づいて係数を調整
    #     if abs(skewness) > 1.0:  # 強い歪み
    #         if skewness > 0:  # 右に歪んでいる（高鮮明度が多い）
    #             return 1.8  # より厳しい判定
    #         else:  # 左に歪んでいる（低鮮明度が多い）
    #             return 1.2  # より緩い判定
    #     
    #     elif normality_score > 0.8:  # 正規分布に近い
    #         return 1.5  # 標準的な判定
    #     
    #     else:  # その他の分布
    #         return 1.3  # 中間的な判定
    
    # def calculate_sample_size_based_multiplier(self, n: int, iqr: float) -> float:
    #     """
    #     サンプルサイズに基づいてIQR係数を調整
    #     
    #     Args:
    #         n: サンプルサイズ
    #         iqr: 四分位範囲
    #         
    #     Returns:
    #         float: 調整されたIQR係数
    #     """
    #     if n < 10:
    #         # サンプルが少ない場合は保守的に
    #         return 1.0
    #     
    #     elif n < 30:
    #         # 中程度のサンプルサイズ
    #         return 1.2
    #     
    #     elif n < 100:
    #         # 十分なサンプルサイズ
    #         return 1.5
    #     
    #     else:
    #         # 大量のサンプル
    #         return 1.7
    
    # def calculate_outlier_robust_multiplier(self, vals: np.ndarray, q1: float, q3: float) -> float:
    #     """
    #     外れ値の影響を考慮してIQR係数を調整
    #     
    #     Args:
    #         vals: 鮮明度値の配列
    #         q1: 第1四分位数
    #         q3: 第3四分位数
    #         
    #     Returns:
    #         float: 外れ値に頑健なIQR係数
    #     """
    #     # 外れ値の割合を計算
    #     outlier_ratio = self.calculate_outlier_ratio(vals, q1, q3)
    #     
    #     if outlier_ratio > 0.1:  # 外れ値が10%以上
    #         return 2.0  # より保守的な判定
    #     
    #     elif outlier_ratio > 0.05:  # 外れ値が5%以上
    #         return 1.7  # やや保守的な判定
    #     
    #     else:  # 外れ値が少ない
    #         return 1.5  # 標準的な判定
    
    # def calculate_final_iqr_multiplier(self, vals: np.ndarray, q1: float, q3: float, 
    #                                   iqr: float, median: float) -> float:
    #     """
    #     複数の要因を組み合わせて最終的なIQR係数を計算
    #     
    #     Args:
    #         vals: 鮮明度値の配列
    #         q1: 第1四分位数
    #         q3: 第3四分位数
    #         iqr: 四分位範囲
    #         median: 中央値
    #         
    #     Returns:
    #         float: 最終的なIQR係数
    #     """
    #     # 各要因の係数を計算
    #     iqr_based = self.calculate_dynamic_iqr_multiplier(iqr, q1, q3)
    #     distribution_based = self.calculate_distribution_based_multiplier(vals, q1, q3, median)
    #     sample_based = self.calculate_sample_size_based_multiplier(len(vals), iqr)
    #     outlier_based = self.calculate_outlier_robust_multiplier(vals, q1, q3)
    #     
    #     # 重み付き平均で最終係数を決定
    #     weights = [0.3, 0.3, 0.2, 0.2]  # 各要因の重み
    #     final_multiplier = (
    #         iqr_based * weights[0] +
    #         distribution_based * weights[1] +
    #         sample_based * weights[2] +
    #         outlier_based * weights[3]
    #     )
    #     
    #     # 係数の範囲を制限（0.5 ～ 2.5）
    #     final_multiplier = max(0.5, min(2.5, final_multiplier))
    #     
    #     return final_multiplier
    
    # 不鮮明画像検出（IQRベースの下限・固定上限でスクリーニング）
    def screen_image_quality(
        self,
        image_paths: List[str],
        images: List[np.ndarray],
        sharpness_values: List[float]
    ) -> List[str]:
        """
        不鮮明画像検出（IQRベースの下限・固定上限でスクリーニング）
        - 下限: calculate_image_statistics で設定された T_low（= Q1 - 1.5*IQR, 最小10）
        - 上限: self.sharpness_threshold_max（例: 5000.0）
        """
        logger.info("品質スクリーニングを開始...")

        sharp_images = []
        for img_path, sharpness in zip(image_paths, sharpness_values):
            # 上限（ノイズ過多）チェック：内視鏡ではほぼ出ない想定だが念のため
            if sharpness > self.sharpness_threshold_max:
                logger.warning(
                    f"ノイズ画像を除外: {os.path.basename(img_path)} (鮮明度: {sharpness:.2f})"
                )
                continue

            # 下限（ボケ）チェック：IQRベースの T_low
            if self.sharpness_threshold_min is not None and sharpness < self.sharpness_threshold_min:
                logger.info(
                    f"× 鮮明度基準未満: {os.path.basename(img_path)} ({sharpness:.2f})"
                )
                continue

            sharp_images.append(img_path)
            logger.info(f"⚪ 鮮明度基準OK: {os.path.basename(img_path)} ({sharpness:.2f})")

        logger.info(
            f"鮮明度フィルタリング完了: {len(sharp_images)}/{len(image_paths)} 画像が選択"
        )
        return sharp_images
    
    def delete_unselected_images(self, all_image_paths: List[str], selected_paths: List[str]) -> None:
        """
        選択されなかった画像を削除
        
        Args:
            all_image_paths: 元の全画像パスのリスト
            selected_paths: 選択された画像パスのリスト
        """
        logger.info("選択されなかった画像の削除を開始...")
        
        deleted_count = 0
        for img_path in all_image_paths:
            if img_path not in selected_paths:
                try:
                    os.remove(img_path)
                    deleted_count += 1
                    logger.info(f"🗑️ 削除: {os.path.basename(img_path)}")
                except Exception as e:
                    logger.error(f"画像削除エラー {img_path}: {e}")
                    continue
        
        logger.info(f"削除完了: {deleted_count} 画像を削除")
    
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
    
    def delete_original_images_after_rename(self, original_paths: List[str], renamed_paths: List[str]) -> None:
        """
        リネーム後に元画像を削除（名前が同じ場合は削除しない）
        
        Args:
            original_paths: 元の画像パスのリスト
            renamed_paths: リネーム後の画像パスのリスト
        """
        logger.info("リネーム後の元画像削除を開始...")
        
        deleted_count = 0
        for original_path in original_paths:
            original_filename = os.path.basename(original_path)
            
            # リネーム後のファイル名と比較
            should_delete = True
            for renamed_path in renamed_paths:
                renamed_filename = os.path.basename(renamed_path)
                if original_filename == renamed_filename:
                    # 名前が同じ場合は削除しない
                    should_delete = False
                    logger.info(f"🔒 保持: {original_filename} (名前が同じ)")
                    break
            
            if should_delete:
                try:
                    os.remove(original_path)
                    deleted_count += 1
                    logger.info(f"🗑️ 削除: {original_filename}")
                except Exception as e:
                    logger.error(f"元画像削除エラー {original_path}: {e}")
                    continue
        
        logger.info(f"元画像削除完了: {deleted_count} 画像を削除")
    
    def process(self) -> List[str]:
        """
        メイン処理：鮮明度フィルタリング → 選択されなかった画像削除 → リネーム → 元画像削除
        
        Returns:
            List[str]: 最終的な画像パスのリスト
        """
        logger.info("画像鮮明度スクリーニング処理を開始...")
        
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
        
        # 1. 画像統計情報の計算とIQRベース自動閾値設定
        self.calculate_image_statistics(sharpness_values)
        
        # 2. 不鮮明画像検出（IQRベース）
        sharp_images = self.screen_image_quality(valid_paths, images, sharpness_values)
        
        # 3. 選択されなかった画像を削除
        self.delete_unselected_images(image_paths, sharp_images)
        
        # 4. リネーム
        final_images = self.rename_images(sharp_images)
        
        # 5. リネーム後に元画像を削除（名前が同じ場合は削除しない）
        self.delete_original_images_after_rename(sharp_images, final_images)
        
        logger.info("画像鮮明度スクリーニング処理完了!")
        logger.info(f"最終結果: {len(final_images)} 画像")
        
        return final_images

def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description='画像鮮明度スクリーニングシステム（IQRベース、入力・出力同一ディレクトリ）')
    parser.add_argument('input_dir', help='入力画像ディレクトリ')
    parser.add_argument('output_dir', help='出力画像ディレクトリ（入力と同じディレクトリ）')
    parser.add_argument('--sharpness_min', type=float, default=None, 
                       help='鮮明度閾値の下限（指定しない場合はIQRベースで自動設定）')
    parser.add_argument('--sharpness_max', type=float, default=5000.0, 
                       help='鮮明度閾値の上限（デフォルト: 5000.0）')

    args = parser.parse_args()
    
    # 画像鮮明度スクリーニングを実行
    screener = SharpnessScreener(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        sharpness_threshold_min=args.sharpness_min,
        sharpness_threshold_max=args.sharpness_max
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
