import XCTest

import boardTests

var tests = [XCTestCaseEntry]()
tests += boardTests.allTests()
XCTMain(tests)
