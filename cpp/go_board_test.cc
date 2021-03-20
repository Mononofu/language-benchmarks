#include "go_board.h"
#include "utils.h"

void testSpecialPoints() {
  CHECK_EQ(MakePoint("pass"), kVirtualPass);
}

int main(int argc, char** argv) { 
  testSpecialPoints();
}