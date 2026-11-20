// Binary extension of ../20261120-argon-interface-turnover/fluid.cpp.
// Periodic 3D dynamics with pair-specific linear-force-shifted Lennard-Jones forces.
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
    double sigma_sq, epsilon, cutoff, cutoff_sq, u_cut, f_cut;
    LJ(double sigma, double depth, double range)
        : sigma_sq(sigma * sigma), epsilon(depth), cutoff(sigma * range), cutoff_sq(cutoff * cutoff) {
        const double ri2 = sigma_sq / cutoff_sq;
        const double ri6 = ri2 * ri2 * ri2;
        u_cut = 4 * epsilon * ri6 * (ri6 - 1);
        f_cut = 24 * epsilon * ri6 * (2 * ri6 - 1) / cutoff;
    }

    double potential(double r2) const {
        if (r2 >= cutoff_sq) return 0;
        const double ri2 = sigma_sq / r2;
        const double ri6 = ri2 * ri2 * ri2;
        return 4 * epsilon * ri6 * (ri6 - 1) - u_cut + (std::sqrt(r2) - cutoff) * f_cut;
    }

    double force_factor(double r2) const {
        const double inverse_r2 = 1 / r2;
        const double ri2 = sigma_sq * inverse_r2;
        const double ri6 = ri2 * ri2 * ri2;
        return 24 * epsilon * inverse_r2 * ri6 * (2 * ri6 - 1) - f_cut * std::sqrt(inverse_r2);
    }
};

class Fluid {
public:
    const double length, half_length, dt;
    const std::array<LJ, 3> pairs;
    const std::array<double, 2> mass;
    std::vector<Vec> pos, vel, forces;
    std::vector<uint8_t> species;
    double bath_work = 0;

