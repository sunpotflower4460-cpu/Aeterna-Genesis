# F0 プリレジストレーション — P01「成長が点火する3D等方アクティブ液滴」（自走で M2 scissors を切る）

> **docs-only プリレジストレーション（F0）。** physics code・schema・CI・Room・実験番号は**一切変更しない**。
> 「入れるもの／出ると主張するもの／既知理論／対照／失敗条件」を実装前に反証可能な形へ凍結する。
> **F0 提示のみ・実装せず承認待ちで停止。** provisional slug: `p01_active_droplet`（未採番）。

## 0. 中心問い
> **安定したコンパクトな3D個体が、速度も向きも与えられずに、成長で自分の運動閾値を横切って自発的に動き出すか。**

一様混合＋等方ノイズ → 相分離で液滴 → 界面が等方的に溶質を生成 → 半径 R が成長し `Pe_eff(R)` 上昇 →
臨界で **非Goldstone 球面調和 ℓ=1 極性モード**が自発増幅 → Marangoni 応力で液滴が力・トルク自由のまま動く →
向きは法則にも IC にも符号化されず seed 毎に3D空間の別方向。**activity を途中で on にせず、速度も目標軌道も与えない。**

## 1. なぜこの白か（M2 scissors ＋ 今回の null の後継）
これまでの M2：
- SH：安定 compact 個体はあるが非Goldstone drift モードがない。
- 3成分RD：drift 機構候補はあるが安定単一個体がない（存在ゲート REFUSED）。
- **M2-E-3D（#55・済）**：質量保存で安定3D個体は得たが **static**（drift モード無し）。
- **M2-E-3D-NR / NR-2（#56・済＋今回）**：非相反（等方抑制 −κw／勾配移流）で押す試み＝**両方 null**。
  等方抑制は球の**振幅**を、勾配移流は対称な球で**正味ゼロの押し**しか作れず、動く強さは球を**分裂**させる。

→ 教訓：**drift を振幅でなく "並進モード" に、かつ "個体を保つ軸" と "drift を動かす軸" を別の物理量で分離**する
必要がある。P01 はそれを満たす：**A=個体を保つ（相分離・質量保存・界面張力）／B=drift を動かす（溶質 Pe）／
C=split を抑える（capillary number）**を**別パラメータ**で動かせる。`Pe∝R` なので**成長が内生的に運動閾値を横切る**。

## 2. 白（連続式・第一候補は低Re Stokes）
```
F[phi]=∫[ a/4 (phi^2-1)^2 + kappa/2 |grad phi|^2 ] dV ;  mu = a phi(phi^2-1) - kappa lap phi
∂_t phi + u·grad phi = M_phi lap mu                                   (保存相場)
∂_t c   + u·grad c   = D_c lap c + q delta_eps(phi) - k_c c           (界面で等方生成される溶質)
0 = -grad p + eta lap u + div( sigma_K[phi] + sigma_M[phi,c] ) ; div u = 0
```
- `delta_eps(phi)`＝拡散界面だけに局在する回転不変な局所関数（例：正規化 |∇φ|）。`q` は全界面で同一のスカラー（向き無し）。
- `sigma_M`＝界面張力 `gamma(c)=gamma_0-Gamma c` の Marangoni 応力。**応力の発散形**で書き、周期箱の総内部力＝0（運動量収支で監査）。
- 剛体球の最小理論：`Pe=A M R/D_c^2`、**唯一の swimming mode は ℓ=1 で `Pe_1=4`**、高次 `Pe_n=4(n+1)`（化学高調波 ℓ=2 は `Pe=12`）。
- **FFT の位置づけ（C・honesty）**：3D 非圧縮射影/Stokes に FFT を使う版は「global spectral validator」と明記し「中央なし」と呼ばない。将来 local stencil / lattice-Boltzmann で独立検証。

## 3. claim ladder
| 段 | IC / 幾何 | 置くもの | 主張 | role |
|---|---|---|---|---|
| **V0** | 3D固定球・等方 c・無流 | 球＋表面反応 | `Pe_1≈4`・mode hierarchy の既知則再現 | V |
| **V0'** | 3D Cartesian 固定球 | 同上 | 格子で x/y/z の ℓ=1 縮退・回転不変・総内部力=0 | V |
| **S1** | 球状 φ bump・c=0・u=0 | 身体だけ | 身体 seeded・**極性/速度/向きは創発** | S/E capability split |
| **E2** | 一様混合 φ̄+ノイズ・c=0・u=0 | 平均組成＋固定法則 | 液滴形成・単一化・極性・運動が同じ固定白から | E candidate |

