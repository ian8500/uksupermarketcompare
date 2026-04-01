import Foundation

final class LiveSupermarketDataService: SupermarketDataProviding {
    struct Config {
        let url: URL
        let timeout: TimeInterval

        static func fromEnvironment() -> Config? {
            let key = "LIVE_SUPERMARKET_DATA_URL"
            guard let raw = ProcessInfo.processInfo.environment[key], !raw.isEmpty else {
                print("[LiveSupermarketDataService][config] \(key) not set; app will use mock service.")
                return nil
            }

            guard let url = URL(string: raw) else {
                print("[LiveSupermarketDataService][config] \(key) has invalid URL value: \(raw)")
                return nil
            }

            print("[LiveSupermarketDataService][config] \(key) found: \(url.absoluteString)")
            return Config(url: url, timeout: 8)
        }
    }

    struct Diagnostics {
        let liveURL: URL
        let requestedAt: Date
        let completedAt: Date
        let httpStatusCode: Int?
        let supermarketCount: Int
        let errorDescription: String?
        let backendMarker: String?

        var wasSuccessful: Bool {
            errorDescription == nil && supermarketCount > 0
        }
    }

    private let markets: [Supermarket]
    private let productsByStore: [String: [SupermarketProduct]]
    let diagnostics: Diagnostics

    init(config: Config) {
        let report = Self.loadPayload(config: config)
        diagnostics = report.diagnostics

        self.markets = report.payload.supermarkets.map { Supermarket(name: $0.name, description: $0.description) }

        var builtProducts: [String: [SupermarketProduct]] = [:]
        for market in report.payload.supermarkets {
            builtProducts[market.name] = market.products.map { product in
                SupermarketProduct(
                    supermarketName: market.name,
                    name: product.name,
                    category: product.category,
                    subcategory: product.subcategory,
                    price: product.price,
                    size: product.size,
                    brand: product.brand,
                    isOwnBrand: product.isOwnBrand,
                    isPremium: product.isPremium,
                    isOrganic: product.isOrganic,
                    unitDescription: product.unitDescription,
                    unitValue: product.unitValue,
                    tags: product.tags
                )
            }
        }

        self.productsByStore = builtProducts
    }

    func supermarkets() -> [Supermarket] {
        markets
    }

    func products(at supermarket: Supermarket) -> [SupermarketProduct] {
        productsByStore[supermarket.name, default: []]
    }

