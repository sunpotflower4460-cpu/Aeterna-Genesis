// Local periodic stencil for the three-dimensional, dimensionless Gross-Pitaevskii equation.
// The only time-dependent term is the externally prescribed Gaussian potential.
#include <algorithm>
#include <array>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

constexpr double pi = 3.14159265358979323846;

struct Cell {
    double re;
    double im;
};
static_assert(sizeof(Cell) == 2 * sizeof(double));

double norm(Cell a) { return a.re * a.re + a.im * a.im; }

struct Motion {
    double center, speed, height, rise;
};

Motion motion(double t, const std::string& mode) {
    constexpr double height = 5.0;
    constexpr double speed = 0.68;
    constexpr double start = 30.0;
    if (t < 16.0) {
        const double angle = pi * t / 16.0;
        return {start, 0.0, 0.5 * height * (1.0 - std::cos(angle)),
                0.5 * height * (pi / 16.0) * std::sin(angle)};
    }
    if (mode == "static") return {start, 0.0, height, 0.0};
    if (t < 40.0) {
        const double angle = pi * (t - 16.0) / 24.0;
        return {start + 0.5 * speed * ((t - 16.0) - (24.0 / pi) * std::sin(angle)),
                0.5 * speed * (1.0 - std::cos(angle)), height, 0.0};
    }
    if (mode == "brake" && t >= 120.0) {
        const double elapsed = std::min(t - 120.0, 12.0);
        const double angle = pi * elapsed / 12.0;
        return {start + speed * (92.0 + 0.5 * (elapsed + (12.0 / pi) * std::sin(angle))),
                0.5 * speed * (1.0 + std::cos(angle)), height, 0.0};
    }
    return {start + speed * (t - 28.0), speed, height, 0.0};
}

struct Gaussian {
    double value, center_derivative;
};

Gaussian gaussian(double separation, double period) {
    constexpr double sigma = 2.5;
    double d = separation - period * std::nearbyint(separation / period);
    Gaussian result{};
    for (int image = -1; image <= 1; ++image) {
        const double offset = d + image * period;
        const double value = std::exp(-0.5 * offset * offset / (sigma * sigma));
        result.value += value;
        result.center_derivative += offset * value / (sigma * sigma);
    }
    return result;
}

struct Rates {
    double work = 0.0;
    double heat = 0.0;
};

class Simulation {
public:
    const int nx, ny, nz;
    const double dx, dt, gamma;
    std::vector<Cell> state;
    Rates integrated;
    Motion boundary{};
    std::vector<double> transverse, axial, axial_rate;

    Simulation(int nx_, int ny_, int nz_, double dx_, double dt_, double gamma_)
        : nx(nx_), ny(ny_), nz(nz_), dx(dx_), dt(dt_), gamma(gamma_),
          state(static_cast<size_t>(nx) * ny * nz), transverse(nx * ny), axial(nz), axial_rate(nz),
          first(state.size()), second(state.size()), sum(state.size()), phase(state.size()) {
        for (int x = 0; x < nx; ++x) {
            const double gx = gaussian((x - nx / 2) * dx, nx * dx).value;
            for (int y = 0; y < ny; ++y) {
                transverse[x * ny + y] = gx * gaussian((y - ny / 2) * dx, ny * dx).value;
            }
        }
    }

    void set_boundary(Motion next) {
        boundary = next;
        for (int z = 0; z < nz; ++z) {
            const Gaussian g = gaussian(z * dx - next.center, nz * dx);
            axial[z] = next.height * g.value;
            axial_rate[z] = next.rise * g.value + next.height * next.speed * g.center_derivative;
        }
    }

    void advance(double t, const std::string& mode) {
        set_boundary(motion(t, mode));
        const Rates a = stage<1>(state, first);
        set_boundary(motion(t + dt / 2.0, mode));
        const Rates b = stage<2>(first, second);
        const Rates c = stage<3>(second, first);
        set_boundary(motion(t + dt, mode));
        const Rates d = stage<4>(first, state);
        const double weight = dx * dx * dx * dt / 6.0;
        integrated.work += weight * (a.work + 2.0 * (b.work + c.work) + d.work);
        integrated.heat += weight * (a.heat + 2.0 * (b.heat + c.heat) + d.heat);
    }