## 4. 測定器の必要精密化（既存 M2 測定器の弱点を突く）
- **全場・場別の角モード**：drift precursor は主に `c`・`u` に出て `φ` はほぼ球のまま。第一場 `φ` だけ見ると
  「非Goldstone ℓ=1 が無い」と**誤判定**する。`angular_power_by_field={phi,c,ux,uy,uz}` を保存。
- **3D の ℓ**（球面調和）：ℓ=0 breathing／ℓ=1 polarity・translation／ℓ=2 split precursor。m 縮退も保存。
- **3本の並進 Goldstone**（Tx,Ty,Tz を全場 metric で orthonormalize・部分空間射影除去）。
- **複素固有値**：`Re(log mu)/T`（成長）と `Im(log mu)/T`（振動）を両方保存（定常drift/Hopf/回転を区別）。
- **静止基底 vs 移動後**：分岐の線形解析は臨界直下の**静止液滴**・臨界上は comoving residual。固有値陽性だけで自走達成にしない。

## 5. 事前登録ゲート（要旨）
- **存在**：連結成分=1・tail 95%以上単一・体積 CV<2%・非 domain-filling・臨界直下 lab-frame residual 収束。
- **drift-before-split**：3D 全結合 spectrum で並進 Goldstone 3本を同定し、それと別の**非Goldstone ℓ=1 が誤差 3δλ を越えて正**・同点で `φ` 形状 ℓ=2 は負・`c` 界面双極子と速度の整列が高い。
- **非線形自走**：速度が control/数値床の5倍以上・tail で重心が2液滴半径以上移動・速度方向自己相関が持続・split/mass shedding の偽重心移動を除外。
- **方向を置いていない（24 seed 以上）**：run 内で向き持続・ensemble 平均方向長は小・球面等方性 MC 検定・回転共変。
- **収束/artifact 拒否**：48³→64³→96³（fixed-L）と fixed-dx 有限箱を分離・界面 4–6 cell・`ε/R→0` で onset 収束。**diffuse-interface Marangoni artifact**：onset が界面幅 ε と強共移動し `ε/R→0` で消える／固定球 sharp-interface validator に接続しないなら `N: diffuse-interface artifact`。

## 6. 対照（同 solver・同 seed）
`q=0`（界面化学なし）／`Gamma=0`（濃度は作るが張力へ結合せず）／advection off（`u·grad c` を切る）／subcritical `Pe`（静止へ戻る）／mirror・rotation paired IC／固定球 analytic validator。

## 7. 成功時に言ってよい / いけない
- V0 のみ＝等方 autophoretic instability の既知則再現（**新しい自走個体を生んだ、とは言わない**）。
- S1＝seeded 3D 液滴で極性・速度・向きが自発（**個体自体が白から生まれた、とは言わない**）。
- E2＝一様場から生じた compact 液滴が固定法則のまま非Goldstone極性を作り持続自走（**生命・細胞・意志・目的、とは言わない**）。
- 最強の適切表現：**3D field-generated persistent localized self-propelled object candidate**。

## 8. 実施順（各段停止）
F0（本書）→ F1 V0/V0'（球面/Cartesian validator＋新3D spectrum）→ F2 S1（存在＋drift-before-split＋方向 ensemble）→ F3 E2（一様場・複数 seed・収束・対照）。失敗も相図/ledger へ保存。

## 9. 分岐（P01 失敗時・別 ID/別 F0）
P01-B 二スカラー active-stress 液滴（液晶秩序なし）／P09 非相反 coupled Cahn–Hilliard（hydro なし保存場 traveling patch）／P05 3D 能動ネマ回転。**同じ白へ項を足し続けて同一 ID の成功にしない。**

## 10. 一次文献
Michelin–Lauga–Bartolo (arXiv:1211.6935)・Yoshinaga et al. (1206.3625)・Izri et al. (1406.5950)・Morozov–Michelin (1810.03983)・Schmitt–Stark (1512.05721)・Singh–Tjhung–Cates (2004.06064)・Li et al. diffuse-interface Marangoni (2506.09945)。

**役割**: preregistration（F0）／**実装**: none／**採番**: none／**repo 変更**: docs 1ファイル。
**次の正しい行為**: うえきさん承認 → F1（V0/V0'）から実装。