    private static func loadPayload(config: Config) -> LiveLoadReport {
        let requestedAt = Date()
        print("[LiveSupermarketDataService][request] GET \(config.url.absoluteString)")

        var request = URLRequest(url: config.url)
        request.timeoutInterval = config.timeout
        request.setValue("application/json", forHTTPHeaderField: "Accept")

        let group = DispatchGroup()
        group.enter()

        var httpStatusCode: Int?
        var outcome: Result<LivePayload, Error>?

        URLSession.shared.dataTask(with: request) { data, response, error in
            defer { group.leave() }

            if let error {
                outcome = .failure(error)
                return
            }

            guard let http = response as? HTTPURLResponse else {
                outcome = .failure(LiveDataError.invalidResponse)
                return
            }

            httpStatusCode = http.statusCode
            guard (200..<300).contains(http.statusCode) else {
                outcome = .failure(LiveDataError.invalidStatus(http.statusCode))
                return
            }

            guard let data else {
                outcome = .failure(LiveDataError.emptyResponse)
                return
            }

            do {
                let payload = try JSONDecoder().decode(LivePayload.self, from: data)
                guard !payload.supermarkets.isEmpty else {
                    outcome = .failure(LiveDataError.noSupermarkets)
                    return
                }
                outcome = .success(payload)
            } catch {
                outcome = .failure(error)
            }
        }.resume()

        let waitResult = group.wait(timeout: .now() + config.timeout + 1)
        let completedAt = Date()

        switch (waitResult, outcome) {
        case (_, .success(let payload)):
            let marker = payload.metadata?.debugMarker
            print("[LiveSupermarketDataService][response] status=\(httpStatusCode ?? -1) decoded=true supermarkets=\(payload.supermarkets.count) marker=\(marker ?? "n/a")")
            return LiveLoadReport(
                payload: payload,
                diagnostics: Diagnostics(
                    liveURL: config.url,
                    requestedAt: requestedAt,
                    completedAt: completedAt,
                    httpStatusCode: httpStatusCode,
                    supermarketCount: payload.supermarkets.count,
                    errorDescription: nil,
                    backendMarker: marker
                )
            )
        case (_, .failure(let error)):
            let message = error.localizedDescription
            print("[LiveSupermarketDataService][response] status=\(httpStatusCode ?? -1) decoded=false supermarkets=0 error=\(message)")
            return LiveLoadReport(
                payload: .empty,
                diagnostics: Diagnostics(
                    liveURL: config.url,
                    requestedAt: requestedAt,
                    completedAt: completedAt,
                    httpStatusCode: httpStatusCode,
                    supermarketCount: 0,
                    errorDescription: message,
                    backendMarker: nil
                )
            )
        case (.timedOut, .none):
            let message = LiveDataError.timedOut.localizedDescription
            print("[LiveSupermarketDataService][response] status=\(httpStatusCode ?? -1) decoded=false supermarkets=0 error=\(message)")
            return LiveLoadReport(
                payload: .empty,
                diagnostics: Diagnostics(
                    liveURL: config.url,
                    requestedAt: requestedAt,
                    completedAt: completedAt,
                    httpStatusCode: httpStatusCode,
                    supermarketCount: 0,
                    errorDescription: message,
                    backendMarker: nil
                )
            )
        case (_, .none):
            let message = LiveDataError.unknown.localizedDescription
            print("[LiveSupermarketDataService][response] status=\(httpStatusCode ?? -1) decoded=false supermarkets=0 error=\(message)")
            return LiveLoadReport(
                payload: .empty,
                diagnostics: Diagnostics(
                    liveURL: config.url,
                    requestedAt: requestedAt,
                    completedAt: completedAt,
                    httpStatusCode: httpStatusCode,
                    supermarketCount: 0,
                    errorDescription: message,
                    backendMarker: nil
                )
            )
        }
    }
}

private struct LiveLoadReport {
    let payload: LivePayload
    let diagnostics: LiveSupermarketDataService.Diagnostics
}

private enum LiveDataError: LocalizedError {
    case invalidResponse
    case invalidStatus(Int)
    case emptyResponse
    case noSupermarkets
    case timedOut
    case unknown

    var errorDescription: String? {
        switch self {
        case .invalidResponse: return "Live request returned a non-HTTP response."
        case .invalidStatus(let code): return "Live request failed with HTTP status \(code)."
        case .emptyResponse: return "Live request returned no body."
        case .noSupermarkets: return "Live payload decoded but contained zero supermarkets."
        case .timedOut: return "Live request timed out before completion."
        case .unknown: return "Live request failed for an unknown reason."
        }
    }
}

private struct LivePayload: Decodable {
    let supermarkets: [LiveSupermarket]
    let metadata: LiveCatalogMetadata?

    static let empty = LivePayload(supermarkets: [], metadata: nil)
}

private struct LiveCatalogMetadata: Decodable {
    let source: String?
    let debugMarker: String?
    let generatedAt: String?

    private enum CodingKeys: String, CodingKey {
        case source
        case debugMarker
        case generatedAt
        case debug_marker
        case generated_at
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        source = try container.decodeIfPresent(String.self, forKey: .source)
        debugMarker = try container.decodeIfPresent(String.self, forKey: .debugMarker)
            ?? container.decodeIfPresent(String.self, forKey: .debug_marker)
        generatedAt = try container.decodeIfPresent(String.self, forKey: .generatedAt)
            ?? container.decodeIfPresent(String.self, forKey: .generated_at)
    }
}

