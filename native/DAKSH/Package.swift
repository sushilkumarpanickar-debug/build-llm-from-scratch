// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "DAKSH",
    platforms: [
        .macOS(.v14),
        .iOS(.v17)
    ],
    products: [
        .executable(name: "DAKSH", targets: ["DAKSH"])
    ],
    targets: [
        .executableTarget(
            name: "DAKSH",
            path: "Sources/DAKSH",
            resources: [.process("Resources")]
        ),
        .testTarget(
            name: "DAKSHTests",
            dependencies: ["DAKSH"],
            path: "Tests/DAKSHTests"
        )
    ]
)
