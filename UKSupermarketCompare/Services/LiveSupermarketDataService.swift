import Foundation

final class LiveSupermarketDataService: SupermarketDataProviding {
    struct Config {
        let url: URL
        let timeout: TimeInterval

        static func fromEnvironment() -> Config? {
            guard let raw = ProcessInfo.processInfo.environment["LIVE_SUPERMARKET_DATA_URL"],
                  let url = URL(string: raw)
            else {
                return nil
            }

            return Config(url: url, timeout: 8)
        }
    }

    private let markets: [Supermarket]
    private let productsByStore: [String: [SupermarketProduct]]

    init(config: Config) {
        let payload = Self.loadPayload(config: config)
        self.markets = payload.supermarkets.map { Supermarket(name: $0.name, description: $0.description) }

        var builtProducts: [String: [SupermarketProduct]] = [:]
        for market in payload.supermarkets {
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

    private static func loadPayload(config: Config) -> LivePayload {
        var request = URLRequest(url: config.url)
        request.timeoutInterval = config.timeout
        request.setValue("application/json", forHTTPHeaderField: "Accept")

        let semaphore = DispatchSemaphore(value: 0)
        var result: Result<LivePayload, Error>?

        URLSession.shared.dataTask(with: request) { data, response, error in
            defer { semaphore.signal() }

            if let error {
                result = .failure(error)
                return
            }

            guard let http = response as? HTTPURLResponse, (200..<300).contains(http.statusCode) else {
                result = .failure(LiveDataError.invalidStatus)
                return
            }

            guard let data else {
                result = .failure(LiveDataError.emptyResponse)
                return
            }

            do {
                let decoder = JSONDecoder()
                let payload = try decoder.decode(LivePayload.self, from: data)
                guard !payload.supermarkets.isEmpty else {
                    result = .failure(LiveDataError.noSupermarkets)
                    return
                }
                result = .success(payload)
            } catch {
                result = .failure(error)
            }
        }.resume()

        _ = semaphore.wait(timeout: .now() + config.timeout + 1)

        switch result {
        case .success(let payload):
            return payload
        case .failure(let error):
            print("[LiveSupermarketDataService] Failed to load live data: \(error)")
            return LivePayload.empty
        case .none:
            print("[LiveSupermarketDataService] Timed out loading live data.")
            return LivePayload.empty
        }
    }
}

private enum LiveDataError: Error {
    case invalidStatus
    case emptyResponse
    case noSupermarkets
}

private struct LivePayload: Decodable {
    let supermarkets: [LiveSupermarket]

    static let empty = LivePayload(supermarkets: [])
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
}
