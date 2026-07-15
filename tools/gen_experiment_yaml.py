#!/usr/bin/env python3
"""PR3 generator: write one experiment.yaml per experiments/e0xx/ from a hand-authored table.

Data source: docs/TRUST_MAP.md (role / target_encoded), docs/現在地と方向性_TypeABCD.md (confidence Type A-D),
docs/GENESIS_MAP.md §1 (genesis_role), and each module's embedded YAML header / AUDIT.

This is a ONE-TIME, reproducible generator; it writes experiment.yaml (does NOT touch physics code, results,
or any existing file). Run `python tools/gen_experiment_yaml.py [--out-root DIR]`; validates each against
schemas/experiment.schema.json. Idempotent (overwrites only experiment.yaml).
"""

import argparse
import json
import os
import sys

import yaml
from jsonschema import Draft202012Validator

# id -> dict of experiment.yaml fields (minus id). role primary/secondary, confidence, claim_tier,
# put_in/emerged, seeded_structure, dimension {computed, transfer_risk}, genesis_role, target_encoded,
# known_match (optional), results (optional).
DATA = {
  "e001_gpe_vortex_precession": dict(title="GPE 渦歳差", role="E", conf="A", tier=["measured"],
    dim="2D", risk="high", grole="behavior_dictionary", te=False, seeded=False,
    put="実在の Gross-Pitaevskii 場＋渦初期配置", emg="点渦スケール則 ω≈2/d² が場から出る",
    km="点渦近似（Kelvin/Onsager）"),
  "e002_gpe_two_vortex": dict(title="GPE 二渦", role="E", conf="A", tier=["measured"],
    dim="2D", risk="high", grole="behavior_dictionary", te=False, seeded=False,
    put="GPE ＋二渦初期配置", emg="同符号共回転／逆符号並進が創発", km="点渦相互作用"),
  "e003_gpe_vortex_ring": dict(title="GPE 渦リング", role="E", conf="A", tier=["measured"],
    dim="3D", risk="low", grole="behavior_dictionary", te=False, seeded=False,
    put="3D GPE ＋渦リング初期条件", emg="リングが自己伝播（トーラス）", km="渦リング自己誘導速度"),
  "e004_octave_holography": dict(title="オクターブ/ホログラフィー", role="S", conf="C", tier=["analogy"],
    dim="2D", risk="not_applicable", grole="sidebranch_analogy", te=False, seeded=True,
    put="MERA/AdS の設計構造（手配線）", emg="設計した階層構造（忠実創発でない・自己申告 analogy）",
    km="MERA / AdS-CFT"),
  "e008_coemergence": dict(title="同時共創発", role="E", conf="A", tier=["measured", "interpretive"],
    dim="2D", risk="medium", grole="genesis_candidate", te=False, seeded=False,
    put="白色場＋GPE、一様に近い状態", emg="物質/時間/空間が同時・欠陥の自然形成（Genesis 候補）",
    km="Kibble-Zurek"),
  "e009_exploratory": dict(title="探索（トーラス電流・種成長）", role="F", conf="C", tier=["observed"],
    dim="2D", risk="medium", grole="sidebranch_analogy", te=False, seeded=False,
    put="探索的な場・初期条件", emg="持続トーラス電流・種成長候補（側枝・別 modality）", km=None),
  "e010_kz_coherence": dict(title="KZ コヒーレンス長", role="E", conf="A", tier=["measured"],
    dim="2D", risk="high", grole="genesis_candidate", te=False, seeded=False,
    put="GPE クエンチ（一様＋ノイズ）", emg="spacing/ξ は独立 N・ξ 比較が本物（0→差→欠陥の強い候補）",
    km="Kibble-Zurek 欠陥生成則"),
  "e011_defect_chemistry": dict(title="欠陥の化学", role="E", conf="A", tier=["measured"],
    dim="2D", risk="high", grole="behavior_dictionary", te=False, seeded=False,
    put="GPE ＋欠陥対、有限T(SGPE)", emg="v·d, ω·d² 選択則・有限T解離", km="欠陥対運動則"),
  "e012_hopf_stabilization": dict(title="Hopf 安定化（第三）", role="E", conf="A", tier=["measured"],
    sec=["V"], dim="3D", risk="high", grole="behavior_dictionary", te=False, seeded=False,
    put="完全 Faddeev-Skyrme PDE ＋hopfion", emg="自己安定化・有限 L* 収束・Derrick L*∝√c4（静的最小化＝V級）",
    km="Faddeev-Skyrme / Derrick"),
  "e013_vessel_content": dict(title="器＋中身", role="S", conf="B", tier=["measured"],
    sec=["E"], dim="2D", risk="medium", grole="genesis_candidate", te=False, seeded=False,
    put="規定流(S)／自己組織 Rayleigh-Benard(E)＋中身", emg="規定流は設計・自己組織対流は循環創発（Genesis 候補）",
    km="Rayleigh-Benard"),
  "e014_causal_dimension": dict(title="因果→次元", role="E", conf="A", tier=["measured"],
    dim="graph", risk="not_applicable", grole="measurement_tool", te=False, seeded=False,
    put="因果順序のみ（sprinkling）", emg="順序から d=2,3,4→1.99/2.97/3.95（次元計測器）",
    km="Myrheim-Meyer / spectral dimension"),
  "e015_vessel_closure": dict(title="器の閉じ（駆動依存）", role="E", conf="B", tier=["measured"],
    dim="2D", risk="medium", grole="design_hypothesis", te=False, seeded=False,
    put="Gray-Scott 駆動系", emg="駆動で自己維持・切ると死（M∧A 連言）", km="Gray-Scott RD"),
  "e016_hopf_basin": dict(title="Hopf basin（√c4 撤回）", role="F", conf="C", tier=["observed"],
    dim="3D", risk="high", grole="behavior_dictionary", te=True, seeded=False,
    put="Hopf 場＋start∝√c4（初期条件に埋込＝撤回理由）",
    emg="√c4 size 則は初期条件埋込＝撤回。Q_H=2 安定性は observed",
    km="Derrick スケール則", unresolved=["√c4 size 則は target_encoded で撤回（decoupling drift 26%）"]),
  "e017_walled_convection": dict(title="壁つき RB", role="V", conf="A", tier=["established"],
    dim="2D", risk="medium", grole="measurement_tool", te=False, seeded=False,
    put="壁付き Boussinesq 線形安定性/DNS", emg="Ra_c=1714/657＝教科書<0.4%（対流臨界値の検証器）",
    km="Rayleigh-Benard 臨界 Ra"),
  "e018_membrane_vesicle": dict(title="膜小胞", role="E", conf="B", tier=["measured"],
    dim="2D", risk="medium", grole="design_hypothesis", te=False, seeded=False,
    put="phase-field 膜＋駆動", emg="有界小胞（薄い膜）が駆動で持続・切ると溶ける（三腕死＝連言）",
    km="phase-field membrane"),
  "e019_coupling": dict(title="結合", role="S", conf="B", tier=["measured"],
    dim="2D", risk="medium", grole="design_hypothesis", te=False, seeded=False,
    put="規定 roll ＋粒子", emg="規定 roll が粒子を運ぶ（設計）／U_c crossover", km="移流輸送"),
  "e020_vesicle_division": dict(title="小胞分裂（負の結果）", role="N", conf="B", tier=["measured"],
    dim="2D", risk="medium", grole="negative_constraint", te=False, seeded=False,
    put="受動 phase-field 小胞", emg="受動場は自発分裂しない（負の結果＝探索空間の制約）",
    km="phase-field（受動）"),
  "e021_self_receiver": dict(title="自己受信", role="E", conf="B", tier=["measured"],
    dim="2D", risk="medium", grole="design_hypothesis", te=False, seeded=False,
    put="外場ゼロの GL リング＋芯", emg="外場ゼロでリングが芯巻きを読む（受信）", km="Aharonov-Bohm 位相"),
  "e022_horizon_ledger": dict(title="地平線台帳", role="V", conf="B", tier=["measured"],
    dim="2D", risk="high", grole="measurement_tool", te=False, seeded=False,
    put="AB リング／DS 分子（2D）", emg="DS 分子→π²/6（2D SOLID・3D 係数は F）＝ゲージ不変量計測器",
    km="de Sitter エントロピー π²/6", unresolved=["3D DS 係数は床（e032）"]),
  "e023_causal_action": dict(title="順序→時空", role="E", conf="B", tier=["measured"],
    dim="graph", risk="not_applicable", grole="measurement_tool", te=False, seeded=False,
    put="純粋因果順序（sprinkling）", emg="順序から時間・有限次元・向き（時空計測器）",
    km="causal set / Benincasa-Dowker"),
  "e024_vessel_engine": dict(title="器のエンジン", role="F", conf="D", tier=["measured"],
    dim="1D", risk="medium", grole="design_hypothesis", te=False, seeded=False,
    put="1D 過減衰ラチェット＋燃料勾配", emg="ラチェット整流は忠実だが「器モーター」は設計＝frontier",
    km="Brownian ratchet"),
  "e025_vessel_life": dict(title="生きた器（三器官／autopoietic）", role="S", conf="B", tier=["measured"],
    sec=["E"], dim="2D", risk="medium", grole="design_hypothesis", te=True, seeded=True,
    put="2D CGL トイ／winding→gain の手配線閉ループ(oracle)",
    emg="三器官の対比は faithful／autopoietic は手配線回路（target_encoded・S 明示）",
    km="complex Ginzburg-Landau", unresolved=["autopoietic は winding→gain oracle＝target_encoded (role S)"]),
  "e026_vessel_division": dict(title="分裂会計", role="F", conf="B", tier=["measured"],
    dim="2D", risk="medium", grole="negative_constraint", te=False, seeded=False,
    put="巻き保存の静的トポロジー会計", emg="巻き算術は測定／トポロジカル量は単純コピーできない（制約）／動的 pinch は frontier",
    km="トポロジカル電荷保存"),
  "e027_evolution_transition": dict(title="進化・大転移（エージェント）", role="F", conf="B", tier=["measured"],
    dim="2D", risk="not_applicable", grole="sidebranch_analogy", te=False, seeded=False,
    put="エージェント模型（場でない）＋内生需要/群選択", emg="適応・多様化・協力（機構実証）／場版は e033–e036（別 modality）",
    km="Nowak-May / 進化ゲーム", unresolved=["エージェント模型＝場でない（側枝）。場版は e033–e036"]),
  "e028_topological_memory": dict(title="トポロジカル記憶", role="E", conf="B", tier=["measured"],
    dim="2D", risk="medium", grole="design_hypothesis", te=False, seeded=False,
    put="固定格子 GL リング＋穴の巻き", emg="巻き保護受信・capacity>dof（read-miss を honest 化）",
    km="トポロジカル保護 / ゲージ不変"),
  "e029_openended_frontier": dict(title="共進化・大転移 frontier", role="F", conf="D", tier=["frontier"],
    dim="2D", risk="not_applicable", grole="design_hypothesis", te=False, seeded=False,
    put="内生需要の敵対的共進化／群再生産＋ボトルネック（エージェント）",
    emg="内生需要で growth 到達可（reachability ゲート）・協力救済（機構実証）／真の無限オープンエンドは未解決",
    km="Red Queen / major transition", unresolved=["真の無限オープンエンド性は frontier"]),
  "e030_division_of_labor": dict(title="分業（群選択）", role="F", conf="D", tier=["frontier"],
    dim="2D", risk="not_applicable", grole="design_hypothesis", te=False, seeded=False,
    put="群選択エージェント（凸リターン）", emg="凸性→分業（機構実証・抽象 toy 適応度＝床）／場版は e033",
    km="Michod 分業理論"),
  "e031_causal_action_smearing": dict(title="因果作用の平滑化", role="F", conf="D", tier=["frontier"],
    dim="graph", risk="not_applicable", grole="measurement_tool", te=False, seeded=False,
    put="BD 生作用＋Glaser-Surya 平滑化", emg="BD 揺らぎを定量化（治療でなく障害の定量化・曲率信号 ~1σ＝床）",
    km="Benincasa-Dowker / Glaser-Surya"),
  "e032_ds_horizon_3d": dict(title="3D DS 病理", role="F", conf="D", tier=["frontier"],
    dim="3D", risk="not_applicable", grole="measurement_tool", te=False, seeded=False,
    put="3D(2+1) de Sitter DS 分子", emg="面積則成立(R²>0.85)・係数ドリフト(4.02×)＝d>2 病理（次元依存の定量化）",
    km="de Sitter エントロピー（3D）"),
  "e033_field_division_of_labor": dict(title="分業＝場（Cahn-Hilliard）", role="E", conf="A", tier=["measured"],
    sec=["V"], dim="2D", risk="medium", grole="genesis_candidate", te=False, seeded=False,
    put="Cahn-Hilliard/Flory-Huggins（一様＋ノイズ）", emg="スピノーダル分解 χc=2・二相共存・binodal 一致（V級）",
    km="Cahn-Hilliard / Flory-Huggins"),
  "e034_field_cooperation_front": dict(title="空間協力＝場（Nagumo）", role="E", conf="A", tier=["measured"],
    sec=["V"], dim="2D", risk="medium", grole="behavior_dictionary", te=False, seeded=False,
    put="双安定 Nagumo 反応拡散", emg="平均場崩壊・空間侵入・a_c=1/2（Maxwell 点）・Nagumo 速度一致（V級）",
    km="Nagumo bistable front / Maxwell point"),
  "e035_field_red_queen": dict(title="Red Queen＝場（Hopf）", role="E", conf="A", tier=["measured"],
    sec=["V"], dim="2D", risk="low", grole="genesis_candidate", te=False, seeded=False,
    put="Rosenzweig-MacArthur 捕食者被食者", emg="頭打ち→内生振動・発生点＝解析 Hopf 点（V級・時間的自己組織化候補）",
    km="Rosenzweig-MacArthur Hopf"),
  "e036_field_adaptation": dict(title="適応＝場（replicator-mutator）", role="E", conf="A", tier=["measured"],
    sec=["V"], dim="2D", risk="medium", grole="behavior_dictionary", te=False, seeded=False,
    put="replicator-mutator/Crow-Kimura 密度場", emg="σ²=√(2D/k)・lag load（閉形式一致・V級）",
    km="replicator-mutator / Crow-Kimura"),
  "e037_ecological_pgg": dict(title="生態的 PGG（協力＝場）", role="E", conf="B", tier=["measured"],
    dim="2D", risk="medium", grole="behavior_dictionary", te=False, seeded=False,
    put="Hauert-Holmes-Doebeli 生態的 payoff の純 PDE", emg="生態的 feedback で協力持続・古典(定コスト)は崩壊・機構は空間でない",
    km="ecological public goods game"),
  "e038_field_objtrack": dict(title="連続形質進化（object tracking）", role="E", conf="B", tier=["measured"],
    dim="2D", risk="medium", grole="behavior_dictionary", te=False, seeded=False,
    put="Gray-Scott 場＋per-tissue 形質（低播種）", emg="de novo で 0.2→0.9・連続維持・移動最適点追跡（hybrid 床）",
    km="replicator-mutator / de novo adaptation"),
  "e039_field_differentiation": dict(title="分化（morphogen＋Turing）", role="E", conf="B", tier=["measured"],
    dim="2D", risk="medium", grole="behavior_dictionary", te=False, seeded=False,
    put="French-flag モルフォゲン＋Gierer-Meinhardt Turing", emg="3 順序ドメイン・一様から自己組織（std 0.02→1.19）",
    km="Wolpert French-flag / Turing"),
  "e040_field_rps_cooperation": dict(title="協力＝RPS スパイラル", role="E", conf="B", tier=["measured"],
    dim="2D", risk="medium", grole="behavior_dictionary", te=False, seeded=False,
    put="循環 Lotka-Volterra(C-D-L)＋拡散／well-mixed 対照", emg="スパイラル波で三者共存・well-mixed は崩壊（spiral は regime 依存＝床）",
    km="cyclic Lotka-Volterra / May-Leonard"),
  "e041_field_bottleneck": dict(title="ボトルネック（幾何）", role="S", conf="B", tier=["measured"],
    dim="2D", risk="not_applicable", grole="design_hypothesis", te=False, seeded=True,
    put="タグ付き体＋ピンチネック（幾何サンプリング模型）", emg="ネック幅→創設者数→relatedness（狭→clonal・広→mixed）",
    km="Grosberg-Strathmann bottleneck / Simpson"),
  "e043_field_universe": dict(title="場の宇宙（6過程統合）", role="E", conf="B", tier=["measured"],
    dim="2D", risk="medium", grole="behavior_dictionary", te=False, seeded=False,
    put="ONE Gray-Scott 場＋per-tissue 形質＋モルフォゲン最適点", emg="分裂+適応+分化が同時＝分化した適応ボディ（hybrid 床）",
    km="e038+e039 統合 / Wolpert 位置情報"),
  "e044_field_unification": dict(title="場の統一（協力）", role="E", conf="B", tier=["measured"],
    dim="2D", risk="medium", grole="behavior_dictionary", te=False, seeded=False,
    put="e043 場＋局所公共財＋便益ゼロ対照（param 事前固定）", emg="clonal 同類化で協力持続・対照は崩壊（絶対値は param 依存＝床）",
    km="Hamilton assortment / localized public goods"),
  "e045_field_endogenous": dict(title="内生ニッチ（負の結果）", role="N", conf="B", tier=["measured"],
    dim="2D", risk="medium", grole="negative_constraint", te=False, seeded=False,
    put="負の頻度依存のみ（外部最適点なし）＋中立対照＋強罰 run",
    emg="生存窓内では中立を超えず・強罰は絶滅＝内生多様性は自己生成しない（負の結果）",
    km="negative frequency-dependent selection / neutral null"),
  "e046_topological_state_capacity": dict(title="トポロジカル状態容量（独立ホロノミーチャネル=b₁）",
    role="V", sec=["N"], conf="A", tier=["measured", "established"],
    dim="graph", risk="low", grole="measurement_tool", te=False, seeded=True,
    put="固定曲面の胞複体＋辺 U(1) 接続＋H₁ 基底＋（一部）指定巻き（トポロジーと巻きは置く）",
    emg="rank H₁=b₁=2g／読み戻し正確／ゲージ不変／可縮=0／同ホモロジー同値（測定器検証＝V・非創発）",
    km="胞体コホモロジー H¹ / トーリック符号の保護論理dof / Aharonov-Bohm / Poincaré-Hopf(別statement)"),
}


