# 🐦 バードカメラ Linux (vogel-kamera-linux)

**言語 / Languages / Sprachen:** [🇬🇧 English](README.md) | [🇩🇪 Deutsch](README.de.md) | [🇯🇵 日本語](README.ja.md)

> **このプロジェクトのドキュメントはドイツ語で管理されています。** このページは日本語の短い概要です。
> 詳細は下記のリンクをブラウザの翻訳機能でご覧ください。

## 概要

**Raspberry Pi 5** と **AI HAT+ (Hailo-8)** を使った野鳥観察カメラです。NPU 上の YOLOv8 モデルが
鳥(または人、犬、猫)を検出すると、自動的に録画を開始します。操作はすべてブラウザの Web
インターフェースから行います。

- 検出時の**自動録画**、または 10 秒から 10 分までの手動録画
- 音声付きで**最大 4K** の動画、2 種類のスローモーション、音声のみの録音
- パスワード + TOTP でログインする HTTPS の **Web インターフェース**(再生、ダウンロード、削除)
- rsync/SSH による他のマシンへの**自動転送**
- Bluetooth による**モバイルバッテリー監視**(残量警告と安全なシャットダウン)
- Prometheus と Grafana による**モニタリング**(オプション、Pi 上で動作)
- Ansible と Docker による**コマンド一つでのデプロイ**

## クイックスタート

```bash
git clone https://github.com/kamera-linux/vogel-kamera-linux.git
cd vogel-kamera-linux
cp ansible/.env.example ansible/.env   # Pi のアドレス、ユーザー、SSH 鍵を設定
./ansible/build_and_deploy.sh --install
# その後 https://<pi-host>:8443/ を開く
```

## ドキュメント(ドイツ語)

| 内容 | 場所 |
|------|------|
| 概要、機能、クイックスタート | [README.md](../../README.md) |
| 手順ガイド | [Wiki](https://github.com/kamera-linux/vogel-kamera-linux/wiki) |
| アーキテクチャ | [ARCHITEKTUR.md](../ARCHITEKTUR.md) |
| セキュリティ | [SECURITY.md](../SECURITY.md) |
| Grafana によるモニタリング | [monitoring/README.md](../../monitoring/README.md) |
| バージョンごとの変更点 | [CHANGELOG.md](../../CHANGELOG.md) · [Releases](https://github.com/kamera-linux/vogel-kamera-linux/releases) |

質問は [Discussions](https://github.com/kamera-linux/vogel-kamera-linux/discussions) で英語でも受け付けています。
