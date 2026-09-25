# TREASURE_AUDIT — 2か月の自動研究の成果は宝か（P2・2026-09-25）

> 凍結点 `faac01d`（[`INVENTORY_2026-09.md`](INVENTORY_2026-09.md)）の上で、読み取りのみで監査した。研究データは何も動かしていない。
> 再現：
> - `python tools/audit/rooms_index.py --determinism 60 --keyframes`
> - `python tools/audit/xpattern_audit.py --seeds 20 --workers 3`
>
> 詳細：[`X_PATTERN_AUDIT.md`](X_PATTERN_AUDIT.md)。機械可読の結果は `audit/`。

## 1. このリポジトリが研究していること（1 枚で）

**完成形を置かず、一様＋ノイズと局所法則だけを t=0 から回し、どこまで「育つ」か**を、白（場と法則の組）ごとに測る。
どこで止まり、なぜ止まるかを正直に地図にするのが成果（[`WHITE_CEILINGS.md`](WHITE_CEILINGS.md)）。

| 白 | 到達（正直な天井） | 天井の理由 | 宝の度合い |
|---|---|---|---|
| g001 TDGL（緩和 GL クエンチ） | **L2**（渦） | 運動量が無いので動けない | 天井が確定済み。これ以上回しても新しい Level は出ない |
| damped GPE（e001–e003 ほか） | **L3**（自走する渦対）、3D の渦リング | 散逸のため長く持たない | 証拠庫の中核。3D の渦リング（e003）は水槽の第一候補 |
| g002 Boussinesq | **L3**（対流の循環） | 大域ロールなので局在しない | 3D 版あり |
| CGL | L1＋L2＋乱流運動 | 乱流は coherent でなく、個体化しない | — |
| Swift-Hohenberg | **L4-static**（自己修復する局在個体） | 変分なので動かない | 「個体」の最良の実例（局在の種は置いている） |
| Gray-Scott | **L7-partial**（自己複製） | 遺伝する内部自由度が無い | — |
| 三成分反応拡散 | 自走個体は **frontier** | 閉じ込めと自走が拮抗する（codimension≥2 の可能性） | **本当の最前線** |
| g003 Model H | L5 の共分化は frontier | 測定器が未収束 | — |

証拠庫 `experiments/`（55 件、E=24／V=8／S=7／F=12／N=4）と公式 Room 3 つ（g001 L2、g002 L1、g003 L2）は、この地図の根拠である。
**ここが一番の宝**であり、P3 でも一切動かさない。

## 2. 自動研究（2026-08-06 〜 09-25）が実際にやっていたこと

- 候補 Room 6,940 のうち **6,939 が g001 TDGL**。天井 L2 が既に確定している白である。
- そのうえ Room の条件は **37 通りしかない**。
  - 変わっていたのはノイズ振幅×クエンチ時間だけ。初期状態は常に一様＋ノイズ、相関長は常に 1.0。
  - 残りは seed 違いの繰り返しだった（2D 48² が 3,626、3D 20³ が 3,311）。
- Dream が 2D で探していた「つまみ」（拡散比、駆動強度、初期条件の型、相関長）は、Room には反映されていない。
  `genesis/runners/recorded_runner.run_recorded` が、ノイズ振幅とクエンチ時間しか読まないため。
  → Room の山は、Dream の探索結果を 3D で確かめたものではない。
- 候補の「candidate_level 3」（1,568 件）は測定値ではない。`candidate_level = reached_level + 1` という**目標ラベル**である（`genesis/runners/*runner.py`）。
- 見出しだった「名無し変化 X-…」は、延べ観測の 82% が通常のクエンチ物理（振幅の立ち上がり・渦の生成と消滅・対消滅）で、説明できないものは 0 件だった（[`X_PATTERN_AUDIT.md`](X_PATTERN_AUDIT.md)）。

**正直なまとめ**：2 か月・約 4,000 コミットの自動研究は、天井がわかっている白 1 つの、ごく狭い条件空間を繰り返し回していた。
新しい Level も、説明のつかない現象も出ていない。これは「失敗」ではなく**負の結果として有用**である。
TDGL の天井 L2 は、条件と seed を変えても動かないことが、約 7,000 run で裏づけられた。