def _results_for(repo, dirname):
    rd = os.path.join(repo, "experiments", dirname, "results")
    if not os.path.isdir(rd):
        return []
    return ["experiments/%s/results/%s" % (dirname, f) for f in sorted(os.listdir(rd)) if f.endswith(".json")]


def _build(dirname, d, repo):
    eid = dirname.split("_")[0]
    role = {"primary": d["role"]}
    if d.get("sec"):
        role["secondary"] = d["sec"]
    doc = {
        "id": eid,
        "title": d["title"],
        "role": role,
        "confidence": d["conf"],
        "claim_tier": d["tier"],
        "put_in": d["put"],
        "emerged": d["emg"],
        "seeded_structure": d["seeded"],
        "dimension": {"computed": d["dim"], "official_3d": False, "transfer_risk": d["risk"]},
        "genesis_role": d["grole"],
        "target_encoded": d["te"],
    }
    if d.get("km"):
        doc["known_match"] = d["km"]
    if d.get("unresolved"):
        doc["unresolved_audit"] = d["unresolved"]
    res = _results_for(repo, dirname)
    if res:
        doc["results"] = res
    return doc


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-root", default=os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    ap.add_argument("--repo", default=os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    args = ap.parse_args(argv)
    schema_path = os.path.join(args.repo, "schemas", "experiment.schema.json")
    validator = Draft202012Validator(json.load(open(schema_path)))
    exp_dirs = sorted(d for d in os.listdir(os.path.join(args.repo, "experiments"))
                      if d.startswith("e0") and os.path.isdir(os.path.join(args.repo, "experiments", d)))
    missing = [d for d in exp_dirs if d not in DATA]
    if missing:
        print("ERROR: no DATA entry for: %s" % missing)
        return 2
    n_ok = 0
    for dirname in exp_dirs:
        doc = _build(dirname, DATA[dirname], args.repo)
        errs = sorted(validator.iter_errors(doc), key=lambda e: list(e.absolute_path))
        if errs:
            print("INVALID %s:" % dirname)
            for e in errs:
                print("   - %s at %s" % (e.message, list(e.absolute_path)))
            return 1
        out_dir = os.path.join(args.out_root, "experiments", dirname)
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, "experiment.yaml"), "w") as f:
            f.write("# Auto-generated by tools/gen_experiment_yaml.py (PR3). "
                    "Validated against schemas/experiment.schema.json.\n")
            f.write("# 一次情報は docs/TRUST_MAP.md / docs/GENESIS_MAP.md。物理コード・results は不変更。\n")
            yaml.safe_dump(doc, f, allow_unicode=True, sort_keys=False, width=100)
        n_ok += 1
    print("wrote + validated %d experiment.yaml (into %s)" % (n_ok, args.out_root))
    return 0


if __name__ == "__main__":
    sys.exit(main())