    void measure(double t, std::ostream& ledger, std::ostream& crossings) {
        double energy = 0.0;
        double mass = 0.0;
        double power = 0.0;
        const double kinetic = 0.5 / (dx * dx);
        for (int x = 0; x < nx; ++x) {
            for (int y = 0; y < ny; ++y) {
                const double gxy = transverse[x * ny + y];
                for (int z = 0; z < nz; ++z) {
                    const int index = offset(x, y, z);
                    const Cell u = state[index];
                    const double n = norm(u);
                    const double potential = gxy * axial[z];
                    const Cell ux = state[offset((x + 1) % nx, y, z)];
                    const Cell uy = state[offset(x, (y + 1) % ny, z)];
                    const Cell uz = state[offset(x, y, (z + 1) % nz)];
                    const double grad = norm({ux.re - u.re, ux.im - u.im})
                                      + norm({uy.re - u.re, uy.im - u.im})
                                      + norm({uz.re - u.re, uz.im - u.im});
                    energy += kinetic * grad + 0.5 * (n - 1) * (n - 1) + potential * n;
                    mass += n;
                    power += n * gxy * axial_rate[z];
                    phase[index] = std::atan2(u.im, u.re);
                }
            }
        }
        if (!std::isfinite(energy) || !std::isfinite(mass) || !std::isfinite(integrated.heat) ||
            !std::isfinite(integrated.work)) {
            throw std::runtime_error("non-finite state at t=" + std::to_string(t));
        }
        const double volume = dx * dx * dx;
        ledger << t << ',' << boundary.center << ',' << boundary.speed << ',' << boundary.height
               << ',' << integrated.work << ',' << integrated.heat << ',' << volume * energy
               << ',' << volume * mass << ',' << volume * power << '\n';
        for (int x = 0; x < nx; ++x) {
            const int xx = (x + 1) % nx;
            for (int y = 0; y < ny; ++y) {
                const int yy = (y + 1) % ny;
                for (int z = 0; z < nz; ++z) {
                    const int zz = (z + 1) % nz;
                    const double a  = phase[offset(x, y, z)];
                    const double bx = phase[offset(xx, y, z)];
                    const double by = phase[offset(x, yy, z)];
                    const double bz = phase[offset(x, y, zz)];
                    const std::array<int, 3> winding{
                        circulation(a, by, phase[offset(x, yy, zz)], bz),
                        circulation(a, bz, phase[offset(xx, y, zz)], bx),
                        circulation(a, bx, phase[offset(xx, yy, z)], by)
                    };
                    for (int normal = 0; normal < 3; ++normal) {
                        if (winding[normal] != 0) {
                            crossings << t << ',' << normal << ',' << x << ',' << y << ',' << z
                                      << ',' << winding[normal] << '\n';
                        }
                    }
                }
            }
        }
        ledger.flush();
        crossings.flush();
        if (!ledger || !crossings) throw std::runtime_error("could not save the frame");
    }

    void write_state(const std::string& path) const {
        std::ofstream stream(path, std::ios::binary);
        stream.write(reinterpret_cast<const char*>(state.data()), state.size() * sizeof(Cell));
        if (!stream) throw std::runtime_error("could not save " + path);
    }

    void write_slice(std::ostream& stream) const {
        for (int y = 0; y < ny; ++y) {
            for (int z = 0; z < nz; ++z) {
                const float density = static_cast<float>(norm(state[offset(nx / 2, y, z)]));
                stream.write(reinterpret_cast<const char*>(&density), sizeof(density));
            }
        }
        if (!stream) throw std::runtime_error("could not save the density slice");
    }

private:
    std::vector<Cell> first, second, sum;
    std::vector<double> phase;

    int offset(int x, int y, int z) const { return (x * ny + y) * nz + z; }

    static double wrap(double angle) {
        if (angle >= pi) return angle - 2.0 * pi;
        if (angle < -pi) return angle + 2.0 * pi;
        return angle;
    }

    static int circulation(double a, double b, double c, double d) {
        return static_cast<int>(std::lround((wrap(b - a) + wrap(c - b) + wrap(d - c) + wrap(a - d))
                                             / (2.0 * pi)));
    }

