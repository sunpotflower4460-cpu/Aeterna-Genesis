// Three-dimensional monatomic fluid, periodic box, linear-force-shifted Lennard-Jones pairs.
// Atom indices identify the same atom throughout an integration. Diagnostics never change its force.
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <random>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

using Vec = std::array<double, 3>;
namespace fs = std::filesystem;

double squared(Vec a) { return a[0] * a[0] + a[1] * a[1] + a[2] * a[2]; }

struct LJ {
    double cutoff, cutoff_sq, u_cut, f_cut;
    explicit LJ(double r) : cutoff(r), cutoff_sq(r * r) {
        const double ri2 = 1 / cutoff_sq;
        const double ri6 = ri2 * ri2 * ri2;
        u_cut = 4 * ri6 * (ri6 - 1);
        f_cut = 24 * ri6 * (2 * ri6 - 1) / r;
    }

    double potential(double r2) const {
        if (r2 >= cutoff_sq) return 0;
        const double ri2 = 1 / r2;
        const double ri6 = ri2 * ri2 * ri2;
        return 4 * ri6 * (ri6 - 1) - u_cut + (std::sqrt(r2) - cutoff) * f_cut;
    }

    double force_factor(double r2) const {
        const double ri2 = 1 / r2;
        const double ri6 = ri2 * ri2 * ri2;
        return 24 * ri2 * ri6 * (2 * ri6 - 1) - f_cut * std::sqrt(ri2);
    }
};

class Fluid {
public:
    const double length, half_length, dt;
    const LJ pair;
    std::vector<Vec> pos, vel, forces;
    double bath_work = 0;

    Fluid(int lattice_cells, double side, double timestep, double cutoff, uint64_t seed)
        : length(side), half_length(side / 2), dt(timestep), pair(cutoff),
          ncell(static_cast<int>(side / (cutoff + skin))), rng(seed) {
        if (ncell < 3 || lattice_cells < 1 || dt <= 0 || cutoff <= 0) {
            throw std::invalid_argument("need a positive step and at least three neighbour-list cells per axis");
        }
        const int count = 4 * lattice_cells * lattice_cells * lattice_cells;
        pos.reserve(count);
        vel.resize(count);
        forces.resize(count);
        const std::array<Vec, 4> basis{{{0, 0, 0}, {0, 0.5, 0.5}, {0.5, 0, 0.5}, {0.5, 0.5, 0}}};
        const double spacing = side / lattice_cells;
        for (int x = 0; x < lattice_cells; ++x) {
            for (int y = 0; y < lattice_cells; ++y) {
                for (int z = 0; z < lattice_cells; ++z) {
                    for (const Vec& b : basis) {
                        pos.push_back({spacing * (x + b[0]), spacing * (y + b[1]), spacing * (z + b[2])});
                    }
                }
            }
        }
        Vec total{};
        for (Vec& v : vel) {
            for (int a = 0; a < 3; ++a) {
                v[a] = std::sqrt(1.5) * standard_normal(rng);
                total[a] += v[a];
            }
        }
        for (Vec& v : vel) {
            for (int a = 0; a < 3; ++a) v[a] -= total[a] / count;
        }
        bins.resize(ncell * ncell * ncell);
        neighbours.resize(bins.size());
        for (int x = 0; x < ncell; ++x) {
            for (int y = 0; y < ncell; ++y) {
                for (int z = 0; z < ncell; ++z) {
                    auto& ids = neighbours[cell(x, y, z)];
                    int next = 0;
                    for (int dx = -1; dx <= 1; ++dx) {
                        for (int dy = -1; dy <= 1; ++dy) {
                            for (int dz = -1; dz <= 1; ++dz) {
                                ids[next++] = cell((x + dx + ncell) % ncell, (y + dy + ncell) % ncell,
                                                   (z + dz + ncell) % ncell);
                            }
                        }
                    }
                }
            }
        }
        rebuild();
        calculate_forces();
    }

