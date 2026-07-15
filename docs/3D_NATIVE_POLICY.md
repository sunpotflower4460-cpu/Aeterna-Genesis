# 3D_NATIVE_POLICY — 3D を本線にする規律（うえきさんの指針・2026-07）

> 前提：[`AGENTS.md`](../AGENTS.md)「現実に忠実な起き方で計算する」。2D は速い便宜だが、脳/生命/宇宙の核心の
> 自由度（非平面配線・結び目/絡み・ヘリシティ・渦伸長・内部を囲う）は **2D に無い**。→ **新規の創発探索は 3D を本線**。
> 2D は削除しない：診断・断面・過去検証・測定器の単体テストに限定。

## 1. 「本物の 3D か」を必ず監査する（`genesis/diagnostics/topology3d.py`）
配列が Nx×Ny×Nz でも 3D とは限らない（2D の押し出し＝偽 3D の恐れ）。**3D を主張する run は下を通す**：
- `three_d_authenticity(field)` が **`genuinely_3d: True`**（z 微分が効く・押し出しでない・z 変動率 > 閾値）。
- **3D 固有量を最低 1 つ**測る：`helicity`（2D で恒等的 0）／`three_axis_percolation`（3軸貫通）／Hopf 電荷／
  linking／閉曲面・内部体積 のいずれか。
- 面外摂動テスト：2D 的構造に z 揺らぎを与え、崩れる/3D 化/平面へ戻る を測る（可能なら）。
- 機械可読で記録：`three_d_authenticity: {full_volume, z_variation_fraction, extruded_from_2d, genuinely_3d,
  three_d_invariant: <name=value>}`。

## 2. 解像度は物理基準で（固定 edge でなく）
- 段階：Micro 3D(24³〜32³・存在/安定確認)→ Local 3D(32³〜48³)→ Coarse Global(48³〜64³)→ Standard(64³〜96³)→
  Official(96³以上・複数解像度で収束)。粗い 3D は安い（実測 24³≈2s〜48³≈16s/4000step）。
- 基準：`cells_per_core_radius ≥ 8`・`cells_per_interface_width ≥ 6`・`domain_lengths_per_structure ≥ 4`
  （モデル毎に調整可。渦芯が 2 セルなら 96³ でも不足）。

## 3. 局所本線・独立検証器（`corroborate`）
- **局所ステンシルを本線**（`np.roll`）・**スペクトル(FFT)を独立検証器**。両者一致＝solver 独立の証拠。
- 可能なら**別 codebase の裏付け**（`tools/corroborate.py`：Genesis-Room 3D／0-looper 2D を隔離サブプロセスで
  並列実行）。kind ラベルで「同一モデル定量」と「還元機構の構造」裏付けを区別。

## 4. drift は 3D で測る（`coupled_spectrum` 次元非依存）
- 3 並進 Goldstone(Tx,Ty,Tz)＋球面調和 ℓ（ℓ=0 呼吸/ℓ=1 drift/ℓ=2 split）。非 Goldstone ℓ=1 が ℓ=2 より
  先に不安定＝3D drift-before-split 候補（[`ANGULAR_MODES.md`](ANGULAR_MODES.md) M2→3D）。

## 5. ANTI_DRIFT（3D 版）
- **トーラス/hopfion/DNA 的ねじれを IC に置かない**（置けば `provenance` の `claim_excludes` 必須・V 検証扱い）。
  構造なし 3D 場から**育つ**か（E 創発）を問う。
- **同じトポロジー ≠ 同じもの**：3D で結び目/渦が出ても「宇宙/生命/意識」とは言わない（spots≠life の 3D 版）。
- no-go は white/領域/解像度限定。honest floor：粗い 3D は安いが高解像度収束は分単位＝正式の少数だけ。

## 6. 2D の役割（限定）
- 過去実験・理論検証・**断面表示**・**測定器の単体テスト**のみ。**新規の創発候補の本線探索には使わない。**
