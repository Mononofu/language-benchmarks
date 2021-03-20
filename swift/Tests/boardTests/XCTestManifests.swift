import XCTest

#if !canImport(ObjectiveC)
public func allTests() -> [XCTestCaseEntry] {
    return [
        testCase(GoPointTests.allTests),
        testCase(GoBoardTests.allTests), 
    ]
}
#endif
