# Portable Linux CI — GitHub Actions / Mac 不使用

Aeterna Genesis の検証は GitHub Actions を前提にしない。CI は OCI コンテナとして固定し、Linux 上の
Docker または Podman で同一条件を再現する。Mac 固有のランナー、Xcode、Apple Silicon 固有処理は使わない。

## 目的

- Python / NumPy / SciPy の計算環境を `ci/Dockerfile` に固定する。
- Autopilot のキューだけでなく、**実際の 2D と local-3D 計算**をスモーク検証する。
- テスト中に生成される Room、SQLite、台帳は一時コピーへ隔離し、作業ツリーを汚さない。
- `rooms/official/` のハッシュが計算前後で変化していないことを検査する。
- ログと `report.json` を `ci-artifacts/` に保存する。
- 同じコンテナをローカル Linux、NAS、オンプレ、任意の Linux VM で使う。

## 最短実行

Linux 上でリポジトリのルートから:

```bash
bash ci/run-container.sh autopilot
```

Docker がなければ Podman を自動検出する。

成果物:

```text
ci-artifacts/
├─ latest.json
└─ YYYYMMDDTHHMMSSZ/
   ├─ report.json
   └─ logs/
```

## プロファイル

### `autopilot`

```bash
bash ci/run-container.sh autopilot
```

実行内容:

1. 追加Pythonコードの構文コンパイル
2. Autopilotの単体テスト
3. JSON Schema / registry 検証
4. 隔離された一時リポジトリで実計算
   - 2D screen
   - local 3D
   - 3D `field.json` の生成
   - 非公式候補Roomの生成
   - `rooms/official/` 無変更確認

### `quick`

```bash
bash ci/run-container.sh quick
```

`autopilot` に加え、Observatory のTypeScript型検査と本番ビルドを行う。

### `full`

```bash
bash ci/run-container.sh full
```

`tests/` 全体とObservatoryビルドを行う。研究実験群すべての長時間回帰は、通常のPR検証とは分離し、
必要なキャンペーンだけAutopilotへ投入する。

## コンテナを使わずLinux環境で直接実行

Python依存とNode.js依存を導入済みなら:

```bash
python ci/run_ci.py autopilot
python ci/run_ci.py quick
python ci/run_ci.py full
```

ただし、環境差を減らすため通常はコンテナ実行を正とする。

## クラウド / 常設Linux VM

Ubuntu / Debian系などのLinux VMにGitとDockerまたはPodmanを入れ、次を実行する:

```bash
sudo mkdir -p /var/lib/aeterna-ci
sudo AETERNA_REF=main \
     AETERNA_CI_PROFILE=autopilot \
     bash ci/cloud-runner.sh
```

別ブランチの検証:

```bash
sudo AETERNA_REF=agent/genesis-autopilot \
     AETERNA_CI_PROFILE=quick \
     bash ci/cloud-runner.sh
```

`ci/cloud-runner.sh` は以下を行う:

1. リポジトリを取得または更新
2. 指定refへ強制同期
3. Linuxコンテナをビルド
4. CIプロファイルを実行
5. `/var/lib/aeterna-ci/artifacts` にログとJSON結果を保存
6. `flock` があれば重複実行を防止

cronまたはsystemd timerから同じスクリプトを呼べる。CIサービス固有APIへの依存はない。

## 計算資源の目安

- `autopilot`: 2 CPU / 4 GB RAM
- `quick`: 2 CPU / 4–6 GB RAM
- `full`: 4 CPU / 8 GB RAMを推奨
- 本番 `full-3d` キャンペーン: ジョブ数と格子に応じて個別にCPU/RAM上限を設定

ローカルの既定値は `CI_CPUS=2`, `CI_MEMORY=4g`。変更例:

```bash
CI_CPUS=4 CI_MEMORY=8g bash ci/run-container.sh full
```

## 科学的完全性

CIの3Dスモークは表示だけの偽物ではない。`genesis.runners.recorded_runner` が既存の参照stepperと
測定関数を呼び、時刻0から計算する。記録器は計算済み場を間引いて保存するだけで、物理場へ戻さない。
単体テストでは通常Runnerとの最終チェックサム一致も確認する。

CIは候補Roomまでしか作れず、`rooms/official/` への昇格処理を持たない。
