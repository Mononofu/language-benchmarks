#ifndef UTILS_H
#define UTILS_H

#include <iostream>
#include <sstream>

class FatalError {
  public:
    FatalError(const std::string& file, int line) : file_(file), line_(line) {}

    template <typename T>
    FatalError& operator<<(const T& value) {
      ss_ << value;
      return *this;
    }

    [[ noreturn ]] ~FatalError() {
      std::cerr <<  file_ << ":" << line_ << ": " << ss_.str() << std::endl;
      exit(EXIT_FAILURE);
    }

  private:
    std::string file_;
    int line_;
    std::stringstream ss_;
};

#define FATAL() FatalError(__FILE__, __LINE__)
#define CHECK_TRUE(cond) if (!cond) FATAL() << #cond
#define CHECK_EQ(a, b) if (a != b) FATAL() << "check failed"
#define CHECK_GT(a, b) if (!(a > b)) FATAL() << #a << " > " << #b

#endif // UTILS_H