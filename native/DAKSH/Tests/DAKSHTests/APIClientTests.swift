import XCTest
@testable import DAKSH

final class APIClientTests: XCTestCase {
    func testAcceptsHTTPSBaseURLAndBuildsAPIPath() throws {
        let client = try APIClient(baseURLString: "https://daksh.example.ts.net/dashboard/")

        XCTAssertEqual(client.baseURL.scheme, "https")
        XCTAssertEqual(client.baseURL.host, "daksh.example.ts.net")
    }

    func testRejectsNonHTTPSBaseURL() {
        XCTAssertThrowsError(try APIClient(baseURLString: "http://daksh.example.ts.net")) { error in
            XCTAssertEqual(error as? APIClientError, .insecureURL)
        }
    }

    func testRejectsMalformedBaseURL() {
        XCTAssertThrowsError(try APIClient(baseURLString: "not a url")) { error in
            XCTAssertEqual(error as? APIClientError, .invalidBaseURL)
        }
    }
}