    Fluid(int lattice_cells, double side, double timestep, const std::array<LJ, 3>& potentials,
          double mass_ratio, double kr_fraction, double hot, uint64_t seed)
        : length(side), half_length(side / 2), dt(timestep), pairs(potentials), mass{{1, mass_ratio}},
          search_radius(std::max({pairs[0].cutoff, pairs[1].cutoff, pairs[2].cutoff}) + skin),
          ncell(static_cast<int>(side / search_radius)), rng(seed) {
        if (ncell < 3 || lattice_cells < 1 || dt <= 0 || mass_ratio <= 0 ||
            kr_fraction <= 0 || kr_fraction >= 1 || hot <= 0) {
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
        species.resize(count);
        std::fill_n(species.begin(), std::lround(kr_fraction * count), uint8_t{1});
        std::mt19937_64 species_rng(seed ^ UINT64_C(0x9E3779B97F4A7C15));
        std::shuffle(species.begin(), species.end(), species_rng);
        Vec total{};
        double total_mass = 0;
        const std::array<double, 2> scale{{std::sqrt(hot), std::sqrt(hot / mass_ratio)}};
        for (int i = 0; i < count; ++i) {
            const uint8_t kind = species[i];
            total_mass += mass[kind];
            for (int a = 0; a < 3; ++a) {
                vel[i][a] = scale[kind] * standard_normal(rng);
                total[a] += mass[kind] * vel[i][a];
            }
        }
        for (Vec& v : vel) {
            for (int a = 0; a < 3; ++a) v[a] -= total[a] / total_mass;
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
        const std::array<double, 2> kick{{0.5 * dt, (0.5 * dt) / mass[1]}};
        for (size_t i = 0; i < pos.size(); ++i) {
            for (int a = 0; a < 3; ++a) {
                vel[i][a] += kick[species[i]] * forces[i][a];
                const double new_position = pos[i][a] + dt * vel[i][a];
                pos[i][a] = wrap(new_position);
            }
            rebuild_needed |= squared(difference(pos[i], origin[i])) > (skin / 2) * (skin / 2);
        }
        if (rebuild_needed) rebuild();
        calculate_forces();

        const std::array<double, 2> velocity_scale{{std::sqrt(temperature), std::sqrt(temperature / mass[1])}};
        for (size_t i = 0; i < pos.size(); ++i) {
            const uint8_t kind = species[i];
            for (int a = 0; a < 3; ++a) vel[i][a] += kick[kind] * forces[i][a];
            if (collision_probability > 0 && std::generate_canonical<double, 53>(rng) < collision_probability) {
                const double initial = squared(vel[i]);
                for (double& value : vel[i]) value = velocity_scale[kind] * standard_normal(rng);
                bath_work += 0.5 * mass[kind] * (squared(vel[i]) - initial);
            }
        }
    }

    void observe(int step, std::ostream& ledger, std::ostream& frames) const {
        double kinetic = 0;
        double potential = 0;
        double virial = 0;
        double total_mass = 0;
        Vec momentum{};
        for (size_t i = 0; i < vel.size(); ++i) {
            const double m = mass[species[i]];
            total_mass += m;
            kinetic += 0.5 * m * squared(vel[i]);
            for (int a = 0; a < 3; ++a) momentum[a] += m * vel[i][a];
        }
        for (const auto& [i, j, kind] : candidates) {
            const auto& pair = pairs[kind];
            const double r2 = squared(difference(pos[i], pos[j]));
            if (r2 >= pair.cutoff_sq) continue;
            potential += pair.potential(r2);
            virial += r2 * pair.force_factor(r2);
        }
        const double twice_thermal_kinetic = 2 * kinetic - squared(momentum) / total_mass;
        const double temperature = twice_thermal_kinetic / (3 * (pos.size() - 1));
        const double pressure = (twice_thermal_kinetic + virial) / (3 * length * length * length);
        if (!std::isfinite(temperature) || !std::isfinite(potential) || !std::isfinite(bath_work) ||
            !std::isfinite(pressure)) {
            throw std::runtime_error("nonfinite dynamics at step " + std::to_string(step));
        }
        ledger << step << ',' << step * dt << ',' << temperature << ',' << kinetic << ',' << potential << ','
               << bath_work << ',' << momentum[0] << ',' << momentum[1] << ',' << momentum[2]
               << ',' << pressure << '\n';
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

    void write_species(const fs::path& name) const {
        std::ofstream file(name, std::ios::binary);
        file.write(reinterpret_cast<const char*>(species.data()), species.size());
        if (!file) throw std::runtime_error("could not write the immutable species IDs");
    }

private:
    static constexpr double skin = 0.6;
    const double search_radius;
    int ncell;
    std::mt19937_64 rng;
    std::normal_distribution<double> standard_normal;
    std::vector<Vec> origin;
    struct Candidate { int i, j; uint8_t kind; };
    std::vector<Candidate> candidates;
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
        candidates.clear();
        for (int i = 0; i < static_cast<int>(pos.size()); ++i) {
            for (int cube : neighbours[cell_ids[i]]) {
                for (int j : bins[cube]) {
                    if (j <= i) continue;
                    const auto kind = static_cast<uint8_t>(species[i] + species[j]);
                    const double radius = pairs[kind].cutoff + skin;
                    if (squared(difference(pos[i], pos[j])) < radius * radius)
                        candidates.push_back({i, j, kind});
                }
            }
        }
    }

    void calculate_forces() {
        std::fill(forces.begin(), forces.end(), Vec{});
        for (const auto& [i, j, kind] : candidates) {
            const auto& pair = pairs[kind];
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
                int quench, double hot, double cold, double rate) {
    std::ofstream ledger(out / (name + ".csv"));
    std::ofstream frames(out / (name + ".u16"), std::ios::binary);
    ledger << std::setprecision(17)
           << "step,t,temperature,kinetic,potential,bath_work,px,py,pz,pressure\n";
    const double collision_probability = -std::expm1(-rate * fluid.dt);
    for (int step = begin; step <= end; ++step) {
        if (step % stride == 0) fluid.observe(step, ledger, frames);
        if (step < end) fluid.advance(step < quench ? hot : cold, collision_probability);
    }
}

int main(int argc, char** argv) {
    try {
        if (argc != 18) {
            throw std::runtime_error(
                "fluid OUT CELLS BOX DT CUTOFF SEED QUENCH_T FORK_T END_T SAMPLE_T COLLISION_RATE MODE"
                " HOT COLD MASS_RATIO KR_FRACTION PAIR_FILE");
        }
        const fs::path out = argv[1];
        const double dt = std::stod(argv[4]);
        const double rc = std::stod(argv[5]);
        const int quench = std::lround(std::stod(argv[7]) / dt);
        const int fork = std::lround(std::stod(argv[8]) / dt);
        const int end = std::lround(std::stod(argv[9]) / dt);
        const int stride = std::lround(std::stod(argv[10]) / dt);
        const double rate = std::stod(argv[11]);
        const std::string mode = argv[12];
        const double hot = std::stod(argv[13]);
        const double cold = std::stod(argv[14]);
        const double mass_ratio = std::stod(argv[15]);
        const double kr_fraction = std::stod(argv[16]);
        if (!(rc > 0 && cold > 0 && rate >= 0) || (mode != "paired" && mode != "warm"))
            throw std::invalid_argument("invalid force range, bath or mode");
        if (stride < 1 || quench < 0 || fork < quench || end < fork || fork % stride || end % stride) {
            throw std::invalid_argument("invalid or unaligned time schedule");
        }
        std::ifstream parameters(argv[17]);
        auto read_pair = [&]() {
            double sigma, epsilon;
            if (!(parameters >> sigma >> epsilon) || !(sigma > 0 && epsilon > 0))
                throw std::invalid_argument("need three positive sigma and epsilon pairs");
            return LJ(sigma, epsilon, rc);
        };
        const std::array<LJ, 3> pairs{{read_pair(), read_pair(), read_pair()}};
        Fluid fluid(std::stoi(argv[2]), std::stod(argv[3]), dt, pairs, mass_ratio, kr_fraction,
                    hot, std::stoull(argv[6]));
        fluid.write_species(out / "species.u8");
        fluid.checkpoint(out / "initial.state");
        if (mode == "warm") {
            trajectory(fluid, out, "warm", 0, end, stride, quench, hot, hot, rate);
            return 0;
        }
        trajectory(fluid, out, "prefix", 0, fork, stride, quench, hot, cold, rate);
        fluid.checkpoint(out / "prefix.state");
        Fluid kept = fluid;
        kept.checkpoint(out / "bath.state");
        trajectory(kept, out, "bath", fork, end, stride, quench, hot, cold, rate);
        fluid.checkpoint(out / "isolated.state");
        trajectory(fluid, out, "isolated", fork, end, stride, quench, hot, cold, 0);
        return 0;
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