## 3. 決定性（index-only にして失うものは無いか）

- 37 条件セル×次元を巡回して選んだ **60 Room を t=0 から再実行した**（50 セルを網羅）。
- `final_field_sha256` は **60/60 で一致**（numpy 2.4.6、Python 3.11.15）。
- → 生の field データは、`genesis.yaml` と seed から**再生成できる**。index-only にしても、再計算できないものは失わない。
- 限界：一致を確かめたのは同じ numpy 系列の中だけ。別の BLAS や FFT 環境でのビット一致は未確認（`numerical-portability` workflow の領分）。

## 4. 分類（`audit/candidates.jsonl`：1 Room 1 行・理由つき）

| 分類 | Room 数 | 現在のサイズ | 中身 |
|---|---:|---:|---:|
| **keep-full** | 272 | 104 MB | 下の内訳 |
| **distill** | 1,497 | 145 MB | L2 に達した seed 違いの重複 |
| **index-only** | 5,171 | 1.97 GB | L1 の seed 違いの重複 |

keep-full の内訳（重複あり）：
- Dream 以外の Room（g001-a-cand-01、job-0001、g002-c3-flux、gl-haiku robustness など）：103
- 条件セル×次元×Level ごとの代表（最小 seed）：89
- セル内の外れ値（conservation_drift または defect_count の |z|>3）：110
- 人間の文書からの引用：1

**小さな資産**：`audit/candidates_keyframes.npz`（**5.3 MB**）
- 形は [1,767 Room, 4 時刻, 24×24, 2 レンズ（位相・密度）] の uint8。3D は中央の z 断面。
- keep-full と distill の全 Room について、見返せる粒度で残す。

## 5. 台帳・レポート（`ai_lab/discoveries/` 94 MB、`ai_lab/reports/` 530 MB）

| ファイル | サイズ | 読むコード | 判定 |
|---|---:|---:|---|
| promising_leads.json | 26 MB | 1 | 要約して index-only（再生成可能な探索ログ） |
| ledger.json | 17 MB | 16 | 残す（多くのコードが読む）→ P5 でコードと一緒に整理 |
| research_memory.json | 14 MB | 5 | 残す |
| coverage_atlas.json | 10 MB | 1 | 要約して index-only |
| emergence_graph.json・unknown_followups.json・x_mechanisms.json | 計 1.5 MB | 4 | 残す（X 監査の出典） |
| reports/nightly（297 MB）・reports/easy（231 MB） | — | — | 直近分と参照されている分だけ作業ツリーに残し、残りはアーカイブ |

## 6. 本当の宝（次に進むべき所）

1. **白の天井地図と証拠庫**：e001–e059、公式 Room、`WHITE_CEILINGS.md`。
2. **自走個体の frontier**：三成分反応拡散（`ANGULAR_MODES.md` の M2＝結合固有値解）。「局在」と「自発運動」を 1 つの白で同時に得る最小の材料は何か。
3. **3D で本物に見える現象**：e003 の GPE 渦リング、Boussinesq 3D、Swift-Hohenberg の局在個体。これらを P4 の水槽テンプレートにする。
4. **負の結果**：TDGL は約 7,000 run でも L2 を越えない。X パターンは、既知の物理で説明できる。

## 7. P3（アーカイブ化）への申し送り

- **作業ツリーから外す候補**：
  - index-only の Room（1.97 GB）
  - distill の Room の field（145 MB。キーフレームで代替）
  - `app/public/data`（生成物・2.2 GB）
  - 古い nightly／easy レポート
- 外すものはすべて `archive/MANIFEST.jsonl`（path・sha256・size・復元コマンド）に記録し、凍結点 `faac01d` から `git restore` で戻せることをテストで保証する。
- keep-full の 272 Room、`experiments/`、`rooms/official/`、`audit/` は作業ツリーに残す。
- `CURRENT_RESEARCH.md` の X の見出しは、この監査への注記に置き換える（P5 で羅針盤を作り直す）。
