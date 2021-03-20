#include <random>

// n-dimensional array of uniform random numbers.
// Example:
//   ZobristTable<int, 3, 4, 5> table;
//
//   table[a][b][c] is a random int where a < 3, b < 4, c < 5
//
template <typename T, std::size_t InnerDim, std::size_t... OtherDims>
class ZobristTable {
 public:
  using Generator = std::mt19937_64;
  using NestedTable = ZobristTable<T, OtherDims...>;

  ZobristTable(Generator::result_type seed) {
    Generator generator(seed);
    std::uniform_int_distribution<Generator::result_type> dist;
    data_.reserve(InnerDim);
    for (std::size_t i = 0; i < InnerDim; ++i) {
      data_.emplace_back(dist(generator));
    }
  }

  const NestedTable& operator[](std::size_t inner_index) const {
    return data_[inner_index];
  }

 private:
  std::vector<NestedTable> data_;
};

// 1-dimensional array of uniform random numbers.
template <typename T, std::size_t InnerDim>
class ZobristTable<T, InnerDim> {
 public:
  using Generator = std::mt19937_64;

  ZobristTable(Generator::result_type seed) : data_(InnerDim) {
    Generator generator(seed);
    std::uniform_int_distribution<T> dist;
    for (auto& field : data_) {
      field = dist(generator);
    }
  }

  T operator[](std::size_t index) const { return data_[index]; }

 private:
  std::vector<T> data_;
};
