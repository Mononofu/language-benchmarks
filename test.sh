#!/bin/bash

set -e

echo "testing C++"
pushd cpp

clang++ -std=c++17 -Wall -Werror go_board.cc go_board_test.cc -o go_board_test
./go_board_test
rm go_board_test

popd

echo "testing Python"
pushd python
python3 go_board_test.py
popd

echo "testing Swift"
pushd swift
swift test
popd