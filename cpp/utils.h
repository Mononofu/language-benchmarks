#ifndef UTILS_H
#define UTILS_H

#include <iostream>
#include <sstream>

class FatalError {
  public:
    template <typename T>
    FatalError& operator<<(const T& value) {
      ss_ << value;
      return *this;
    }

    [[ noreturn ]] ~FatalError() {
      std::cerr << ss_.str() << std::endl;
      exit(EXIT_FAILURE);
    }

  private:
    std::stringstream ss_;
};

#define CHECK_TRUE(cond) if (!cond) FatalError()
#define CHECK_EQ(a, b) if (a != b) FatalError() << "check failed"
#define CHECK_GT(a, b) if (!(a > b)) FatalError()

#endif // UTILS_H