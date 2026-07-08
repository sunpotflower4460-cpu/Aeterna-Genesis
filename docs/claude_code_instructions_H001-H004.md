# AeternaGenesis ClaudeCode指示書 — H001 → H002+ → H003full → H004

作成: Claude（Cowork）/ 2026-07-08
形式: `LAW.md`のモジュールヘッダ規約＋`docs/codex-gauge-invariant-audit-instruction.md`のTask/DoD形式に準拠。
このファイルをリポジトリの`docs/`に置き、フェーズごとに該当セクションだけをClaude Codeに渡して実行させる想定。

## 共通の掟（全フェーズ厳守、LAW.mdより）
- 各`run.py`冒頭とAUDIT.mdに10項目ヘッダ必須：`MODULE / QUESTION / PUT IN / EMERGED / CLAIM TIER / KNOWN MATCH / AUDIT(7) / STATUS / A_OR_B`
- 7点監査全通過のみGREEN。それ以外を成功と呼ばない
- claim tier（measured/observed/interpretive/analogy/frontier）を全主張に付与
- 崩壊・dead-end・否定された仮説も隠さず記録（`_archive/`または該当working_ledger）
- 「生命/意識/電子/魂/分子/脳/永遠/証明/perfect」等の禁止語を使わない。「同じ数学」≠「同じもの」

## フェーズ1: H001続き — ホップ粒子の大域化（basin拡大・L=56劣化の原因特定）
背景（`docs/working_ledger/H001_hopf_global_newton.md`より）
- e016で `size = k√c4`（k=0.901, CV=3.5%, R²=0.941）を確認済み（L=44/52でtight）
- L=56ではCV=6.6%・R²≈0.57に劣化。「κ∝dx⁴較正」仮説を試したが否定済み（較正κ=20.5でも固定κ=40より改善せず）
- basinは有界（保持window mult ≈[0.7, 1.5]）。原因未特定の開いた床のまま

Task 1: 既存コードの現状確認 — `arrested_newton.py`と`hopf_basin.py`を読み、L=56劣化がどう測定されているかを`results/`のJSONで確認。κ較正以外に何が未試験かをリストアップ。
Task 2: 真のarrested-Newton実装 — Newton的加速（line-search／過緩和）＋高波数kのbiharmonic抑制の変種を新関数で実装。「勾配流のみ」vs「arrested-Newton」のbasin幅を比較。
Task 3: 高解像度でのL=56原因特定 — L=64で同じsize則。L=44/52/56/64のCV・R²を並べ、劣化がLに対して単調か閾値的か。dxとκの効果分離も検討。
Task 4（余力があれば）: トポロジー保存離散化 — Q_Hを離散保存する差分スキームの試作。

DoD: `results/arrested_newton_v2.json`にbasin幅・CV・R²・Q_H・エネルギー単調性。L=56劣化を「原因特定→promoted」or「別仮説も否定→dead-end追記」のどちらかをH001台帳に追記（曖昧なまま放置しない）。AUDIT.md更新、STATUS/A_OR_B明記。

## フェーズ2: H002+ — 小胞の分裂 ＋ 小胞の中に渦の粒を入れる
背景（`docs/working_ledger/H002_membrane_vesicle.md`より）：e018小胞GREEN、e019粒子GREEN。次の一手「小胞の分裂（体積制御を緩める）」「三体結合で小胞の中に粒子」。新モジュール（e020, e021等、次番号を採番）。

Task 1: 小胞分裂（e0NN_vesicle_division）— `evolve(p,s,leak)`ベースに質量制御`target`を緩める。分裂を直接コーディングしない（スクリプト化禁止）。曲率不安定/Rayleigh-Plateau的くびれが場の力学から自然に出るかだけ見る。連結成分数の時系列を測定。
Task 2: 小胞に渦の粒を内包（e0NN_vesicle_particle）— e016のホップ粒子をe018小胞の中心に埋め込み共存発展。Q_H保持・小胞連結性・溶けたときの粒子の運命。

DoD: 分裂は`not_scripted_check`明記の上、起きた/起きなかったをそのまま記録。内包は独立対照実験を含める。AUDIT/claim_ledger追記、STATUS判定。

## フェーズ3: H003full — 三体結合を本物の流体（Boussinesq DNS）で
背景（`docs/working_ledger/H003_three_body_coupling.md`より）：e019は流れを振幅UだけのODEで簡略。双方向でU=3.35自己制限Q_H=0.97／一方向U=9.56破壊Q_H=−0.21。次の一手「実Boussinesq流に粒子を埋め込む双方向」。

Task 1: 計算コスト見積もり — `rb_dns.py`の`dns(p,Ra)`を確認、粒子埋め込み込みのコスト見積もり。quickで試走し完走可能上限を決める。
Task 2: 三体結合の本体化 — `dns`の実速度場にe016ホップ粒子を埋め込み、`three_body.py`と同じ双方向結合（背反応=抗力）を実速度場に対して実装。
Task 3: 対照実験 — 一方向 vs 双方向で自己制限が本物の流体でも再現するか。

DoD: 重すぎて完走しない場合はその旨と縮小設定を正直に記録し`frontier`扱いで台帳に残す（無理に軽量化して歪めない）。再現した場合はH003に「full-DNS版」追記、AUDIT/claim_ledger更新。

## フェーズ4: H004 — 作用＝エントロピー（最深、おもちゃモデルから）
背景（`docs/working_ledger/H004_action_entropy.md`より）：proposed（未実装）。TypeD。仮説：作用（高階項）がエントロピー最大化／もつれ面積則から導出できないか（Jacobson 1995, Verlinde 2011）。

Task 1: おもちゃモデル — `causal_dimension.py`の`sprinkle_interval(d,N,rng)`を再利用、因果ダイヤモンド上にエントロピー汎関数（関係数/もつれ代理）を定義。停留点が既知運動方程式（拡散→波動）と整合するか。
Task 2: 面積則の代理測定 — `core/field.py`複素場のサブ領域もつれ代理量が面積とスケールするか。manifold#2と接続。
Task 3: δQ=TδSの局所検証 — 玩具モデルの範囲で局所領域を探索（本格もつれ計算は対象外＝スケール環境向け明記）。

DoD: 3タスクとも「measured」の数値を得るか、得られなければ「frontier継続・具体的に何が未解決か」明記。「作った」と言わない（問いの登録、Jacobson/Verlindeは提案）。新規`experiments/e0NN_action_entropy/`、AUDIT/claim_ledger新規。

## 運用メモ
- 各フェーズは独立したClaude Codeセッションとして渡すことを推奨（コンテキスト混在回避）
- フェーズ1→2は軽い（既存資産の組み合わせ・拡張）。フェーズ3は重い計算（先にコスト見積もり必須）
- フェーズ4はいつ着手してもよい（独立）。土台が固まってから着手する方が安全で最後に配置
- 各フェーズ完了後、`docs/claim_ledger.md`と該当working_ledger（H001-H004）の状態欄を必ず更新
