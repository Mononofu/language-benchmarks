#include "go_board.h"
#include "utils.h"

int main(int argc, char** argv) { 
  std::ios_base::sync_with_stdio(false);

  int board_size = 19;
  float komi = 7.5;
  GoBoard board(board_size);

  for (std::string line; std::getline(std::cin, line);) {
    std::istringstream iss(std::move(line));
    std::string command;
    iss >> command;

    bool success = true;
    std::string message;
    if (command == "play") {
      std::string color, point;
      iss >> color; 
      iss >> point;
      auto p = MakePoint(point);
      auto c = MakeColor(color); 
      success = board.IsLegalMove(p, c) ? board.PlayMove(p, c) : false;
    } else if (command == "boardsize") {
      iss >> board_size;
    } else if (command == "komi") {
      iss >> komi;
    } else if (command == "clear_board") {
      board = GoBoard(board_size);
    } else if (command == "final_score") {
      message.resize(16);
      message.resize(std::snprintf(&message[0], message.size(), "%.1f", TrompTaylorScore(board, komi)));
    } else {
      success = false;
      message = "unknown command " + command; 
    }

    std::cout << (success ? "=" : "?");
    if (!message.empty()) std::cout << " " << message;
    std::cout << std::endl;
  }
}