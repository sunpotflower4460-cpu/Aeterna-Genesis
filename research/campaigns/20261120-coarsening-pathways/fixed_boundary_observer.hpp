// Registers fixed read-only masks and counts accepted macro hops.
class FixedBoundaryObserver {
  struct Counters {
    std::vector<int32_t> labels;
    std::vector<std::array<uint64_t, 4>> rows;
  };
  const int volume;
  std::ifstream masks;
  std::ofstream observations;
  std::array<Counters, 4> views;
  int interval_begin = -1;

public:
  FixedBoundaryObserver(const std::filesystem::path& folder, int sites)
      : volume(sites), masks(folder / "observer-masks.bin", std::ios::binary),
        observations(folder / "boundary-hops.csv") {
    if (!masks || !observations) throw std::runtime_error("Cannot open transport observation streams");
    observations << "start,end,threshold_index,endpoint,label,in_I,out_I,in_B,out_B\n";
  }

  void sample(int time) {
    if (time < 1200 || time > 1800 || time % 50 != 0) return;
    if (interval_begin >= 0) {
      for (int view = 0; view < int(views.size()); ++view) {
        for (size_t label = 1; label < views[view].rows.size(); ++label) {
          observations << interval_begin << ',' << time << ',' << view / 2 << ','
                       << view % 2 << ',' << label;
          for (auto count : views[view].rows[label]) observations << ',' << count;
          observations << '\n';
        }
      }
      observations.flush();
      if (!observations) throw std::runtime_error("Transport observation write failed");
    }
    if (time == 1800) {
      if (masks.peek() != std::char_traits<char>::eof()) throw std::runtime_error("Extra observer mask input");
      interval_begin = -1;
      return;
    }
    interval_begin = time;
    for (auto& view : views) {
      view.labels.resize(volume);
      masks.read(reinterpret_cast<char*>(view.labels.data()), std::streamsize(volume) * sizeof(int32_t));
      if (!masks) throw std::runtime_error("Observer mask input ended early");
      auto extrema = std::minmax_element(view.labels.begin(), view.labels.end());
      if (*extrema.first < 0 || *extrema.second > volume) throw std::runtime_error("Observer label out of range");
      view.rows.assign(size_t(*extrema.second) + 1, {});
    }
  }

  void hop(int species, int x, int y) {
    if (interval_begin < 0 || species > 2) return;
    const int kind = 2 * (species - 1);
    for (auto& view : views) {
      const int origin = view.labels[x], target = view.labels[y];
      if (origin == target) continue;
      if (origin) ++view.rows[origin][kind + 1];
      if (target) ++view.rows[target][kind];
    }
  }
};