private struct LiveSupermarket: Decodable {
    let name: String
    let description: String
    let products: [LiveProduct]
}

private struct LiveProduct: Decodable {
    let name: String
    let category: GroceryCategory
    let subcategory: String
    let price: Decimal
    let size: String
    let brand: String
    let isOwnBrand: Bool
    let isPremium: Bool
    let isOrganic: Bool
    let unitDescription: String
    let unitValue: Decimal
    let tags: [String]

    private enum CodingKeys: String, CodingKey {
        case name
        case category
        case subcategory
        case price
        case size
        case brand
        case isOwnBrand
        case isPremium
        case isOrganic
        case unitDescription
        case unitValue
        case tags
        case is_own_brand
        case is_premium
        case is_organic
        case unit_description
        case unit_value
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)

        name = try container.decode(String.self, forKey: .name)
        subcategory = try container.decode(String.self, forKey: .subcategory)
        size = try container.decode(String.self, forKey: .size)
        brand = try container.decode(String.self, forKey: .brand)
        tags = try container.decodeIfPresent([String].self, forKey: .tags) ?? []

        let rawCategory = try container.decode(String.self, forKey: .category)
        category = GroceryCategory(rawValue: rawCategory) ?? .unknown

        price = try Self.decodeDecimal(container: container, primary: .price, fallback: nil)
        unitValue = try Self.decodeDecimal(container: container, primary: .unitValue, fallback: .unit_value)

        isOwnBrand = try Self.decodeBool(container: container, primary: .isOwnBrand, fallback: .is_own_brand)
        isPremium = try Self.decodeBool(container: container, primary: .isPremium, fallback: .is_premium)
        isOrganic = try Self.decodeBool(container: container, primary: .isOrganic, fallback: .is_organic)
        unitDescription = try Self.decodeString(container: container, primary: .unitDescription, fallback: .unit_description)
    }

    private static func decodeString(
        container: KeyedDecodingContainer<CodingKeys>,
        primary: CodingKeys,
        fallback: CodingKeys?
    ) throws -> String {
        if let value = try container.decodeIfPresent(String.self, forKey: primary) {
            return value
        }
        if let fallback, let value = try container.decodeIfPresent(String.self, forKey: fallback) {
            return value
        }
        throw DecodingError.keyNotFound(primary, .init(codingPath: container.codingPath, debugDescription: "Missing required string value."))
    }

    private static func decodeBool(
        container: KeyedDecodingContainer<CodingKeys>,
        primary: CodingKeys,
        fallback: CodingKeys?
    ) throws -> Bool {
        if let value = try container.decodeIfPresent(Bool.self, forKey: primary) {
            return value
        }
        if let fallback, let value = try container.decodeIfPresent(Bool.self, forKey: fallback) {
            return value
        }
        throw DecodingError.keyNotFound(primary, .init(codingPath: container.codingPath, debugDescription: "Missing required boolean value."))
    }

    private static func decodeDecimal(
        container: KeyedDecodingContainer<CodingKeys>,
        primary: CodingKeys,
        fallback: CodingKeys?
    ) throws -> Decimal {
        if let value = try container.decodeIfPresent(Decimal.self, forKey: primary) {
            return value
        }
        if let fallback, let value = try container.decodeIfPresent(Decimal.self, forKey: fallback) {
            return value
        }
        if let text = try container.decodeIfPresent(String.self, forKey: primary), let value = Decimal(string: text) {
            return value
        }
        if let fallback, let text = try container.decodeIfPresent(String.self, forKey: fallback), let value = Decimal(string: text) {
            return value
        }
        throw DecodingError.keyNotFound(primary, .init(codingPath: container.codingPath, debugDescription: "Missing required decimal value."))
    }
}