    // The arrays on the right are stage inputs. No output read by a neighbour is updated in place.
    template<int step>
    Rates stage(const std::vector<Cell>& input, std::vector<Cell>& output) {
        const double kinetic = 0.5 / (dx * dx);
        Rates rate{};
        for (int x = 0; x < nx; ++x) {
            const int xm = (x + nx - 1) % nx;
            const int xp = (x + 1) % nx;
            for (int y = 0; y < ny; ++y) {
                const int base = offset(x, y, 0);
                const Cell* xm_row = &input[offset(xm, y, 0)];
                const Cell* xp_row = &input[offset(xp, y, 0)];
                const Cell* ym_row = &input[offset(x, (y + ny - 1) % ny, 0)];
                const Cell* yp_row = &input[offset(x, (y + 1) % ny, 0)];
                const Cell* row = &input[base];
                const double gxy = transverse[x * ny + y];
                for (int z = 0; z < nz; ++z) {
                    const Cell u = row[z];
                    const Cell zm = row[z == 0 ? nz - 1 : z - 1];
                    const Cell zp = row[z + 1 == nz ? 0 : z + 1];
                    const double n = norm(u);
                    const double diagonal = 6.0 * kinetic + n - 1.0 + gxy * axial[z];
                    const double h_re = diagonal * u.re - kinetic * (
                        xm_row[z].re + xp_row[z].re + ym_row[z].re + yp_row[z].re + zm.re + zp.re);
                    const double h_im = diagonal * u.im - kinetic * (
                        xm_row[z].im + xp_row[z].im + ym_row[z].im + yp_row[z].im + zm.im + zp.im);
                    const Cell k{h_im - gamma * h_re, -h_re - gamma * h_im};
                    const int i = base + z;
                    const Cell old = state[i];
                    if constexpr (step == 4) {
                        output[i] = {old.re + dt / 6.0 * (sum[i].re + k.re),
                                     old.im + dt / 6.0 * (sum[i].im + k.im)};
                    } else {
                        if constexpr (step == 1) sum[i] = k;
                        else sum[i] = {sum[i].re + 2.0 * k.re, sum[i].im + 2.0 * k.im};
                        const double factor = step == 3 ? dt : 0.5 * dt;
                        output[i] = {old.re + factor * k.re, old.im + factor * k.im};
                    }
                    rate.work += n * axial_rate[z] * gxy;
                    rate.heat += h_re * h_re + h_im * h_im;
                }
            }
        }
        rate.heat *= 2.0 * gamma;
        return rate;
    }
};

int main(int argc, char** argv) {
    try {
        if (argc != 13) {
            throw std::runtime_error(
                "evolve OUT NX NY NZ DX DT GAMMA MODE END EVERY DUMP_PREFIX_AND_FINAL INITIAL");
        }
        const std::string out = argv[1], mode = argv[8];
        Simulation sim(std::stoi(argv[2]), std::stoi(argv[3]), std::stoi(argv[4]), std::stod(argv[5]),
                       std::stod(argv[6]), std::stod(argv[7]));
        const int steps = std::lround(std::stod(argv[9]) / sim.dt);
        const int every = std::lround(std::stod(argv[10]) / sim.dt);
        const bool dump_final = std::stoi(argv[11]) != 0;
        std::ifstream initial(argv[12], std::ios::binary);
        initial.read(reinterpret_cast<char*>(sim.state.data()), sim.state.size() * sizeof(Cell));
        if (!initial || initial.peek() != EOF) throw std::runtime_error("wrong size of the initial field");
        std::ofstream ledger(out + "/ledger.csv"), faces(out + "/faces.csv");
        std::ofstream cuts(out + "/cuts.f32", std::ios::binary);
        ledger << std::setprecision(17) << "t,obstacle_z,speed,height,work,heat,energy,mass,power\n";
        faces << std::setprecision(17) << "t,normal,x,y,z,charge\n";
        sim.set_boundary(motion(0.0, mode));
        for (int step = 0; step <= steps; ++step) {
            const double t = step * sim.dt;
            if (step % every == 0) {
                sim.set_boundary(motion(t, mode));
                sim.measure(t, ledger, faces);
            }
            if (t == 0.0 || t == 80.0 || t == 120.0 || t == 132.0 || t == 176.0 || step == steps) {
                sim.write_slice(cuts);
            }
            if (t == 120.0) sim.write_state(out + "/prefix.c128");
            if (step < steps) sim.advance(t, mode);
        }
        if (dump_final) sim.write_state(out + "/final.c128");
        return 0;
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
