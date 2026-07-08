# e020 — 小胞の分裂は場の力学から出るか（H002+, 負の結果）— AUDIT

> e018 の有界小胞を「二つに割れるか」。**分裂を直接コーディングせず**（「くびれたら切る」等なし）、
> 場に形（円/楕円/ダンベル/フィラメント）と緩めた質量制御を与え、連結成分数を測る。
> **結果は明確な負**：受動 phase-field（Allen-Cahn も Cahn-Hilliard も）は分裂せず、全形が単一
> ドロップレットに緩和する。分裂には**能動 turnover（Zwicker）**が要る＝frontier（誘導しない）。

## 監査ヘッダ（division.py 先頭と同一）
```
MODULE:   e020_vesicle_division
QUESTION: phase-field 小胞は場の力学だけで自発的に分裂（n_components 1→2）するか、スクリプトなしで。
PUT IN:   受動 phase-field（Allen-Cahn 質量制御・Cahn-Hilliard 保存）＋形（円/楕円/ダンベル/フィラメント）。分裂則なし。
EMERGED:  (measured) 否。全形が単一ドロップレットに緩和（AC は合体、CH は退縮）。受動緩和は分裂しない。
CLAIM TIER: measured(受動力学で自発分裂なし) ; interpretive(分裂は能動 turnover が要る) ; analogy(小胞/分裂)。
KNOWN MATCH: 曲率流/Ostwald 熟成（合体）；Rayleigh-Plateau（長い細糸が要る）；Zwicker 能動ドロップレット（分裂、frontier）。
STATUS:   GREEN（受動 phase-field が分裂しないことを忠実に測定＝きれいな負。スクリプトしていない）。能動分裂は frontier。
A_OR_B:   (A) 忠実。手入力＝受動力学＋形；（非）分裂は創発・測定であって、入れていない。
```

## 測定（`division.py` → `results/division.json`）

**Allen-Cahn（e018 質量制御モデル、曲率流）**：円/楕円/ダンベル/フィラメント、全て **final_components=1**。
ダンベルの**くびれは埋まる**（曲率流は凹を平滑化＝合体）。分裂しない。

**Cahn-Hilliard（保存、半陰的スペクトル）**：細いフィラメントは Rayleigh-Plateau で割れうるが、
2D 表面張力が**端から退縮**して単一ドロップレットに（half=0.028/0.040/0.055 全て final=1）。分裂しない。

| モデル | 形 | 最終連結成分 | 分裂 |
|---|---|---|---|
| Allen-Cahn | 円/楕円/ダンベル/フィラメント | **1**（全て） | No |
| Cahn-Hilliard | フィラメント×3 | **1**（全て） | No |

- **受動 phase-field は自発分裂しない**（エネルギー最小化→単一ドロップレットが引力）— measured（負）。
- **分裂には能動機構が要る**（Zwicker 能動ドロップレット＝成長＋形状不安定）— interpretive、**frontier（本モジュールでは回さない＝誘導しない）**。

## 7監査
| # | 監査 | 判定 | 理由 |
|---|---|---|---|
| 1 | 規則が結果を名指す? | **No** | 分裂則を書いていない（「割れたら切る」なし） |
| 2 | 忠実な物理? | **Yes** | Allen-Cahn 曲率流・Cahn-Hilliard 保存は実在 |
| 3 | 結果は初期条件に? | **No** | 形は与えるが、（非）分裂は後から測定 |
| 4 | 入れてない物が出る? | **Yes（負として）** | 「分裂しない・単一に緩和」を測定（入れていない） |
| 5 | 数で合う? | **Yes** | 全 run で final_components=1、finite=True |
| 6 | 頑健? | **Yes** | 2モデル・4形・3半幅で一貫して単一 |
| 7 | コードが発見? | **Yes** | ndimage.label で成分を測定、分裂を書き込まない |

→ 実験は忠実で、**きれいな負の測定**＝GREEN（誠実な負の結果）。能動分裂は frontier。

## 床（隠さない・必須）
1. **2D 粗視化連続**。受動モデルのみ（**能動 Zwicker 分裂は frontier、回していない＝誘導しない**）。
2. 「小胞/分裂」は analogy。固定周期格子。**分裂する細胞を作ったのではない**。
3. Rayleigh-Plateau は十分長い細糸で起きうるが、2D では退縮が先に効く（測定した床）。

## 再現
```bash
python experiments/e020_vesicle_division/division.py   # AC/CH とも単一に緩和（分裂なし）
pytest tests/test_e020.py
```
