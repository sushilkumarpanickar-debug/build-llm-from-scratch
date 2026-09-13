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

    func testAcceptsLocalhostHTTPForTheMacApp() throws {
        let client = try APIClient(baseURLString: "http://127.0.0.1:9000")

        XCTAssertEqual(client.baseURL.host, "127.0.0.1")
    }

    func testRejectsMalformedBaseURL() {
        XCTAssertThrowsError(try APIClient(baseURLString: "not a url")) { error in
            XCTAssertEqual(error as? APIClientError, .invalidBaseURL)
        }
    }
}