    void advance(double temperature, double collision_probability) {
        bool rebuild_needed = false;
        for (size_t i = 0; i < pos.size(); ++i) {
            for (int a = 0; a < 3; ++a) {
                vel[i][a] += (0.5 * dt) * forces[i][a];
                const double new_position = pos[i][a] + dt * vel[i][a];
                pos[i][a] = wrap(new_position);
            }
            rebuild_needed |= squared(difference(pos[i], origin[i])) > (skin / 2) * (skin / 2);
        }
        if (rebuild_needed) rebuild();
        calculate_forces();

        const double velocity_scale = std::sqrt(temperature);
        for (size_t i = 0; i < pos.size(); ++i) {
            for (int a = 0; a < 3; ++a) vel[i][a] += (0.5 * dt) * forces[i][a];
            if (collision_probability > 0 && std::generate_canonical<double, 53>(rng) < collision_probability) {
                const double initial_k = 0.5 * squared(vel[i]);
                for (double& value : vel[i]) value = velocity_scale * standard_normal(rng);
                bath_work += 0.5 * squared(vel[i]) - initial_k;
            }
        }
    }

    void observe(int step, std::ostream& ledger, std::ostream& frames) const {
        double kinetic = 0;
        double potential = 0;
        Vec momentum{};
        for (const Vec& v : vel) {
            kinetic += 0.5 * squared(v);
            for (int a = 0; a < 3; ++a) momentum[a] += v[a];
        }
        for (const auto& [i, j] : candidates) potential += pair.potential(squared(difference(pos[i], pos[j])));
        const double temperature = (2 * kinetic - squared(momentum) / pos.size()) / (3 * (pos.size() - 1));
        if (!std::isfinite(kinetic) || !std::isfinite(potential) || !std::isfinite(bath_work)) {
            throw std::runtime_error("nonfinite dynamics at step " + std::to_string(step));
        }
        ledger << step << ',' << step * dt << ',' << temperature << ',' << kinetic << ',' << potential << ','
               << bath_work << ',' << momentum[0] << ',' << momentum[1] << ',' << momentum[2] << '\n';
        const double scale = 65536.0 / length;
        for (const Vec& p : pos) {
            for (double x : p) {
                if (!(0 <= x && x < length)) throw std::runtime_error("wrapped coordinate outside the box");
                const uint16_t code = static_cast<uint16_t>(std::min(65535.0, x * scale));
                frames.write(reinterpret_cast<const char*>(&code), sizeof(code));
            }
        }
        ledger.flush();
        frames.flush();
        if (!ledger || !frames) throw std::runtime_error("could not record trajectory");
    }

    void checkpoint(const fs::path& name) const {
        static_assert(sizeof(Vec) == 3 * sizeof(double));
        std::ofstream file(name, std::ios::binary);
        file.write(reinterpret_cast<const char*>(pos.data()), pos.size() * sizeof(Vec));
        file.write(reinterpret_cast<const char*>(vel.data()), vel.size() * sizeof(Vec));
        if (!file) throw std::runtime_error("could not write the common state");
    }

private:
    static constexpr double skin = 0.5;
    int ncell;
    std::mt19937_64 rng;
    std::normal_distribution<double> standard_normal;
    std::vector<Vec> origin;
    std::vector<std::pair<int, int>> candidates;
    std::vector<std::vector<int>> bins;
    std::vector<std::array<int, 27>> neighbours;

    int cell(int x, int y, int z) const { return (x * ncell + y) * ncell + z; }

    Vec difference(const Vec& a, const Vec& b) const {
        Vec d;
        for (int i = 0; i < 3; ++i) {
            d[i] = a[i] - b[i];
            if (d[i] >= half_length) d[i] -= length;
            if (d[i] < -half_length) d[i] += length;
        }
        return d;
    }

    double wrap(double x) const {
        if (x >= length) x -= length;
        if (x < 0) x += length;
        return x;
    }

