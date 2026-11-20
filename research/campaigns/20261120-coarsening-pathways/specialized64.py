"""Build a byte-checked fixed-edge specialization in a private scratch directory."""
from __future__ import annotations

import argparse
from pathlib import Path
import subprocess

from coarsening_runs import PLAN, read_json, sha256, trials_for
import run as archival

FLAGS = ("-O3", "-march=native", "-ffp-contract=off", "-std=c++17")


def specialized_source(original):
    """Avoid the random-access neighbor table and reuse unchanged proposal weights."""
    code = original

    def replace(old, new):
        nonlocal code
        if code.count(old) != 1:
            raise ValueError(f"Unexpected solver source at {old[:60]}")
        code = code.replace(old, new)

    replace("  const int N=std::stoi(argv[1]),d=std::stoi(argv[2]),M=std::stoi(argv[3]),z=2*d;",
    """  constexpr int N=64,d=3,z=6;
      if(std::stoi(argv[1])!=N||std::stoi(argv[2])!=d)throw std::runtime_error("optimized binary requires periodic 64 cubed");
      const int M=std::stoi(argv[3]);""")
    replace("  int V=1;for(int a=0;a<d;++a)V*=N;", "  constexpr int V=N*N*N;")
    start = code.index("  std::vector<std::array<int,6>> neighbor(V);")
    end = code.index("  std::mt19937_64 initial_rng", start)
    code = code[:start] + """  constexpr std::array<unsigned,6> masks{63,63,63<<6,63<<6,63<<12,63<<12};
      constexpr std::array<int,6> offsets{1,-1,1<<6,-(1<<6),1<<12,-(1<<12)};
      auto neighbor_at=[&](unsigned x,int a) {
        return int((x&~masks[a])|((x+unsigned(offsets[a]))&masks[a]));
      };
      for(int x=0;x<V;++x)for(int a=0,jump=1;a<d;++a,jump*=N){
        const int c=(x/jump)%N;
        if(neighbor_at(x,2*a)!=(c+1==N?x-(N-1)*jump:x+jump)
           ||neighbor_at(x,2*a+1)!=(c==0?x+(N-1)*jump:x-jump))
           throw std::runtime_error("neighbor specialization disagrees");
      }
    """ + code[end:]
    for start_name, axis in (("x","a"),("y","a"),("x","direction")):
        code = code.replace(f"neighbor[{start_name}][{axis}]",f"neighbor_at({start_name},{axis})")
    if "neighbor[" in code:
        raise ValueError("Unconverted neighbor reference")
    replace("  auto event=[&](){\n    proposals++;double intensity=contacts*exchange_bound;\n    for(int s=1;s<=4;++s)intensity+=lists[s].size()*bound[s];",
    """  std::array<double,5> weights{};
      double intensity=0.0;
      auto update_weights=[&](){
        intensity=contacts*exchange_bound;
        for(int s=1;s<=4;++s){weights[s]=lists[s].size()*bound[s];intensity+=weights[s];}
      };
      update_weights();
      auto event=[&](){
        proposals++;""")
    replace("const double w=lists[type].size()*bound[type];", "const double w=weights[type];")
    replace("logF:logW);set_type(x,newtype);}", "logF:logW);set_type(x,newtype);update_weights();}")
    replace("    if(path)set_type(y,B?4:3);\n  };", "    if(path)set_type(y,B?4:3);\n    update_weights();\n  };")
    replace("  auto waiting=[&]()->long double {double intensity=contacts*exchange_bound;\n    for(int s=1;s<=4;++s)intensity+=lists[s].size()*bound[s];",
            "  auto waiting=[&]()->long double {")

    return code


def build(plan, scratch):
    original = archival.FUEL / "local_kmc_sparse.cpp"
    if sha256(original) != plan["solver"]["sha256"]:
        raise ValueError("Unexpected reference solver digest")
    source = scratch / "specialized64.cpp"
    source.write_text(specialized_source(original.read_text()))
    binary = scratch / "specialized64"
    subprocess.run(["g++", *FLAGS, str(source), "-o", str(binary)], check=True)
    metadata = {"reference_source_sha256": sha256(original), "specialized_source_sha256": sha256(source),
                "binary_sha256": sha256(binary), "flags": FLAGS,
                "compiler": subprocess.check_output(["g++", "--version"], text=True).splitlines()[0]}
    (scratch / "compiler-manifest.json").write_text(archival.json_text(metadata))
    return binary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", required=True, type=Path)
    parser.add_argument("--scratch", required=True, type=Path)
    parser.add_argument("--jobs", type=int, default=3)
    args = parser.parse_args()
    if args.jobs < 1:
        parser.error("--jobs must be positive")
    plan = read_json(PLAN)
    jobs = [job for job in trials_for(plan) if job.n == 64]
    scratch = args.scratch.resolve()
    scratch.mkdir(parents=True, exist_ok=True)
    binary = build(plan, scratch)
    archival.build_binary = lambda engine, directory: binary
    phase = plan["matrix"]["phase"]
    archival.run_phase(phase, {phase: jobs}, args.evidence.resolve(), scratch,
                       args.jobs, registration_path=PLAN)


if __name__ == "__main__":
    main()
