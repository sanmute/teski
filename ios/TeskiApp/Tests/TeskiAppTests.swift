import XCTest
@testable import TeskiApp

final class TeskiAppTests: XCTestCase {
    func testAgendaBlockKindTitle() {
        XCTAssertEqual(AgendaBlock.Kind.learn.localizedTitle, "Learn")
        XCTAssertEqual(AgendaBlock.Kind.mock.localizedTitle, "Mock")
    }
}