    void rebuild() {
        origin = pos;
        const double scale = ncell / length;
        std::vector<int> cell_ids(pos.size());
        for (auto& b : bins) b.clear();
        for (size_t i = 0; i < pos.size(); ++i) {
            const Vec& v = pos[i];
            const int x = std::min(ncell - 1, static_cast<int>(v[0] * scale));
            const int y = std::min(ncell - 1, static_cast<int>(v[1] * scale));
            const int z = std::min(ncell - 1, static_cast<int>(v[2] * scale));
            cell_ids[i] = cell(x, y, z);
            bins[cell_ids[i]].push_back(static_cast<int>(i));
        }
        const double radius2 = (pair.cutoff + skin) * (pair.cutoff + skin);
        candidates.clear();
        for (int i = 0; i < static_cast<int>(pos.size()); ++i) {
            for (int cube : neighbours[cell_ids[i]]) {
                for (int j : bins[cube]) {
                    if (j > i && squared(difference(pos[i], pos[j])) < radius2) candidates.emplace_back(i, j);
                }
            }
        }
    }

    void calculate_forces() {
        std::fill(forces.begin(), forces.end(), Vec{});
        for (const auto& [i, j] : candidates) {
            const Vec r = difference(pos[i], pos[j]);
            const double r2 = squared(r);
            if (r2 < pair.cutoff_sq) {
                const double c = pair.force_factor(r2);
                for (int a = 0; a < 3; ++a) {
                    const double force = c * r[a];
                    forces[i][a] += force;
                    forces[j][a] -= force;
                }
            }
        }
    }
};

void trajectory(Fluid& fluid, const fs::path& out, const std::string& name, int begin, int end, int stride,
                int quench, double cold, double rate) {
    std::ofstream ledger(out / (name + ".csv"));
    std::ofstream frames(out / (name + ".u16"), std::ios::binary);
    ledger << std::setprecision(17)
           << "step,t,temperature,kinetic,potential,bath_work,px,py,pz\n";
    const double collision_probability = -std::expm1(-rate * fluid.dt);
    for (int step = begin; step <= end; ++step) {
        if (step % stride == 0) fluid.observe(step, ledger, frames);
        if (step < end) fluid.advance(step < quench ? 1.5 : cold, collision_probability);
    }
}

int main(int argc, char** argv) {
    try {
        if (argc != 13) {
            throw std::runtime_error(
                "fluid OUT CELLS BOX DT CUTOFF SEED QUENCH_T FORK_T END_T SAMPLE_T COLLISION_RATE COOL");
        }
        const fs::path out = argv[1];
        const double dt = std::stod(argv[4]);
        const double rc = std::stod(argv[5]);
        const int quench = std::lround(std::stod(argv[7]) / dt);
        const int fork = std::lround(std::stod(argv[8]) / dt);
        const int end = std::lround(std::stod(argv[9]) / dt);
        const int stride = std::lround(std::stod(argv[10]) / dt);
        const double rate = std::stod(argv[11]);
        const bool cool = std::string(argv[12]) == "paired";
        if (stride < 1 || quench < 0 || fork < quench || end < fork || fork % stride || end % stride) {
            throw std::invalid_argument("invalid or unaligned time schedule");
        }
        Fluid fluid(std::stoi(argv[2]), std::stod(argv[3]), dt, rc, std::stoull(argv[6]));
        if (!cool) {
            trajectory(fluid, out, "warm", 0, end, stride, quench, 1.5, rate);
            return 0;
        }
        trajectory(fluid, out, "prefix", 0, fork, stride, quench, 0.8, rate);
        fluid.checkpoint(out / "prefix.state");
        Fluid kept = fluid;
        kept.checkpoint(out / "bath.state");
        trajectory(kept, out, "bath", fork, end, stride, quench, 0.8, rate);
        fluid.checkpoint(out / "isolated.state");
        trajectory(fluid, out, "isolated", fork, end, stride, quench, 0.8, 0);
        return 0;
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
