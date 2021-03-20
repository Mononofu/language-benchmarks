#!/bin/bash

set -e

echo "Benchmarking c++"
pushd cpp
clang++ -std=c++17 -Wall -Werror -O3 go_board.cc go_board_bench.cc -o go_board_bench
time cat ../data/go_board_2_20.gtp | ./go_board_bench > /dev/null 
rm go_board_bench
popd