#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
フレーム最適化システム設定ファイル
"""

# デフォルト設定
DEFAULT_CONFIG = {
    # 鮮明度フィルタリング設定
    'sharpness': {
        'threshold': 100.0,  # ラプラシアンの分散閾値
        'min_threshold': 50.0,  # 最小閾値
        'max_threshold': 500.0,  # 最大閾値
    },
    
    # 類似度フィルタリング設定
    'similarity': {
        'threshold': 0.85,  # SSIM閾値（0-1）
        'min_threshold': 0.70,  # 最小閾値
        'max_threshold': 0.95,  # 最大閾値
    },
    
    # 画像処理設定
    'image': {
        'supported_formats': ['.jpeg', '.jpg', '.png', '.bmp', '.tiff'],
        'max_image_size': 4096,  # 最大画像サイズ
        'quality_threshold': 0.8,  # 画像品質閾値
    },
    
    # 出力設定
    'output': {
        'filename_prefix': 'still_image_1_',
        'filename_format': '{prefix}{index:04d}{extension}',
        'overwrite_existing': False,  # 既存ファイルの上書き
    },
    
    # ログ設定
    'logging': {
        'level': 'INFO',
        'format': '%(asctime)s - %(levelname)s - %(message)s',
        'file_output': False,
        'log_file': 'frame_optimizer.log',
    }
}

# 一般画像用の推奨設定
ENDOSCOPY_CONFIG = {
    'sharpness': {
        'threshold': 150.0,  # 一般画像は鮮明度が重要
        'min_threshold': 80.0,
        'max_threshold': 600.0,
    },
    
    'similarity': {
        'threshold': 0.80,  # 一般画像は類似度閾値を少し下げる
        'min_threshold': 0.65,
        'max_threshold': 0.90,
    },
    
    'image': {
        'supported_formats': ['.jpeg', '.jpg', '.png'],
        'max_image_size': 2048,  # 一般画像は通常小さい
        'quality_threshold': 0.85,
    },
    
    'output': {
        'filename_prefix': 'endoscope_frame_',
        'filename_format': '{prefix}{index:04d}{extension}',
        'overwrite_existing': False,
    }
}

# 設定を取得する関数
def get_config(config_type='default'):
    """
    設定を取得
    
    Args:
        config_type: 設定タイプ ('default' または 'endoscopy')
        
    Returns:
        dict: 設定辞書
    """
    if config_type == 'endoscopy':
        return ENDOSCOPY_CONFIG.copy()
    else:
        return DEFAULT_CONFIG.copy()

# 設定を検証する関数
def validate_config(config):
    """
    設定を検証
    
    Args:
        config: 設定辞書
        
    Returns:
        bool: 設定が有効かどうか
    """
    try:
        # 鮮明度設定の検証
        sharpness = config['sharpness']
        if not (sharpness['min_threshold'] <= sharpness['threshold'] <= sharpness['max_threshold']):
            return False
        
        # 類似度設定の検証
        similarity = config['similarity']
        if not (similarity['min_threshold'] <= similarity['threshold'] <= similarity['max_threshold']):
            return False
        
        # 画像設定の検証
        image = config['image']
        if image['max_image_size'] <= 0:
            return False
        
        return True
        
    except KeyError:
        return False

# 設定を表示する関数
def print_config(config, title="設定内容"):
    """
    設定を表示
    
    Args:
        config: 設定辞書
        title: 表示タイトル
    """
    print(f"\n=== {title} ===")
    
    print(f"鮮明度閾値: {config['sharpness']['threshold']}")
    print(f"類似度閾値: {config['similarity']['threshold']}")
    print(f"サポート形式: {', '.join(config['image']['supported_formats'])}")
    print(f"出力プレフィックス: {config['output']['filename_prefix']}")
    print(f"ログレベル: {config['logging']['level']}")
