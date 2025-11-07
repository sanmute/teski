// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "TeskiApp",
    platforms: [
        .iOS(.v16)
    ],
    products: [
        .library(
            name: "AppModule",
            targets: ["AppModule"]
        )
    ],
    targets: [
        .target(
            name: "AppModule",
            path: "Sources",
            resources: [
                .process("Resources")
            ]
        ),
        .testTarget(
            name: "AppModuleTests",
            dependencies: ["AppModule"],
            path: "Tests"
        )
    ]
)
