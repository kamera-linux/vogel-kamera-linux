# 🐦 バードカメラ Linux

**言語 / Languages / Sprachen:** [🇬🇧 English](README.md) | [🇩🇪 Deutsch](README.de.md) | [🇯🇵 日本語](README.ja.md)

![バードカメラ Linux バナー](../pictures/Vogelhaus-Raspberry-Pi-Backround.jpg)

## リリース v2.0.1 — 概要

- バージョン: v2.0.1
- 主要な更新: Cinema 4K (4096x2160 @ 25fps)、AI-HAD オーディオモード、CLI パラメータとモードの追加（normal, slowmo, 4k, ai-had）、SSH ログ追跡の堅牢化、変換完了後の自動ビデオ同期。
- バグ修正: ISO 週番号 (%V) の修正、パス抽出の不具合修正、自動 SSH 再接続、`pipefail` によるスクリプト終了の回避。

詳細は次の完全なリリースノートを参照してください: [`releases/RELEASE_NOTES_v2.0.1.md`](../../releases/RELEASE_NOTES_v2.0.1.md)

[![Version](https://img.shields.io/badge/Version-v2.0.0-brightgreen)](https://github.com/kamera-linux/vogel-kamera-linux/releases/tag/v2.0.0)
[![Trixie Support](https://img.shields.io/badge/Debian-Trixie%20(13)-blue)](../TRIXIE-MIGRATION.md)
[![GitHub Issues](https://img.shields.io/github/issues/kamera-linux/vogel-kamera-linux)](https://github.com/kamera-linux/vogel-kamera-linux/issues)
[![GitHub PRs](https://img.shields.io/github/issues-pr/kamera-linux/vogel-kamera-linux)](https://github.com/kamera-linux/vogel-kamera-linux/pulls)
[![License](https://img.shields.io/github/license/kamera-linux/vogel-kamera-linux)](../../LICENSE)

> ⚠️ **Raspberry Pi OS Trixie (Debian 13):** このバージョンは **Trixie** に最適化されています。  
> 📘 **Bookworm (Debian 12) の場合:** [bookworm-legacy ブランチ (v1.2.x)](https://github.com/kamera-linux/vogel-kamera-linux/tree/bookworm-legacy) をご使用ください  
> 📖 **移行ガイド:** [TRIXIE-MIGRATION.md](../TRIXIE-MIGRATION.md)

![完全なバードカメラシステム](../../assets/vogelhaus-kamera-komplett.png)

**🐦 AI を活用した物体検出機能を備えたプロフェッショナル野鳥観察システム**

`vogel-kamera-linux` は、Raspberry Pi 5 カメラを使用したリモートバードハウス監視用の**オープンソースプロジェクト**です。このシステムは、高解像度ビデオ/オーディオ録画と **YOLOv8 AI 検出**を組み合わせて、自動野鳥認識と録画を実現します。

### 🚀 クイックスタート
```bash
# 推奨: 統合カメラモニター（Raspberry Pi 上で直接実行）
python3 raspberry-pi-scripts/unified-camera-monitor.py --slowmo

# またはクライアント PC からラッパー経由で実行
cd auto-start-kamera
./start-unified-monitoring.sh slowmo

# レガシー: 古いリモートコントロールスクリプト（legacy/README.md を参照）
python legacy/ai-had-kamera-remote-param-vogel-libcamera-single-AI-Modul.py \
    --duration 5 --width 1920 --height 1080 --ai-modul on
```

> 📺 **ライブデモ:** [YouTube チャンネル](https://www.youtube.com/@vogel-kamera-linux) - vogel-kamera-linux システムからの実際の録画！

## 📖 概要

**vogel-kamera-linux** は、**Raspberry Pi 5** と Python 3.11+ 用に開発された、自然観察用の完全なリモートカメラシステムです。このプロジェクトは、最新のカメラハードウェア（IMX708）と高度な AI 物体検出（YOLOv8）を組み合わせて、自動野鳥認識を実現します。

**🎯 主な用途:** 野鳥検出時の自動録画を備えたリモートバードハウス監視、HD ビデオ（最大 4K）、スローモーション（120fps）、USB マイクによる同期オーディオ録音を含みます。

### 🎬 YouTube チャンネル & サンプル録画

[![YouTube Channel](https://img.shields.io/badge/📺_YouTube_チャンネル-FF0000?style=for-the-badge&logo=youtube&logoColor=white)](https://www.youtube.com/@vogel-kamera-linux)

**vogel-kamera-linux システムからの実際の録画！** ライブ野鳥検出、スローモーション録画、バードハウスからの 4K ビデオでカメラの動作をご覧ください。

**📱 モバイルアクセス用 QR コード:**

![YouTube QR Code](../../assets/qr-youtube-channel.png)

## ✨ 機能

- 🎥 **高解像度ビデオ録画**（最大 4K）
- 🎵 **同期オーディオ録音**（USB マイク経由）
- 🤖 **AI 物体検出**（YOLOv8 とカスタム野鳥種モデル）
- 🎯 **自動トリガーシステム**（自動野鳥検出）*（v1.2.0 の新機能）*
- 📺 **プレビューストリーム**（RTSP）によるライブ監視 *（v1.2.0 の新機能）*
- 🌐 **ネットワーク診断**（パフォーマンス分析用）*（v1.2.0 の新機能）*
- 📊 **システム監視**（CPU 負荷と温度監視）*（v1.1.9 以降）*
- ⚡ **パフォーマンス最適化**（各種録画モード用）*（v1.1.9 以降）*
- 🌐 **リモートコントロール**（SSH 経由）
- 📁 **自動ファイル整理**（年/週別）
- ⚙️ **柔軟な設定**（.env ファイル経由）
- 📊 **進行状況表示**（録画中）
- 🔄 **自動ビデオ/オーディオ同期**
- 📱 **YouTube 統合**（モバイルユーザー向け QR コード）
- 🔧 **簡単インストール**（config/requirements.txt 付き）
- ✅ **自動設定検証**
- 🎯 **カスタム AI モデル**（特定の野鳥種用にトレーニング可能）

## 📸 ハードウェアギャラリー

**モジュラーカメラソリューション:**
![シングルバードハウス](../../assets/vogelhaus-kamera-solo.png)
*最適な録画のための柔軟な配置*

**ライブ録画 & コミュニティ:**
![YouTube チャンネル印象](../../assets/Youtube-Kanal.png) 
*YouTube での実際の野鳥観察*

> 💡 **3D 構造ファイル利用可能！** 再構築用のすべての CAD ファイルは [`3d-konstruktion/`](../../3d-konstruktion/) ディレクトリにあります

## 🛠️ 要件

### ハードウェア
- カメラモジュール付き Raspberry Pi 5（推奨: IMX708 Wide）
- オーディオ録音用 USB マイク
- 安定したネットワーク接続（ギガビット LAN 推奨）

### ソフトウェア（Raspberry Pi）
- **Raspberry Pi OS Trixie (Debian 13)** - このバージョンには必須
- Python 3.13+
- rpicam-apps v1.9.1+
- FFmpeg 7.1.2+
- SSH アクセス設定済み

> ⚠️ **Trixie 固有:** このバージョンはプレビューストリームに TCP Watchdog を使用（FFmpeg 7.1.2 互換）  
> 📘 **Bookworm ユーザー:** [bookworm-legacy ブランチ (v1.2.x)](https://github.com/kamera-linux/vogel-kamera-linux/tree/bookworm-legacy) を使用してください

### ソフトウェア（クライアント PC）
- Python 3.8+
- SSH クライアント
- 仮想環境（推奨）

## 🚀 クイックスタート

### 1. Raspberry Pi へのインストール

**自動セットアップ（推奨）:**
```bash
# Raspberry Pi でセットアップスクリプトを実行
curl -sSL https://raw.githubusercontent.com/kamera-linux/vogel-kamera-linux/main/raspberry-pi-scripts/setup-unified-monitor.sh | bash

# または手動で:
git clone https://github.com/kamera-linux/vogel-kamera-linux.git
cd vogel-kamera-linux
bash raspberry-pi-scripts/setup-unified-monitor.sh
```

**手動インストール:**
```bash
# Raspberry Pi で - Python パッケージをインストール（apt、pip ではありません！）
sudo apt-get update
sudo apt-get install -y python3-picamera2 python3-opencv python3-numpy python3-libcamera

# YOLOv8 をインストール
pip install ultralytics --break-system-packages

# カメラツールを確認
rpicam-hello --version  # v1.9.1+ である必要があります
ffmpeg -version         # 7.1.2+ である必要があります
```

### 2. クライアント PC の設定
```bash
# リポジトリをクローン
git clone https://github.com/kamera-linux/vogel-kamera-linux.git
cd vogel-kamera-linux

# 仮想環境を作成（推奨）
python3 -m venv venv
source venv/bin/activate

# 依存関係をインストール
pip install -r config/requirements.txt

# SSH アクセスを設定
cp python-skripte/.env.example python-skripte/.env
nano python-skripte/.env

# 設定をテスト
python python-skripte/config.py
```

### 3. 最初の録画
```bash
# 標準モード（4K @ 30fps、60秒録画）
python3 raspberry-pi-scripts/unified-camera-monitor.py

# スローモーションモード（1536x864 @ 120fps）
python3 raspberry-pi-scripts/unified-camera-monitor.py --slowmo

# クライアント PC からラッパー経由で実行
cd auto-start-kamera
./start-unified-monitoring.sh slowmo
```

## 🎯 統合カメラモニターシステム (v2.0)

**新機能！** SSH オーバーヘッドなしの統合カメラプロセス - Raspberry Pi 上で直接実行されます。

### ✨ 利点
- ✅ **カメラ競合なし** - すべてを単一プロセスで処理
- ✅ **高速応答** - SSH/ネットワークレイテンシなし
- ✅ **簡単操作** - .env ファイルの代わりに CLI パラメータ
- ✅ **ライブ監視** - 30秒ごとのハートビート、5分ごとのトラフィックライト付きステータス
- ✅ **自動シャットダウン** - 危険温度（>75°C）で停止

### ⚙️ 利用可能なパラメータ

| パラメータ | 説明 | デフォルト | 例 |
|-----------|------|----------|-----|
| `--camera` | カメラ番号 | 0 | `--camera 1` |
| `--threshold` | AI 検出閾値 | 0.4 | `--threshold 0.3` |
| `--cooldown` | 録画間のクールダウン（秒） | 15 | `--cooldown 10` |
| `--trigger-duration` | トリガーの最小期間（秒） | 1.0 | `--trigger-duration 0.5` |
| `--video-path` | ビデオのベースパス | `/home/roimme/Videos/Vogelhaus` | `--video-path /mnt/nas/birds` |
| `--model` | YOLO モデルへのパス | yolov8n.pt | `--model custom.pt` |
| `--preview-fps` | プレビュー FPS | 6 | `--preview-fps 10` |
| `--recording-width` | 録画幅（px） | 4096 | `--recording-width 1920` |
| `--recording-height` | 録画高さ（px） | 2160 | `--recording-height 1080` |
| `--recording-fps` | 録画 FPS | 30 | `--recording-fps 60` |
| `--recording-duration` | 録画期間（秒） | 60 | `--recording-duration 120` |
| `--slowmo` | スローモーションモードを有効化 | - | `--slowmo` |
| `--debug` | デバッグモードを有効化 | - | `--debug` |

### 📊 ライブ監視出力

```
======================================================================
🐦 統合カメラモニター - Vogel-Kamera-Linux
======================================================================

======================================================================
📊 初期ステータスレポート
======================================================================

2025-11-11 19:27:14 - INFO - [✓] モニターアクティブ - 354 フレーム処理済み
2025-11-11 19:29:12 - INFO - ステータス: 0時間5分 | 録画: 0 | フレーム: 584 | 温度: 🟢51.0°C | 負荷: 🟡1.72 | RAM: 🟢7% | ディスク: 🟢215.3GB
```

**トラフィックライトしきい値:**
- **温度:** 🟢 <55°C | 🟡 55-65°C | 🔴 >65°C | ⛔ 停止 >75°C
- **CPU 負荷:** 🟢 <1.0 | 🟡 1.0-2.0 | 🔴 >2.0
- **RAM:** 🟢 <75% | 🟡 75-90% | 🔴 >90%
- **ディスク:** 🟢 <90% | 🟡 90-95% | 🔴 >95%

## 📝 レガシー: リモートコントロールスクリプト

> ⚠️ **これらのスクリプトは非推奨です！** 代わりに**統合カメラモニターシステム**を使用してください（上記参照）。
> 
> 古いスクリプトは `legacy/` に移動されました。詳細: [`legacy/README.md`](../../legacy/README.md)

## 🤖 AI 物体検出 & 野鳥種モデル

### すぐに利用可能: 標準物体検出
```bash
# 一般的な野鳥検出を備えた YOLOv8
python3 raspberry-pi-scripts/unified-camera-monitor.py --model yolov8n.pt
```

### 高度: カスタム野鳥種モデルのトレーニング
システムは特定の野鳥種用のカスタム AI モデルのトレーニングをサポートしています:

🎯 **一般的なヨーロッパの庭鳥:** クロウタドリ、アオガラ、シジュウカラ、コマドリ、アトリ...

📋 **完全ガイド:** [`docs/ANLEITUNG-EIGENES-AI-MODELL.md`](../ANLEITUNG-EIGENES-AI-MODELL.md)（ドイツ語）

🛠️ **トレーニングツール:** [`ai-training-tools/`](../../ai-training-tools/) - カスタムモデル用の完全なツールキット

## 📄 ライセンス

詳細については [LICENSE](../../LICENSE) ファイルを参照してください。

## 🤝 貢献

1. リポジトリをフォーク
2. フィーチャーブランチを作成
3. 変更をコミット
4. プルリクエストを作成

## 👥 コミュニティ & ディスカッション

[![GitHub Discussions](https://img.shields.io/github/discussions/kamera-linux/vogel-kamera-linux)](https://github.com/kamera-linux/vogel-kamera-linux/discussions)

他のユーザーと交流:
- 🙋 **質問する** インストールと設定について  
- 💡 **アイデアを共有** 新機能について
- 📸 **録画を見せる** あなたのバードハウスから
- 🔧 **ハードウェアのヒントを議論**

## 📞 サポート

質問や問題がある場合:
- 💬 **ディスカッションを開始** [GitHub Discussions](https://github.com/kamera-linux/vogel-kamera-linux/discussions) で
- 🐛 **バグを報告** [GitHub Issues](https://github.com/kamera-linux/vogel-kamera-linux/issues) 経由で

## 📚 ドキュメント

### メインドキュメント
- **[docs/CHANGELOG.md](../CHANGELOG.md)** - 完全なバージョン履歴
- **[docs/ARCHITEKTUR.md](../ARCHITEKTUR.md)** - 🏗️ **v1.2.0 の新機能！** Mermaid 図を含む詳細なシステムアーキテクチャ
- **[docs/PROJEKT-REORGANISATION.md](../PROJEKT-REORGANISATION.md)** - プロジェクト再編成の履歴

### 自動トリガーシステム *(v1.2.0)*
- **[kamera-auto-trigger/README.md](../../kamera-auto-trigger/README.md)** - メイン自動トリガードキュメント
- **[kamera-auto-trigger/docs/QUICKSTART-AUTO-TRIGGER.md](../../kamera-auto-trigger/docs/QUICKSTART-AUTO-TRIGGER.md)** - 3分クイックスタート

### AI & トレーニング
- **[docs/AI-MODELLE-VOGELARTEN.md](../AI-MODELLE-VOGELARTEN.md)** - AI モデルドキュメント
- **[docs/ANLEITUNG-EIGENES-AI-MODELL.md](../ANLEITUNG-EIGENES-AI-MODELL.md)** - カスタムモデルのトレーニング

### セキュリティ & 開発
- **[docs/SECURITY.md](../SECURITY.md)** - セキュリティガイドライン
- **[git-automation/README.md](../../git-automation/README.md)** - Git 自動化ドキュメント

## 📋 変更履歴

すべての変更は **[docs/CHANGELOG.md](../CHANGELOG.md)** に文書化されています。

### 🆕 v2.0.0 の新機能（2025年11月）
- 🎯 **統合カメラモニター:** SSH オーバーヘッドなしの単一プロセスシステム
- 🚦 **トラフィックライトシステム:** リアルタイム健全性監視（CPU、RAM、ディスク、温度）
- 🔒 **自動シャットダウン:** 危険温度 >75°C で緊急停止
- ⏱️ **設定可能な録画:** 60秒デフォルト、`--recording-duration` で調整可能
- 📊 **ライブフィードバック:** 30秒ごとのハートビート、5分ごとのステータス
- 📦 **レガシーアーカイブ:** 古いリモートスクリプトを `legacy/` に移動
- 🌐 **多言語ドキュメント:** 英語、ドイツ語、日本語の README
- 🔧 **セットアップスクリプト:** 自動化された Raspberry Pi インストール

### 📡 v1.3.0 の Trixie サポート（2025年11月）
- 📡 **TCP Watchdog システム:** 堅牢なプレビューストリーム管理（FFmpeg 7.1.2 互換）
- 🎯 **オンデマンドストリームモード:** 競合のないデュアルカメラ動作
- 🐍 **PEP 668 準拠:** pip の代わりに apt 経由の Python パッケージ

### 🎬 以前のリリース
- **v1.3.1:** ライブ進行状況バー、TCP watchdog 強化
- **v1.1.9:** システム監視、パフォーマンス最適化
- **v1.1.8:** Bird-species モデル、3D 構造ファイル
- **v1.1.0:** YouTube 統合、中央設定システム

## 🔖 バージョン

- **現在のバージョン:** v2.0.0
- **ブランチ:** `main`（Trixie）
- **レガシーブランチ:** `bookworm-legacy`（Debian 12 用 v1.2.x）
- **すべてのリリース:** [GitHub Releases](https://github.com/kamera-linux/vogel-kamera-linux/releases) | [Tags](https://github.com/kamera-linux/vogel-kamera-linux/tags)

---

**野鳥愛好家とオープンソース愛好家のために ❤️ で作成**
